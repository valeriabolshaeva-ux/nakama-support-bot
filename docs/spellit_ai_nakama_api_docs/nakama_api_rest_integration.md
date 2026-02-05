# nakama_api — REST API интеграция

> Полная документация для подключения к REST API сервиса анализа звонков nakama_api

## Обзор системы

**nakama_api** — REST API сервис для автоматизированного анализа звонков и разговоров.

### Что делает система:
1. **Транскрибация** — преобразование аудио/видео в текст (Synopsis, SpeakAI, Nexara)
2. **Объединение транскрипций** — слияние результатов от разных транскрибаторов
3. **Анализ по критериям** — оценка разговора по критериям качества через GPT
4. **Формирование отчётов** — запись результатов в Google Sheets

### Основные сущности:
- **User** — пользователь системы
- **Project** — проект с настройками критериев анализа
- **ItemSet** — набор файлов (один звонок может состоять из нескольких файлов)
- **Item** — отдельный аудио/видео файл
- **Output** — результаты обработки на каждом этапе

### Pipeline обработки:
```
Загрузка файлов → Транскрибация → Объединение → Анализ критериев → Отчёт
     (Item)        (Synopsis,      (transcript_    (criteria_gpt)
                   SpeakAI,         merger)
                   Nexara)
```

### Технические особенности:
- **Длинные файлы** (2+ часа) — автоматическая нарезка и склейка
- **Мультисервисная транскрибация** — параллельная обработка несколькими сервисами
- **Умное объединение** — AI выбирает лучшие фрагменты из разных транскрипций
- **Неограниченные критерии** — любое количество критериев оценки
- **PII-детекция** — скрытие персональных данных перед анализом

---

## Авторизация

### Способ 1: API-ключ (рекомендуется для интеграций)

```http
API-Access-Key: <your_api_key>
```

API-ключ хранится в БД: `user.base_user.api_key`

**Преимущества:**
- Не требует обновления (без срока действия)
- Простая интеграция
- Подходит для server-to-server

### Способ 2: JWT Bearer токен

**Получение токена:**
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=<email>&password=<password>
```

**Ответ:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer"
}
```

**Использование:**
```http
Authorization: Bearer <access_token>
```

**Сроки жизни:**
- Access token: **4 часа**
- Refresh token: **7 дней** (в cookie `refresh_token`)

**Обновление токена:**
```http
POST /api/auth/refresh
Authorization: <expired_access_token>
Cookie: refresh_token=<refresh_token>
```

**Проверка токена:**
```http
POST /api/auth/check
Authorization: <access_token>
```

**Информация о текущем пользователе:**
```http
GET /api/auth/me
```

---

## Базовый URL

Все эндпоинты имеют префикс `/api`:
```
https://<domain>/api/<endpoint>
```

---

## Эндпоинты для интеграции

### 🎯 GET /api/insights — Результаты анализа критериев

**Самый важный эндпоинт** — возвращает оценки по всем критериям для звонка.

> ✅ **API отдаёт УЖЕ РАСПАРСЕННЫЕ данные!** В отличие от БД, где хранится сырой JSON, 
> API автоматически парсит ответы GPT и возвращает чистый массив критериев.

```http
GET /api/insights?id_project={project_id}&id_item_set={item_set_id}
```

**Параметры:**
| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| id_project | int | ✅ | ID проекта |
| id_item_set | int | ✅ | ID item_set (звонка) |

**Успешный ответ (200):**
```json
{
  "project_id": 1,
  "item_set_id": 50,
  "created_at": "2025-01-08T12:00:00",
  "insights": [
    {
      "criterion_name": "1. Приветствие и установление контакта",
      "score": 5,
      "reasons": "Менеджер представился, назвал компанию и цель звонка",
      "quotes": "Добрый день! Меня зовут Алексей, компания Ригинтел..."
    },
    {
      "criterion_name": "2. Выявление потребностей",
      "score": 3,
      "reasons": "Частично выявил потребности, не уточнил бюджет",
      "quotes": "Какой продукт вас интересует?"
    },
    {
      "criterion_name": "3. Презентация решения",
      "score": 4,
      "reasons": "Хорошо описал преимущества продукта",
      "quotes": "Наш продукт позволяет автоматизировать..."
    }
  ]
}
```

