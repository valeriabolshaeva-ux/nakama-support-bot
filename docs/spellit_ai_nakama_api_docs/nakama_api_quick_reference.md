# nakama_api — Быстрая справка

> Шпаргалка по основным эндпоинтам и запросам

## Авторизация

```http
API-Access-Key: <your_api_key>
```

или

```http
Authorization: Bearer <jwt_token>
```

---

## 🎯 Главные эндпоинты

### Результаты анализа критериев
```http
GET /api/insights?id_project={project_id}&id_item_set={item_set_id}
```
```json
{
  "project_id": 1,
  "item_set_id": 50,
  "insights": [
    {"criterion_name": "...", "score": 5, "reasons": "...", "quotes": "..."}
  ]
}
```

### Транскрипция
```http
GET /api/transcription?id_project={project_id}&id_item_set={item_set_id}
```

### Список звонков проекта
```http
GET /api/client/project/{project_id}/item-sets
```

### Звонки за период
```http
GET /api/client/project/{project_id}/item-sets/by-date?date_from=2025-01-01&date_to=2025-01-31&page=1&per_page=50
```

### Детали звонка
```http
GET /api/client/item-set/{item_set_id}
```

### CRM данные звонка
```http
GET /api/client/item-set/{item_set_id}/crm-data
```

### Результаты формул
```http
GET /api/admin/output/formulas/project/{project_id}/item-set/{item_set_id}
```

### Формулы проекта (CRUD)
```http
GET /api/project/{project_id}/formulas
POST /api/project/{project_id}/formulas?name=...&formula=...
PUT /api/project/{project_id}/formulas/{formula_id}?name=...&formula=...
DELETE /api/project/{project_id}/formulas/{formula_id}
```

### Список проектов
```http
GET /api/projects?limit=20&offset=0&status_filter=active
```

### Health Check
```http
GET /api/health
```

---

## 📤 Отправка файлов

### Создать ItemSet
```http
POST /api/item-set
Content-Type: application/json

{"name": "call_name", "project_id": 1, "processing_parameters": {"extra_processing_data": {"crm_data": {...}}}}
```

### Загрузить файлы
```http
PATCH /api/item-set/upload?item_set_id={id}
Content-Type: multipart/form-data
files: [file.mp3]
```

### Перезапуск обработки
```http
PATCH /api/item-set/processing/restart/{item_set_id}
```

---

## 📊 Статусы для фильтрации

### status_within_project (анализ критериев)
| Статус | Готовность |
|--------|------------|
| `processed` | ✅ Готов |
| `processing` | ⏳ В процессе |
| `all_items_processed` | ⏳ Ожидает анализа |
| `processing_failed` | ❌ Ошибка |
| `added` | 🆕 Новый |

### Проверка готовности
```python
if item_set["status_within_project"] == "processed":
    insights = get_insights(project_id, item_set["id"])
```

---

## 🐍 Python минимальный код

```python
import requests

BASE = "https://<domain>/api"
HEADERS = {"API-Access-Key": "<key>"}

# Insights
r = requests.get(f"{BASE}/insights", 
    params={"id_project": 1, "id_item_set": 50}, 
    headers=HEADERS)
for i in r.json()["insights"]:
    print(f"{i['criterion_name']}: {i['score']}")

# Все звонки проекта
r = requests.get(f"{BASE}/client/project/1/item-sets", headers=HEADERS)
for item in r.json()["item_sets"]:
    if item["status_within_project"] == "processed":
        print(item["name"])
```

---

## 🔄 API vs БД (важно!)

| Источник | `/api/insights` (API) | `output.project_item_set_processing_output` (БД) |
|----------|----------------------|--------------------------------------------------|
| Формат | ✅ **Распарсенный** массив | ❌ **Сырой** JSONB с вложенным JSON |
| Нужен парсинг? | Нет | Да |
| Использовать | Для интеграций | Для глубокого анализа |

---

## 🗄️ SQL быстрые запросы

> ⚠️ В БД критерии и сырые транскрипции хранятся в сыром формате — требуется парсинг!

### Все клиенты
```sql
SELECT id, name, email, is_active FROM "user".base_user ORDER BY id;
```

### Все проекты
```sql
SELECT p.id, p.name, u.name as user_name, p.active_status
FROM object.project p
JOIN "user".base_user u ON u.id = p.id_base_user;
```

### Проекты клиента
```sql
SELECT id, name, active_status FROM object.project WHERE id_base_user = 1;
```

### Результаты критериев (сырые)
```sql
SELECT id_item_set, output 
FROM output.project_item_set_processing_output 
WHERE id_project = 1 AND id_item_set = 50;
```

### Транскрипция (объединённая, готовая)
```sql
SELECT output->>'output' as text, output->>'google_doc' as doc_url
FROM output.item_set_processing_output 
WHERE id_item_set = 50;
```

### Транскрипции сырые от сервисов
```sql
-- Сырой Synopsis (строка! нужен ast.literal_eval)
SELECT output->>'synopsis' as synopsis_raw
FROM output.item_processing_output WHERE id_item = 123;

-- Сырой Nexara (JSONB массив)
SELECT output->'nexara' as nexara_raw
FROM output.item_processing_output WHERE id_item = 123;

-- Все транскрипции для звонка (item_set)
SELECT i.name, ipo.output->>'synopsis', ipo.output->'nexara'
FROM object.item i
JOIN output.item_processing_output ipo ON ipo.id_item = i.id
WHERE i.id_item_set = 50;
```

### Проанализированные звонки
```sql
SELECT id, name, created_at 
FROM object.item_set 
WHERE id_project = 1 
  AND status_within_project = 'processed'
ORDER BY created_at DESC;
```

### CRM данные
```sql
SELECT processing_parameters->'extra_processing_data'->'crm_data'
FROM processing_metadata.item_set_processing_metadata 
WHERE id_item_set = 50;
```

---

## 📁 Файлы документации

| Файл | Содержание |
|------|------------|
| `nakama_api_readme.md` | Общее описание системы (начни отсюда!) |
| `nakama_api_rest_integration.md` | Полное описание REST API |
| `nakama_api_database_schema.md` | Структура БД и SQL запросы |
| `nakama_api_quick_reference.md` | Эта шпаргалка |

---

## 🔗 Swagger

```
https://<domain>/docs
https://<domain>/api/openapi.json
```