**Структура каждого критерия:**
| Поле | Тип | Описание |
|------|-----|----------|
| `criterion_name` | string | Название критерия (как в настройках проекта) |
| `score` | int/string | Оценка 0-5 или `""` если не применимо |
| `reasons` | string | Текстовое обоснование выставленной оценки |
| `quotes` | string | Цитаты из транскрипции, подтверждающие оценку |

**Особенности значений score:**
- `5` — критерий полностью выполнен
- `0` — критерий полностью не выполнен  
- `""` (пустая строка) — критерий не применим к данному звонку

**Коды ответа:**
| Код | Описание |
|-----|----------|
| 200 | Успех |
| 204 | Анализ ещё в процессе (нет данных) |
| 401 | Не авторизован |
| 404 | Данные не найдены |
| 500 | Внутренняя ошибка |

---

### 📝 GET /api/transcription — Транскрипция звонка

```http
GET /api/transcription?id_project={project_id}&id_item_set={item_set_id}
```

**Ответ (200):**
```json
{
  "item_set_id": 50,
  "created_at": "2025-01-08T12:00:00",
  "transcription": {
    "output": "Менеджер: Добрый день!\nКлиент: Здравствуйте...",
    "google_doc": "https://docs.google.com/document/d/1abc...",
    "statistics": {
      "word_count": 1234,
      "character_count": 5678,
      "timestamps_count": 45
    },
    "status": "completed",
    "generated_at": "2025-01-08T12:05:00"
  }
}
```

---

### 📁 GET /api/client/project/{project_id}/item-sets — Список звонков

```http
GET /api/client/project/{project_id}/item-sets
```

**Ответ (200):**
```json
{
  "item_sets": [
    {
      "id": 50,
      "name": "call_2025_01_08_abc123",
      "created_at": "2025-01-08T12:00:00",
      "status": "processed",
      "status_within_project": "processed"
    },
    {
      "id": 51,
      "name": "call_2025_01_08_def456",
      "created_at": "2025-01-08T13:00:00",
      "status": "processing",
      "status_within_project": "all_items_processed"
    }
  ],
  "total_count": 2
}
```

---

### 📅 GET /api/client/project/{project_id}/item-sets/by-date — Звонки по дате

```http
GET /api/client/project/{project_id}/item-sets/by-date?date_from=2025-01-01&date_to=2025-01-31&page=1&per_page=50
```

**Query параметры:**
| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| date_from | date | - | Дата начала (YYYY-MM-DD) |
| date_to | date | - | Дата окончания (YYYY-MM-DD) |
| page | int | - | Номер страницы (с 1) |
| per_page | int | - | Количество на странице (1-100) |

> ⚠️ `page` и `per_page` должны быть указаны вместе или оба не указаны

---

### 📋 GET /api/client/item-set/{item_set_id} — Детали звонка

```http
GET /api/client/item-set/{item_set_id}
```

**Ответ (200):**
```json
{
  "id": 50,
  "name": "call_2025_01_08_abc123",
  "created_at": "2025-01-08T12:00:00",
  "status": "processed",
  "status_within_project": "processed",
  "id_project": 1,
  "processing_parameters": {
    "extra_processing_data": {
      "crm_data": {
        "client_name": "Иван Иванов",
        "call_date": "2025-01-08T12:00:00",
        "manager_name": "Алексей Петров",
        "deal_id": "12345"
      }
    }
  }
}
```

---

### 🏷️ GET /api/client/item-set/{item_set_id}/crm-data — CRM данные звонка

```http
GET /api/client/item-set/{item_set_id}/crm-data
```

**Ответ (200):**
```json
{
  "id_item_set": 50,
  "name": "call_2025_01_08_abc123",
  "crm_data": {
    "client_name": "Иван Иванов",
    "call_date": "2025-01-08T12:00:00",
    "manager_name": "Алексей Петров",
    "deal_stage": "Переговоры",
    "deal_id": "12345"
  },
  "week_of_the_call": "2025-01-06 - 2025-01-12",
  "file_duration": 360.5,
  "created_at": "2025-01-08T12:00:00"
}
```

---

### 📈 GET /api/admin/output/formulas/project/{project_id}/item-set/{item_set_id} — Результаты формул

```http
GET /api/admin/output/formulas/project/{project_id}/item-set/{item_set_id}
```

**Ответ (200):**
```json
[
  {
    "id": 1,
    "id_formula": 5,
    "id_project_item_set_output": 100,
    "id_item_set": 50,
    "result": 85.5,
    "error": null,
    "created_at": "2025-01-08T12:00:00",
    "updated_at": "2025-01-08T12:00:00",
    "formula": {
      "name": "Итоговый балл",
      "text": "(score_1 + score_2 + score_3) / 3 * 20",
      "is_default": true
    }
  },
  {
    "id": 2,
    "id_formula": 6,
    "id_project_item_set_output": 100,
    "id_item_set": 50,
    "result": 72.0,
    "error": null,
    "formula": {
      "name": "Балл по продажам",
      "text": "score_5 * 10 + score_6 * 10",
      "is_default": false
    }
  }
]
```

---

### 🔢 Управление формулами проекта

#### GET /api/project/{project_id}/formulas — Список формул
```http
GET /api/project/{project_id}/formulas
```

#### POST /api/project/{project_id}/formulas — Создать формулу
```http
POST /api/project/{project_id}/formulas?name=Итоговый%20балл&formula=(score_1+score_2)/2
```

#### PUT /api/project/{project_id}/formulas/{formula_id} — Обновить формулу
```http
PUT /api/project/{project_id}/formulas/{formula_id}?name=Новое%20имя&formula=(score_1+score_2+score_3)/3
```

#### DELETE /api/project/{project_id}/formulas/{formula_id} — Удалить формулу
```http
DELETE /api/project/{project_id}/formulas/{formula_id}
```

---

### 🛠️ Конструктор формул (Formula Builder)

Эндпоинты для получения данных, необходимых для создания формул:

```http
GET /api/formula-builder/item-set/{item_set_id}
GET /api/formula-builder/project/{project_id}
```

Возвращают:
- Список CRM полей и их значений
- Результаты анализа критериев
- Группы критериев с их настройками

---

### 📊 GET /api/projects — Список проектов

> 💡 Возвращает проекты **текущего авторизованного пользователя**.
> Для получения проектов всех клиентов используй прямой доступ к БД.

```http
GET /api/projects?limit=20&offset=0&status_filter=active&search=продажи
```

**Query параметры:**
| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| limit | int | 20 | Количество (1-100) |
| offset | int | 0 | Смещение |
| sort_by | string | - | Сортировка |
| status_filter | array | [] | Фильтр статуса |
| search | string | - | Поиск по имени |

**Значения sort_by:**
- `created_at` / `created_at-reverse`
- `updated_at` / `updated_at-reverse`
- `active_status` / `active_status-reverse`
- `analyzed_calls_count` / `analyzed_calls_count-reverse`
- `analyzed_minutes` / `analyzed_minutes-reverse`

**Ответ (200):**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "Проект продаж B2B",
      "created_at": "2025-01-01T10:00:00",
      "updated_at": "2025-01-08T12:00:00",
      "id_base_user": 1,
      "active_status": "active",
      "analyzed_calls_count": 150,
      "analyzed_minutes": 4500,
      "id_project_item_set_processing_metadata": 10,
      "id_default_item_set_processing_metadata": 20,
      "id_default_item_processing_metadata": 30
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

### 🔄 PATCH /api/client/item-set/{item_set_id}/zoom-transcript — Обновить Zoom транскрипт

```http
PATCH /api/client/item-set/{item_set_id}/zoom-transcript
Content-Type: application/json

{
  "zoom_transcript": "Текст транскрипции из Zoom..."
}
```

---

## Эндпоинты для отправки данных (POST/PATCH)

### 📤 POST /api/item-set — Создать звонок (ItemSet)

Создаёт новый ItemSet для последующей загрузки файлов.

```http
POST /api/item-set
Content-Type: application/json

{
  "name": "call_2025_01_08",
  "project_id": 1,
  "processing_parameters": {
    "extra_processing_data": {
      "crm_data": {
        "client_name": "Иван Иванов",
        "manager_name": "Алексей Петров",
        "deal_id": "12345",
        "call_date": "2025-01-08T12:00:00"
      }
    }
  }
}
```

**Ответ (200):**
```json
{
  "id": 50,
  "name": "call_2025_01_08_abc123",
  "id_project": 1,
  "status": "added",
  "status_within_project": "added"
}
```

> ⚠️ К имени автоматически добавляется UUID (6 символов) для уникальности

---

### 📎 PATCH /api/item-set/upload — Загрузить файлы

Загружает аудио/видео файлы в созданный ItemSet и запускает обработку.

```http
PATCH /api/item-set/upload?item_set_id={item_set_id}
Content-Type: multipart/form-data

files: [file1.mp3, file2.mp3]
```

**Поддерживаемые форматы:**
- Аудио: `mp3`, `wav`, `m4a`, `ogg`, `flac`, `aac`
- Видео: `mp4`, `webm`, `mov`, `avi`, `mkv`

**Ответ (200):**
```json
[
  {
    "id": 100,
    "name": "file1_abc123.mp3",
    "id_item_set": 50,
    "status": "added",
    "item_link": "https://s3.../file1_abc123.mp3"
  },
  {
    "id": 101,
    "name": "file2_def456.mp3",
    "id_item_set": 50,
    "status": "added",
    "item_link": "https://s3.../file2_def456.mp3"
  }
]
```

**После загрузки:**
1. Файлы сохраняются в S3
2. Автоматически запускается pipeline обработки
3. Статус меняется: `added` → `processing` → `processed`

---

### 🔄 PATCH /api/item-set/processing/restart/{item_set_id} — Перезапуск обработки

Перезапускает обработку для звонка (если произошла ошибка).

```http
PATCH /api/item-set/processing/restart/{item_set_id}
```

**Ответ (200):**
```
"Restarted"
```

---

### 📝 Полный пример: отправка звонка на анализ

```python
import requests

BASE_URL = "https://<domain>/api"
HEADERS = {"API-Access-Key": "<api_key>"}

# 1. Создать ItemSet
response = requests.post(
    f"{BASE_URL}/item-set",
    headers=HEADERS,
    json={
        "name": "call_2025_01_08",
        "project_id": 1,
        "processing_parameters": {
            "extra_processing_data": {
                "crm_data": {
                    "client_name": "Иван Иванов",
                    "manager_name": "Алексей Петров"
                }
            }
        }
    }
)
item_set = response.json()
item_set_id = item_set["id"]
print(f"Создан ItemSet: {item_set_id}")

# 2. Загрузить файлы
with open("call_recording.mp3", "rb") as f:
    response = requests.patch(
        f"{BASE_URL}/item-set/upload",
        headers=HEADERS,
        params={"item_set_id": item_set_id},
        files={"files": ("call_recording.mp3", f, "audio/mpeg")}
    )
items = response.json()
print(f"Загружено файлов: {len(items)}")

# 3. Ждать завершения обработки (polling)
import time

while True:
    response = requests.get(
        f"{BASE_URL}/client/item-set/{item_set_id}",
        headers=HEADERS
    )
    status = response.json()["status_within_project"]
    print(f"Статус: {status}")
    
    if status == "processed":
        print("Анализ завершён!")
        break
    elif status == "processing_failed":
        print("Ошибка обработки")
        break
    
    time.sleep(30)  # Проверять каждые 30 секунд

# 4. Получить результаты
response = requests.get(
    f"{BASE_URL}/insights",
    headers=HEADERS,
    params={"id_project": 1, "id_item_set": item_set_id}
)
insights = response.json()

for insight in insights["insights"]:
    print(f"{insight['criterion_name']}: {insight['score']}")
```

---

## Сырые vs Распарсенные данные

### Важно понимать!

| Эндпоинт | Что возвращает | Нужен парсинг? |
|----------|----------------|----------------|
| `GET /api/insights` | ✅ **Распарсенный** массив критериев | Нет |
| `GET /api/transcription` | ✅ **Готовый** текст + ссылка на Google Doc | Нет |
| `GET /api/project/{id}/item-set/{id}/outputs` | ❌ **Сырой** JSON с вложенными данными | Да |

**Рекомендация:** Используй `/api/insights` и `/api/transcription` — они отдают чистые данные.

---

## Сырые эндпоинты (raw data)

> ⚠️ Эти эндпоинты возвращают данные "как есть" из БД. Используй их только если нужны:
> - Полные промпты GPT (для отладки)
> - Результаты от разных транскрибаторов до объединения
> - Метаданные обработки

### 🎙️ GET /api/item/{item_id}/outputs — Сырые транскрипции файла

**Требует права Admin!**

```http
GET /api/item/{item_id}/outputs
```

**Возвращает сырые транскрипции от всех сервисов:**
```json
[
  {
    "id": 456,
    "id_item": 123,
    "created_at": "2025-01-08T12:00:00",
    "output": {
      "synopsis": "...",  // Сырой Synopsis (Python-строка, нужен ast.literal_eval!)
      "nexara": [...],    // Сырой Nexara (массив объектов)
      "speakai": [...]    // Сырой SpeakAI (массив объектов)
    }
  }
]
```

**Особенности форматов:**

| Сервис | Формат | Парсинг |
|--------|--------|---------|
| Synopsis | Python-строка | `ast.literal_eval()` → JSON |
| Nexara | JSONB массив | `[{start: float, text, speaker}]` |
| SpeakAI | JSONB массив | `[{start: float, text, speakerId: int}]` |

> 📄 Подробный парсинг каждого формата описан в `nakama_api_database_schema.md`

---

### GET /api/project/{project_id}/item-set/{item_set_id}/outputs

Сырые данные анализа критериев (включая промпты GPT).

### GET /api/project/{project_id}/item-set-outputs

Все результаты анализа проекта.

### GET /api/project/{project_id}/processing-outputs

Общий результат обработки проекта (ссылки на отчёты).

### GET /api/item/{item_id}/outputs

Результаты транскрибации отдельного файла.

### GET /api/item-set/{item_set_id}/outputs

Результаты объединения транскрипций.

---

## Статусы

### ItemSet status (транскрибация)

| Статус | Описание |
|--------|----------|
| `added` | Добавлен, ожидает обработки |
| `processing` | Транскрибация в процессе |
| `processed` | Транскрибация завершена |
| `processing_failed` | Ошибка транскрибации |
| `balance_stop` | Остановлен (баланс) |

### ItemSet status_within_project (анализ критериев)

| Статус | Описание |
|--------|----------|
| `added` | Добавлен в проект |
| `all_items_processed` | Транскрибация завершена, ожидает анализа |
| `processing` | Анализ критериев в процессе |
| `processed` | ✅ Анализ завершён |
| `processing_failed` | Ошибка анализа |
| `balance_stop` | Остановлен (баланс) |

### Project active_status

| Статус | Описание |
|--------|----------|
| `active` | ✅ Активен |
| `paused` | Приостановлен |
| `deleted` | Удалён |
| `balance_stop` | Остановлен (баланс) |
| `setting` | В настройке |

---

## Примеры кода

### Python — полный клиент

```python
import requests
from typing import Optional
from datetime import date

class NakamaAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {"API-Access-Key": api_key}
    
    def _get(self, endpoint: str, params: dict = None):
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_projects(self, status_filter: list = None):
        """Получить список проектов"""
        params = {}
        if status_filter:
            params["status_filter"] = status_filter
        return self._get("/projects", params)
    
    def get_item_sets(self, project_id: int):
        """Получить список звонков проекта"""
        return self._get(f"/client/project/{project_id}/item-sets")
    
    def get_item_sets_by_date(
        self, 
        project_id: int, 
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = None,
        per_page: int = None
    ):
        """Получить звонки за период"""
        params = {}
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        if page and per_page:
            params["page"] = page
            params["per_page"] = per_page
        return self._get(f"/client/project/{project_id}/item-sets/by-date", params)
    
    def get_insights(self, project_id: int, item_set_id: int):
        """Получить результаты анализа критериев"""
        return self._get("/insights", {
            "id_project": project_id,
            "id_item_set": item_set_id
        })
    
    def get_transcription(self, project_id: int, item_set_id: int):
        """Получить транскрипцию"""
        return self._get("/transcription", {
            "id_project": project_id,
            "id_item_set": item_set_id
        })
    
    def get_crm_data(self, item_set_id: int):
        """Получить CRM данные"""
        return self._get(f"/client/item-set/{item_set_id}/crm-data")
    
    def get_formula_results(self, project_id: int, item_set_id: int):
        """Получить результаты формул"""
        return self._get(f"/admin/output/formulas/project/{project_id}/item-set/{item_set_id}")


# Использование
client = NakamaAPIClient(
    base_url="https://your-domain.com/api",
    api_key="your-api-key"
)

# Получить все проанализированные звонки за январь
from datetime import date

project_id = 1
item_sets = client.get_item_sets_by_date(
    project_id=project_id,
    date_from=date(2025, 1, 1),
    date_to=date(2025, 1, 31)
)

for item_set in item_sets["item_sets"]:
    # Только завершённые анализом
    if item_set["status_within_project"] == "processed":
        insights = client.get_insights(project_id, item_set["id"])
        
        print(f"\n=== {item_set['name']} ===")
        total_score = 0
        for insight in insights["insights"]:
            score = insight["score"] if isinstance(insight["score"], int) else 0
            total_score += score
            print(f"  {insight['criterion_name']}: {score}")
        
        avg_score = total_score / len(insights["insights"]) if insights["insights"] else 0
        print(f"  Средний балл: {avg_score:.1f}")
```

### JavaScript/TypeScript

```typescript
interface Insight {
  criterion_name: string;
  score: number | string;
  reasons: string;
  quotes: string;
}

interface InsightsResponse {
  project_id: number;
  item_set_id: number;
  created_at: string;
  insights: Insight[];
}

class NakamaAPIClient {
  private baseUrl: string;
  private headers: HeadersInit;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.headers = {
      'API-Access-Key': apiKey,
      'Content-Type': 'application/json'
    };
  }

  private async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.append(key, String(value));
        }
      });
    }
    
    const response = await fetch(url.toString(), { headers: this.headers });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  async getInsights(projectId: number, itemSetId: number): Promise<InsightsResponse> {
    return this.get('/insights', {
      id_project: projectId,
      id_item_set: itemSetId
    });
  }

  async getItemSets(projectId: number) {
    return this.get(`/client/project/${projectId}/item-sets`);
  }
}

// Использование
const client = new NakamaAPIClient('https://your-domain.com/api', 'your-api-key');

const insights = await client.getInsights(1, 50);
insights.insights.forEach(insight => {
  console.log(`${insight.criterion_name}: ${insight.score}`);
});
```

### cURL примеры

```bash
# Авторизация по API-ключу
API_KEY="your-api-key"
BASE_URL="https://your-domain.com/api"

# Получить список проектов
curl -X GET "$BASE_URL/projects" \
  -H "API-Access-Key: $API_KEY"

# Получить список звонков проекта
curl -X GET "$BASE_URL/client/project/1/item-sets" \
  -H "API-Access-Key: $API_KEY"

# Получить результаты анализа
curl -X GET "$BASE_URL/insights?id_project=1&id_item_set=50" \
  -H "API-Access-Key: $API_KEY"

# Получить транскрипцию
curl -X GET "$BASE_URL/transcription?id_project=1&id_item_set=50" \
  -H "API-Access-Key: $API_KEY"

# Получить CRM данные
curl -X GET "$BASE_URL/client/item-set/50/crm-data" \
  -H "API-Access-Key: $API_KEY"

# Получить звонки за период с пагинацией
curl -X GET "$BASE_URL/client/project/1/item-sets/by-date?date_from=2025-01-01&date_to=2025-01-31&page=1&per_page=50" \
  -H "API-Access-Key: $API_KEY"
```

---

## Обработка ошибок

### HTTP коды

| Код | Описание | Действие |
|-----|----------|----------|
| 200 | Успех | Обработать данные |
| 204 | Нет контента | Данные в обработке, повторить позже |
| 400 | Неверный запрос | Проверить параметры |
| 401 | Не авторизован | Проверить API-ключ/токен |
| 403 | Доступ запрещён | Нет прав на ресурс |
| 404 | Не найдено | Проверить ID |
| 422 | Ошибка валидации | Проверить формат данных |
| 500 | Внутренняя ошибка | Связаться с поддержкой |

### Формат ошибки

```json
{
  "detail": "Описание ошибки"
}
```

### Пример обработки

```python
try:
    insights = client.get_insights(project_id, item_set_id)
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 204:
        print("Анализ ещё не завершён, повторите позже")
    elif e.response.status_code == 404:
        print("Звонок не найден")
    elif e.response.status_code == 401:
        print("Ошибка авторизации, проверьте API-ключ")
    else:
        print(f"Ошибка: {e.response.json().get('detail', str(e))}")
```

---

## Типичный сценарий интеграции

```
1. Получить API-ключ от администратора
         ↓
2. GET /api/projects — найти нужный project_id
         ↓
3. GET /api/client/project/{id}/item-sets — получить список звонков
         ↓
4. Отфильтровать по status_within_project == "processed"
         ↓
5. Для каждого звонка:
   ├── GET /api/insights — оценки критериев
   ├── GET /api/transcription — текст разговора
   └── GET /api/client/item-set/{id}/crm-data — CRM данные
         ↓
6. Сохранить данные в свою систему
```

---

## Ограничения

| Параметр | Значение |
|----------|----------|
| Пагинация | max 100 элементов |
| JWT access token | 4 часа |
| JWT refresh token | 7 дней |
| Размер reasons/quotes | до 5000 символов |

---

## Swagger/OpenAPI

Документация доступна по адресу:
```
https://<domain>/api/openapi.json
https://<domain>/docs
```
