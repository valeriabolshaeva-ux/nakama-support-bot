ДДДД# nakama_api — Структура базы данных

> Документация для прямого подключения к PostgreSQL базе данных nakama_api

## Подключение к БД

### Параметры подключения

```
Host: <pg_host>
Port: <pg_port>
Database: <pg_database>
User: <pg_user>
Password: <pg_password>
```

### Connection string

```
postgresql://<pg_user>:<pg_password>@<pg_host>:<pg_port>/<pg_database>
```

### Python (asyncpg/SQLAlchemy)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:password@host:port/database"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async with async_session() as session:
    result = await session.execute(text("SELECT * FROM object.project LIMIT 10"))
    projects = result.fetchall()
```

### Python (psycopg2)

```python
import psycopg2

conn = psycopg2.connect(
    host="host",
    port=5432,
    database="database",
    user="user",
    password="password"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM object.project LIMIT 10")
projects = cursor.fetchall()
```

---

## Схемы (Schemas)

База данных разделена на логические схемы:

| Схема | Описание |
|-------|----------|
| `user` | Пользователи и балансы |
| `object` | Основные объекты (проекты, звонки, файлы) |
| `processor` | Процессоры обработки |
| `processing_metadata` | Метаданные обработки |
| `output` | Результаты обработки |
| `consumed_processed_units` | Статистика использования ресурсов |
| `config` | Конфигурация системы |

---

## Основные таблицы

### user.base_user — Пользователи

```sql
CREATE TABLE "user".base_user (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    hashed_password BYTEA,
    date_reg TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    date_last_login TIMESTAMP WITH TIME ZONE,
    api_key VARCHAR(250),                    -- API ключ для интеграций
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_superuser BOOLEAN DEFAULT false NOT NULL,
    is_verified BOOLEAN DEFAULT false NOT NULL,
    main_transcribe_folder_url VARCHAR(500), -- Google Drive папка
    balance_minutes INTEGER DEFAULT 0,       -- Баланс минут
    balance_mode VARCHAR(50) DEFAULT 'basic' -- basic | strict
);
```

**Ключевые поля:**
- `api_key` — используется для авторизации в API
- `balance_minutes` — оставшийся баланс минут транскрибации
- `balance_mode` — режим баланса (basic = уходить в минус, strict = останавливать)

---

### object.project — Проекты

```sql
CREATE TABLE object.project (
    id SERIAL PRIMARY KEY,
    name VARCHAR(250) NOT NULL,
    created_at TIMESTAMP DEFAULT now() NOT NULL,
    updated_at TIMESTAMP DEFAULT now(),
    id_base_user INTEGER REFERENCES "user".base_user(id),
    id_project_item_set_processing_metadata INTEGER NOT NULL,  -- Метаданные анализа критериев
    id_default_item_set_processing_metadata INTEGER NOT NULL,  -- Метаданные объединения
    id_default_item_processing_metadata INTEGER NOT NULL,      -- Метаданные транскрибации
    active_status VARCHAR(250) DEFAULT 'active' NOT NULL       -- active|paused|deleted|balance_stop|setting
);
```

**Связи:**
- `id_base_user` → `user.base_user.id` — владелец проекта
- `id_project_item_set_processing_metadata` → метаданные с настройками критериев

---

### object.item_set — Наборы файлов (звонки)

```sql
CREATE TABLE object.item_set (
    id SERIAL PRIMARY KEY,
    name VARCHAR(250) NOT NULL,
    created_at TIMESTAMP DEFAULT now() NOT NULL,
    updated_at TIMESTAMP DEFAULT now(),
    id_base_user INTEGER REFERENCES "user".base_user(id),
    id_project INTEGER NOT NULL REFERENCES object.project(id),
    status VARCHAR(250) NOT NULL,                    -- added|processing|processed|processing_failed|balance_stop
    status_within_project VARCHAR(250) NOT NULL,    -- added|all_items_processed|processing|processed|processing_failed|balance_stop
    reanalysis_count INTEGER DEFAULT 0 NOT NULL     -- Количество повторных анализов
);
```

**Статусы:**
- `status` — статус транскрибации
- `status_within_project` — статус анализа по критериям

---

### object.item — Файлы

```sql
CREATE TABLE object.item (
    id SERIAL PRIMARY KEY,
    name VARCHAR(250) NOT NULL,
    id_item_type INTEGER REFERENCES object.item_type(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    id_base_user INTEGER REFERENCES "user".base_user(id),
    id_item_set INTEGER NOT NULL REFERENCES object.item_set(id),
    item_link VARCHAR(1000),                         -- Ссылка на файл в S3
    last_processing_date TIMESTAMP WITH TIME ZONE DEFAULT now(),
    status VARCHAR(250) NOT NULL                     -- added|processing|processed|processing_failed|balance_stop
);
```

---

### object.project_formula — Формулы проекта

```sql
CREATE TABLE object.project_formula (
    id SERIAL PRIMARY KEY,
    id_project INTEGER NOT NULL REFERENCES object.project(id),
    id_formula INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    is_default BOOLEAN DEFAULT true NOT NULL,
    name VARCHAR(250) NOT NULL,                      -- Название формулы
    formula TEXT NOT NULL                            -- Текст формулы (например: "(score_1 + score_2) / 2")
);
```

**Синтаксис формул:**

Формулы — это Python-выражения с доступными переменными:

| Переменная | Описание | Пример |
|------------|----------|--------|
| `score_0`, `score_1`, ... | Баллы критериев (по индексу, с 0) | `score_0 + score_1` |
| `file_duration` | Длительность файла в секундах | `file_duration / 60` |
| `crm_<key>` | CRM поля по ключу | `crm_deal_amount` |

**Примеры формул:**
```python
# Средний балл по первым 3 критериям
(score_0 + score_1 + score_2) / 3

# Взвешенный итоговый балл
(score_0 * 2 + score_1 * 3 + score_2) / 6 * 100

# Балл в процентах от максимума (5 критериев по 5 баллов)
(score_0 + score_1 + score_2 + score_3 + score_4) / 25 * 100
```

---

## Таблицы результатов (output)

### output.project_item_set_processing_output — Результаты анализа критериев ⭐

**Самая важная таблица для получения оценок!**

```sql
CREATE TABLE output.project_item_set_processing_output (
    id SERIAL PRIMARY KEY,
    id_processor INTEGER NOT NULL REFERENCES processor.processor(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    output JSONB,                                    -- Результаты анализа критериев
    id_metadata INTEGER NOT NULL REFERENCES processing_metadata.project_item_set_processing_metadata(id),
    id_item_set INTEGER NOT NULL REFERENCES object.item_set(id),
    id_project INTEGER NOT NULL REFERENCES object.project(id)
);
```

**Структура поля `output` (вложенный JSON!):**

Критерии приходят пакетами от GPT (по 5-10 штук за раз). Каждый пакет — отдельный элемент массива:

```json
[
  {
    "messages": [...],  // Промпт для критериев 1-5 (для отладки)
    "response": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "```json\n[{\"criterion\": \"1. Приветствие\", \"score\": 5, \"reason\": \"...\", \"quote\": \"...\"}]\n```"
        }
      }
    ]
  },
  {
    "messages": [...],  // Промпт для критериев 6-10
    "response": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "```json\n[{\"criterion\": \"6. Работа с возражениями\", \"score\": 3, ...}]\n```"
        }
      }
    ]
  }
]
```

> ⚠️ **КРИТИЧНО!** Поле `content` содержит:
> 1. **JSON как строку**, а не как объект
> 2. Часто с **markdown-обёрткой** ` ```json ... ``` `
> 3. Может содержать **управляющие символы** и невалидные escape-последовательности

**Распарсенная структура критериев:**
```json
[
  {
    "criterion": "1. Приветствие и установление контакта",
    "score": 5,
    "reason": "Менеджер представился, назвал компанию",
    "quote": "Добрый день! Меня зовут Алексей..."
  },
  {
    "criterion": "2. Выявление потребностей",
    "score": 3,
    "reason": "Частично выявил потребности",
    "quote": "Какой продукт вас интересует?"
  }
]
```

**Как извлечь критерии (Python) — базовый способ:**
```python
import json

# Получаем output из БД
raw_output = row['output']  # Это уже dict, не строка

criteria = []
for block in raw_output:
    for response in block.get('response', []):
        content_str = response.get('message', {}).get('content', '[]')
        # Парсим JSON из строки
        parsed = json.loads(content_str)
        criteria.extend(parsed)

for c in criteria:
    print(f"{c['criterion']}: {c['score']}")
```

---

## 🔧 Готовые функции парсинга (из nakama_api)

В nakama_api уже есть готовые функции для парсинга сырых данных. Рекомендую использовать их логику:

### Функция `parse_insights()` — для API

Используется в эндпоинте `/api/insights`. Возвращает **список объектов**:

```python
# Результат parse_insights():
[
    {
        "criterion_name": "1. Приветствие и установление контакта",
        "score": 5,
        "reasons": "Менеджер представился, назвал компанию",
        "quotes": "Добрый день! Меня зовут Алексей..."
    },
    {
        "criterion_name": "2. Выявление потребностей", 
        "score": 3,
        "reasons": "Частично выявил потребности",
        "quotes": "Какой продукт вас интересует?"
    }
]
```

**Полная реализация (упрощённая версия):**
```python
import json
import re

def parse_insights(content: str) -> list[dict]:
    """
    Парсит сырой ответ GPT в список критериев.
    
    Args:
        content: Строка из response->message->content
        
    Returns:
        Список словарей с criterion_name, score, reasons, quotes
    """
    if not content or not isinstance(content, str):
        return []
    
    content = content.strip()
    data = []
    
    # Убираем markdown code fences если есть
    if '```json' in content:
        # Извлекаем все JSON блоки
        pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(pattern, content, re.DOTALL)
        all_criteria = []
        for match in matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, list):
                    all_criteria.extend(parsed)
                elif isinstance(parsed, dict):
                    all_criteria.append(parsed)
            except json.JSONDecodeError:
                continue
        criteria = all_criteria
    else:
        # Ищем JSON массив
        json_start = content.find('[')
        json_end = content.rfind(']') + 1
        if json_start == -1 or json_end <= json_start:
            return []
        json_str = content[json_start:json_end]
        criteria = json.loads(json_str)
    
    # Преобразуем в нужный формат
    for criterion in criteria:
        if not isinstance(criterion, dict):
            continue
            
        # Парсим score
        raw_score = criterion.get("score", "")
        if isinstance(raw_score, (int, float)):
            parsed_score = int(raw_score)
        elif isinstance(raw_score, str) and raw_score.strip().isdigit():
            parsed_score = int(raw_score.strip())
        elif raw_score in ["", "Пусто", "[Пусто]", None]:
            parsed_score = ""
        else:
            parsed_score = raw_score
            
        data.append({
            "criterion_name": criterion.get("criterion", ""),
            "score": parsed_score,
            "reasons": str(criterion.get("reason", "")).strip(),
            "quotes": str(criterion.get("quote", "")).strip()
        })
    
    return data
```

### Функция `parse_json_response()` — для Google Sheets

Используется для записи в отчёты. Возвращает **плоский словарь** с индексами:

```python
# Результат parse_json_response():
{
    "count_criteria": 10,
    "score_0": 5,
    "reason_0": "Менеджер представился, назвал компанию",
    "quote_0": "Добрый день! Меня зовут Алексей...",
    "score_1": 3,
    "reason_1": "Частично выявил потребности",
    "quote_1": "Какой продукт вас интересует?",
    ...
}
```

Этот формат удобен для:
- Записи в ячейки таблицы по индексу
- Работы с формулами (`score_0 + score_1 / 2`)
- Сопоставления с заголовками столбцов

---

## 📊 Как nakama записывает данные в Google Sheets

Nakama автоматически записывает результаты в Google таблицу клиента. Понимание этого процесса поможет повторить логику.

### Куда записываются данные

| Данные | Куда записывается |
|--------|-------------------|
| Транскрипция | Google Doc (ссылка в `output.item_set_processing_output`) |
| Результаты критериев | Google Sheets, лист "AI" |
| CRM данные | Google Sheets, столбцы с названиями из `crm_key_to_label` |
| Результаты формул | Google Sheets, столбцы с названиями формул |

### Структура отчёта Google Sheets

Лист "AI" имеет следующие стандартные колонки:

| Заголовок | Ключ данных | Источник |
|-----------|-------------|----------|
| № | `number` | Порядковый номер |
| Call file name | `call_name` | `item_set.name` |
| Transcription | `transcription` | Ссылка на Google Doc |
| Week of the call | `default_call_week` | Вычисляется из `call_date` |
| Item Set ID | `id_item_set` | `item_set.id` |
| Item Set Created At | `item_set_created_at` | `item_set.created_at` |
| Real File Duration | `real_file_duration` | `item_processing_metadata.file_duration` |

Далее идут:
- **Колонки CRM данных** — названия из `crm_key_to_label_global`
- **Колонки критериев** — формат: `"{номер} {название}..."`, `"{номер} Reason"`, `"{номер} Quote"`
- **Колонки формул** — названия из `project_formula.name`

### Логика записи критериев в колонки

```python
# Данные критериев после парсинга:
all_criteria_data = {
    "score_0": 5,
    "reason_0": "Менеджер представился",
    "quote_0": "Добрый день!",
    "score_1": 3,
    # ...
}

# Заголовки таблицы (row 1):
header_index = {
    "1. Приветствие": 8,      # колонка H
    "1. Reason": 9,            # колонка I
    "1. Quote": 10,            # колонка J
    "2. Выявление": 11,        # колонка K
    # ...
}

# Сопоставление: score_0 → "1. Приветствие" (колонка 8)
# Логика: ищем заголовок начинающийся с "0" или "1" для score_0
for data_key, value in all_criteria_data.items():
    # score_0 → field_type="score", criterion_num="0"
    field_type, criterion_num = data_key.split('_', 1)
    
    for header_text, col_idx in header_index.items():
        # Ищем заголовок начинающийся с номера критерия
        if header_text.startswith(f"{criterion_num}.") or header_text.startswith(f"{criterion_num} "):
            if field_type == "score" and "score" not in header_text.lower():
                # Основная колонка критерия (без слова "reason"/"quote")
                write_to_cell(row, col_idx, value)
            elif field_type == "reason" and "reason" in header_text.lower():
                write_to_cell(row, col_idx, value)
            elif field_type == "quote" and "quote" in header_text.lower():
                write_to_cell(row, col_idx, value)
```

### Получение URL отчёта

```sql
-- URL Google Sheets отчёта
SELECT output_data->>'report_url' as report_url
FROM output.project_processing_output
WHERE id_project = 1;
```

---

## Что где хранится (итоговая схема)

| Данные | Таблица | Формат | Нужен парсинг? |
|--------|---------|--------|----------------|
| **Synopsis сырой** | `output.item_processing_output` | `output->>'synopsis'` (Python-строка!) | **Да, сложный!** |
| **Nexara сырой** | `output.item_processing_output` | `output->'nexara'` (JSONB массив) | Да, простой |
| **SpeakAI сырой** | `output.item_processing_output` | `output->'speakai'` (JSONB массив) | Да, простой |
| Транскрипция объединённая | `output.item_set_processing_output` | `{output: "текст", google_doc: "url"}` | Нет |
| Результаты критериев | `output.project_item_set_processing_output` | Вложенный JSON в markdown | **Да!** |
| Результаты формул | `output.formula_output` | Float `result` | Нет |
| CRM данные | `processing_metadata.item_set_processing_metadata` | JSONB `processing_parameters` | Нет |
| Ссылки на отчёты | `output.project_processing_output` | `{report_url, google_doc}` | Нет |

### Уровни обработки транскрипций

```
1. СЫРАЯ (от сервиса)
   └── output.item_processing_output.output->'nexara' / ->>'synopsis'
   └── Формат разный у каждого сервиса, нужен парсинг

2. ОЧИЩЕННАЯ (clean_*)
   └── Нормализованные таймстампы, спикеры
   └── Унифицированный формат: [{start, speaker, text}, ...]
   └── В БД НЕ хранится! Вычисляется на лету

3. ОБЪЕДИНЁННАЯ (AI merge)
   └── output.item_set_processing_output.output
   └── Финальный текст + ссылка на Google Doc
   └── Результат слияния лучших частей из разных сервисов
```

---

### output.item_set_processing_output — Результаты объединения транскрипций

```sql
CREATE TABLE output.item_set_processing_output (
    id SERIAL PRIMARY KEY,
    id_processor INTEGER NOT NULL REFERENCES processor.processor(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    output JSONB,                                    -- Объединённая транскрипция
    id_metadata INTEGER NOT NULL REFERENCES processing_metadata.item_set_processing_metadata(id),
    id_item_set INTEGER NOT NULL REFERENCES object.item_set(id)
);
```

**Структура поля `output`:**
```json
{
  "output": "Менеджер: Добрый день!\nКлиент: Здравствуйте...",
  "google_doc": "https://docs.google.com/document/d/...",
  "statistics": {
    "word_count": 1234,
    "character_count": 5678
  },
  "status": "completed",
  "generated_at": "2025-01-08T12:00:00"
}
```

---

### output.item_processing_output — Результаты транскрибации файла

```sql
CREATE TABLE output.item_processing_output (
    id SERIAL PRIMARY KEY,
    id_processor INTEGER NOT NULL REFERENCES processor.processor(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    output JSONB,                                    -- Транскрипция от сервисов
    id_metadata INTEGER NOT NULL REFERENCES processing_metadata.item_processing_metadata(id),
    id_item INTEGER NOT NULL REFERENCES object.item(id)
);
```

**Структура поля `output`:**
```json
{
  "synopsis": "...",    // Результат от Synopsis (СТРОКА, не массив!)
  "speakai": [...],     // Результат от SpeakAI (массив)
  "nexara": [...]       // Результат от Nexara (массив)
}
```

---

## 🎙️ Сырые транскрипции от разных сервисов

В таблице `output.item_processing_output` хранятся **сырые** транскрипции от каждого сервиса.
У каждого сервиса свой формат — ниже подробно разобрано как их парсить.

### Nexara — формат данных

**Сырой формат в БД** (массив объектов):
```json
[
  {"start": 0.5, "text": "Привет", "speaker": "SPEAKER_00"},
  {"start": 2.3, "text": "Здравствуйте", "speaker": "SPEAKER_01"},
  {"start": 5.1, "text": "Меня зовут Алексей", "speaker": "SPEAKER_00"}
]
```

**Особенности:**
- `start` — время в **секундах** (float)
- `speaker` — идентификатор спикера (строка)
- `text` — текст реплики

**SQL для получения сырой Nexara:**
```sql
SELECT 
    ipo.id_item,
    ipo.output->'nexara' as nexara_raw
FROM output.item_processing_output ipo
WHERE ipo.id_item = 123;
```

**Python парсинг (чистый, как в nakama):**
```python
def clean_nexara(nexara_result):
    """Очищает и нормализует Nexara транскрипцию"""
    cleaned = []
    for item in nexara_result:
        start = item.get("start")
        
        # Конвертация секунд в HH:MM:SS.mmm
        if isinstance(start, (int, float)):
            ms = int(round((start - int(start)) * 1000))
            s = int(start) % 60
            m = (int(start) // 60) % 60
            h = int(start) // 3600
            ts = f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
        else:
            ts = str(start)
        
        # Нормализация имени спикера
        speaker = item.get("speakerId") or item.get("speaker") or "SPEAKER"
        speaker = speaker.upper().replace("-", "_")
        
        text = (item.get("text") or "").strip()
        
        cleaned.append({"start": ts, "speaker": speaker, "text": text})
    
    return cleaned

# Результат после очистки:
# [{"start": "00:00:00.500", "speaker": "SPEAKER_00", "text": "Привет"}, ...]
```

---

### Synopsis — формат данных (СЛОЖНЫЙ!)

**Сырой формат в БД** — это **СТРОКА с Python-структурой** (не JSON!):

```python
# Внимание: это строка, которую нужно парсить через ast.literal_eval()
"[{'transcription': '[\"{\\\\"start\\\\":\\\\"00:00:01.234\\\\",\\\\"speaker\\\\":\\\\"Speaker 1\\\\",\\\\"text\\\\":\\\\"Привет\\\\"}\", \"{\\\\"start\\\\":\\\\"00:00:03.567\\\\",\\\\"speaker\\\\":\\\\"Speaker 2\\\\",\\\\"text\\\\":\\\\"Здравствуйте\\\\\"}\"]', 'status': 'completed'}]"
```

**Разбор структуры:**
1. Внешний уровень — Python-список (парсим через `ast.literal_eval`)
2. Каждый элемент — словарь с полем `transcription`
3. `transcription` — JSON-строка со списком JSON-строк реплик
4. Каждая реплика — ещё одна JSON-строка с полями `start`, `speaker`, `text`

**SQL для получения сырого Synopsis:**
```sql
SELECT 
    ipo.id_item,
    ipo.output->>'synopsis' as synopsis_raw  -- Обратите внимание: ->> для строки!
FROM output.item_processing_output ipo
WHERE ipo.id_item = 123;
```

**Python парсинг (как в nakama):**
```python
import ast
import json
import re

def clean_synopsis(synopsis_result_str):
    """
    Парсит сложную структуру Synopsis.
    Ожидает строку с Python-like списком.
    """
    if not synopsis_result_str:
        return []
    
    # 1. Парсим внешний Python-список
    root = ast.literal_eval(synopsis_result_str)
    
    # Проверка на статус "ещё обрабатывается"
    if isinstance(root, dict) and root.get('status') == "202 Running":
        return []
    
    cleaned = []
    for rec in root:
        tr = rec.get("transcription")
        if not tr:
            continue
        
        # 2. Парсим JSON-список реплик
        outer_list = json.loads(tr)
        
        for chunk in outer_list:
            # 3. Каждая реплика — ещё одна JSON-строка
            msg = json.loads(chunk)
            
            start = msg.get("start", "")
            
            # Нормализация таймстампа (HH:MM:SS.mmm)
            ts = normalize_timestamp(start)
            
            # Нормализация спикера
            speaker = msg.get("speaker") or "SPEAKER"
            speaker = speaker.upper().replace("-", "_")
            
            text = (msg.get("text") or "").strip()
            
            cleaned.append({"start": ts, "speaker": speaker, "text": text})
    
    return cleaned

def normalize_timestamp(ts: str) -> str:
    """Нормализует таймстамп к формату HH:MM:SS.mmm"""
    s = str(ts).strip()
    m = re.fullmatch(r"(\d{1,2}):([0-5]?\d):([0-5]?\d)(?:\.(\d{1,6}))?", s)
    if not m:
        return s
    h, mm, ss, frac = m.groups()
    h = int(h); mm = int(mm); ss = int(ss)
    frac = (frac or "")[:3].ljust(3, "0")
    return f"{h:02d}:{mm:02d}:{ss:02d}.{frac}"

# Результат после очистки:
# [{"start": "00:00:01.234", "speaker": "SPEAKER_01", "text": "Привет"}, ...]
```

---

### SpeakAI — формат данных

**Сырой формат в БД** (массив объектов):
```json
[
  {"start": 0.5, "text": "Привет", "speakerId": 0},
  {"start": 2.3, "text": "Здравствуйте", "speakerId": 1}
]
```

**Особенности:**
- `start` — время в секундах (float)
- `speakerId` — числовой ID спикера (int)
- `text` — текст реплики

**SQL:**
```sql
SELECT ipo.output->'speakai' as speakai_raw
FROM output.item_processing_output ipo
WHERE ipo.id_item = 123;
```

---

### Zoom Transcript — формат данных

Если транскрипция загружена из Zoom, она хранится в формате VTT/SRT:

**Сырой формат:**
```
1
00:00:01,234 --> 00:00:03,456
Алексей: Добрый день!

2
00:00:03,567 --> 00:00:05,678
Клиент: Здравствуйте
```

**Python парсинг (как в nakama):**
```python
import re

def clean_zoom_transcript(zoom_transcript_str):
    """Парсит VTT/SRT формат Zoom"""
    if not zoom_transcript_str:
        return ""
    
    text = str(zoom_transcript_str).replace('\r\n', '\n').replace('\\n', '\n')
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)  # Убираем BOM
    
    lines = text.split('\n')
    out = []
    current_ts = None
    
    re_idx = re.compile(r'^\s*\d+\s*$')  # Индексы блоков: "1", "2"...
    re_time = re.compile(r'(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->')
    re_speaker = re.compile(r'^([^:]+):\s*(.+)$')  # "Имя: текст"
    
    for line in lines:
        line = line.strip()
        if not line or re_idx.match(line):
            continue
        
        time_match = re_time.match(line)
        if time_match:
            h, m, s, ms = map(int, time_match.groups())
            current_ts = f"[{h:02d}:{m:02d}:{s:02d}.{ms:03d}]"
            continue
        
        speaker_match = re_speaker.match(line)
        if speaker_match and current_ts:
            speaker = speaker_match.group(1).strip()
            text = speaker_match.group(2).strip()
            out.append(f"{current_ts} - {speaker} - {text}")
            current_ts = None
    
    return '\n'.join(out)
```

---

### Унифицированный формат после очистки

После применения функций `clean_*` все транскрипции приводятся к единому формату:

```json
[
  {"start": "00:00:01.234", "speaker": "SPEAKER_01", "text": "Добрый день!"},
  {"start": "00:00:03.567", "speaker": "SPEAKER_02", "text": "Здравствуйте"},
  {"start": "00:00:05.890", "speaker": "SPEAKER_01", "text": "Меня зовут Алексей"}
]
```

**Форматирование в текст:**
```python
def format_lines(items):
    """Форматирует в читаемый текст"""
    return "\n".join(f"[{it['start']}] - {it['speaker']} - {it['text']}" for it in items)

# Результат:
# [00:00:01.234] - SPEAKER_01 - Добрый день!
# [00:00:03.567] - SPEAKER_02 - Здравствуйте
# [00:00:05.890] - SPEAKER_01 - Меня зовут Алексей
```

---

### Полный SQL для получения всех транскрипций файла

```sql
-- Все транскрипции для одного item (файла)
SELECT 
    ipo.id,
    ipo.id_item,
    ipo.created_at,
    ipo.output->>'synopsis' as synopsis_raw,      -- Строка (нужен ast.literal_eval + json.loads)
    ipo.output->'nexara' as nexara_raw,           -- JSONB массив
    ipo.output->'speakai' as speakai_raw          -- JSONB массив
FROM output.item_processing_output ipo
WHERE ipo.id_item = 123
ORDER BY ipo.created_at DESC
LIMIT 1;

-- Все транскрипции для item_set (звонка) — может быть несколько файлов
SELECT 
    i.id as item_id,
    i.name as file_name,
    ipo.output->>'synopsis' as synopsis_raw,
    ipo.output->'nexara' as nexara_raw,
    ipo.output->'speakai' as speakai_raw
FROM object.item i
JOIN output.item_processing_output ipo ON ipo.id_item = i.id
WHERE i.id_item_set = 50
ORDER BY i.id;
```

---

### output.formula_output — Результаты формул

```sql
CREATE TABLE output.formula_output (
    id SERIAL PRIMARY KEY,
    id_formula INTEGER NOT NULL REFERENCES object.project_formula(id),
    id_project_item_set_output INTEGER NOT NULL REFERENCES output.project_item_set_processing_output(id),
    id_item_set INTEGER NOT NULL REFERENCES object.item_set(id),
    result FLOAT,                                    -- Вычисленный результат
    error VARCHAR,                                   -- Ошибка вычисления (если есть)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);
```

---

### output.project_processing_output — Общий результат проекта

```sql
CREATE TABLE output.project_processing_output (
    id SERIAL PRIMARY KEY,
    id_project INTEGER NOT NULL REFERENCES object.project(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    output_data JSONB                                -- Ссылки на отчёты
);
```

**Структура поля `output_data`:**
```json
{
  "report_url": "https://docs.google.com/spreadsheets/d/...",
  "template_report_url": "https://docs.google.com/spreadsheets/d/...",
  "child_folder_url": "https://drive.google.com/drive/folders/..."
}
```

---

## Таблицы метаданных (processing_metadata)

### processing_metadata.project_item_set_processing_metadata

Настройки анализа критериев для проекта.

```sql
CREATE TABLE processing_metadata.project_item_set_processing_metadata (
    id SERIAL PRIMARY KEY,
    id_processor INTEGER NOT NULL REFERENCES processor.processor(id),
    processing_parameters JSONB NOT NULL,            -- Настройки критериев
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    is_default BOOLEAN DEFAULT true NOT NULL,
    id_project INTEGER REFERENCES object.project(id),
    id_item_set INTEGER REFERENCES object.item_set(id)
);
```

**Структура `processing_parameters`:**
```json
{
  "criteria_settings": {
    "criteria_sheet_id": "1abc...",
    "model_name": "gpt-4o",
    "model_temperature": 0.2,
    "use_pii_detection": true
  },
  "extra_processing_data": {
    "crm_data": {
      "client_name": "...",
      "manager_name": "..."
    }
  }
}
```

---

### processing_metadata.item_set_processing_metadata

Настройки объединения транскрипций.

```sql
CREATE TABLE processing_metadata.item_set_processing_metadata (
    id SERIAL PRIMARY KEY,
    id_processor INTEGER NOT NULL REFERENCES processor.processor(id),
    processing_parameters JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    is_default BOOLEAN DEFAULT true NOT NULL,
    id_item_set INTEGER REFERENCES object.item_set(id)
);
```

---

### processing_metadata.item_processing_metadata

Настройки транскрибации файла.

```sql
CREATE TABLE processing_metadata.item_processing_metadata (
    id SERIAL PRIMARY KEY,
    id_processor INTEGER NOT NULL REFERENCES processor.processor(id),
    processing_parameters JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    is_default BOOLEAN DEFAULT true NOT NULL,
    id_item INTEGER REFERENCES object.item(id)
);
```

**Структура `processing_parameters`:**
```json
{
  "file_duration": 360.5,                // Длительность файла в секундах
  "extra_processing_data": {
    "crm_data": {...}
  }
}
```

---

## Таблица процессоров

### processor.processor

```sql
CREATE TABLE processor.processor (
    id SERIAL PRIMARY KEY,
    internal_name VARCHAR(500) NOT NULL,             -- transcribe, json_merger, criteria_gpt, etc.
    is_public BOOLEAN DEFAULT false NOT NULL,
    user_facing_name VARCHAR(500),
    is_enabled BOOLEAN DEFAULT false NOT NULL,
    id_type_input INTEGER REFERENCES object.item_type(id),
    type_output VARCHAR(500),
    processor_type VARCHAR(255) NOT NULL             -- item, item_set, project
);
```

**Основные процессоры:**
| internal_name | Описание |
|---------------|----------|
| `transcribe` | Транскрибация файлов |
| `json_merger` | Объединение транскрипций (старый) |
| `transcript_merger` | Объединение транскрипций (новый) |
| `criteria_gpt` | Анализ по критериям |

---

## Flow данных через таблицы

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        КАК ДАННЫЕ ПРОХОДЯТ ЧЕРЕЗ БД                             │
└─────────────────────────────────────────────────────────────────────────────────┘

1. СОЗДАНИЕ ЗВОНКА
   object.item_set (status='added', status_within_project='added')
        │
        └── object.item (status='added') — для каждого файла
              │
              └── processing_metadata.item_processing_metadata (настройки)

2. ТРАНСКРИБАЦИЯ
   object.item (status='processing' → 'processed')
        │
        └── output.item_processing_output (output: {synopsis: [...], speakai: [...]})

3. ОБЪЕДИНЕНИЕ ТРАНСКРИПЦИЙ  
   object.item_set (status='processed', status_within_project='all_items_processed')
        │
        └── output.item_set_processing_output (output: {output: "текст", google_doc: "url"})

4. АНАЛИЗ КРИТЕРИЕВ
   object.item_set (status_within_project='processing' → 'processed')
        │
        ├── output.project_item_set_processing_output (output: [{response: [...]}])
        │
        └── output.formula_output (result: 85.5) — для каждой формулы
```

---

## Полезные SQL запросы

### 👥 Список всех клиентов (пользователей)

```sql
-- Все активные клиенты
SELECT 
    id,
    name,
    email,
    date_reg,
    date_last_login,
    balance_minutes,
    balance_mode,
    is_active
FROM "user".base_user
WHERE is_active = true
ORDER BY date_reg DESC;
```

### 📁 Список всех проектов

```sql
-- Все проекты с названиями клиентов
SELECT 
    p.id as project_id,
    p.name as project_name,
    p.created_at,
    p.active_status,
    u.id as user_id,
    u.name as user_name,
    u.email as user_email
FROM object.project p
JOIN "user".base_user u ON u.id = p.id_base_user
ORDER BY p.created_at DESC;

-- Проекты конкретного клиента
SELECT 
    p.id,
    p.name,
    p.created_at,
    p.active_status
FROM object.project p
WHERE p.id_base_user = 1  -- ID клиента
ORDER BY p.created_at DESC;
```

### 📊 Статистика по клиентам и проектам

```sql
-- Количество проектов и звонков у каждого клиента
SELECT 
    u.id as user_id,
    u.name as user_name,
    u.email,
    COUNT(DISTINCT p.id) as projects_count,
    COUNT(DISTINCT iss.id) as total_calls,
    COUNT(DISTINCT iss.id) FILTER (WHERE iss.status_within_project = 'processed') as analyzed_calls
FROM "user".base_user u
LEFT JOIN object.project p ON p.id_base_user = u.id
LEFT JOIN object.item_set iss ON iss.id_project = p.id
WHERE u.is_active = true
GROUP BY u.id, u.name, u.email
ORDER BY total_calls DESC;
```

### 🔍 Найти проект по названию

```sql
-- Поиск проекта (нечёткий поиск)
SELECT 
    p.id,
    p.name,
    u.name as user_name,
    p.created_at
FROM object.project p
JOIN "user".base_user u ON u.id = p.id_base_user
WHERE p.name ILIKE '%продажи%'  -- Поиск по части названия
ORDER BY p.created_at DESC;
```

### 📋 Полная информация о проекте

```sql
-- Проект со всеми связанными данными
SELECT 
    p.id as project_id,
    p.name as project_name,
    p.active_status,
    p.created_at,
    u.name as user_name,
    u.email,
    ppo.output_data->>'report_url' as report_url,
    (SELECT COUNT(*) FROM object.item_set WHERE id_project = p.id) as total_calls,
    (SELECT COUNT(*) FROM object.item_set WHERE id_project = p.id AND status_within_project = 'processed') as analyzed_calls,
    (SELECT COUNT(*) FROM object.project_formula WHERE id_project = p.id) as formulas_count
FROM object.project p
JOIN "user".base_user u ON u.id = p.id_base_user
LEFT JOIN output.project_processing_output ppo ON ppo.id_project = p.id
WHERE p.id = 1;  -- ID проекта
```

---

### Получить все проанализированные звонки проекта

```sql
SELECT 
    iss.id,
    iss.name,
    iss.created_at,
    iss.status,
    iss.status_within_project
FROM object.item_set iss
WHERE iss.id_project = 1
  AND iss.status_within_project = 'processed'
ORDER BY iss.created_at DESC;
```

### Получить результаты анализа критериев для звонка

```sql
SELECT 
    piso.id,
    piso.id_item_set,
    piso.id_project,
    piso.created_at,
    piso.output
FROM output.project_item_set_processing_output piso
WHERE piso.id_item_set = 50
  AND piso.id_project = 1
ORDER BY piso.created_at DESC
LIMIT 1;
```

### Распарсить критерии из JSONB

```sql
SELECT 
    piso.id_item_set,
    criterion->>'criterion' as criterion_name,
    criterion->>'score' as score,
    criterion->>'reason' as reason,
    criterion->>'quote' as quote
FROM output.project_item_set_processing_output piso,
     jsonb_array_elements(piso.output) as block,
     jsonb_array_elements(block->'response') as response,
     jsonb_array_elements(
         (response->'message'->>'content')::jsonb
     ) as criterion
WHERE piso.id_item_set = 50
  AND piso.id_project = 1;
```

### Получить транскрипцию звонка

```sql
SELECT 
    iso.id,
    iso.id_item_set,
    iso.created_at,
    iso.output->>'output' as transcription_text,
    iso.output->>'google_doc' as google_doc_url,
    iso.output->'statistics' as statistics
FROM output.item_set_processing_output iso
WHERE iso.id_item_set = 50
ORDER BY iso.created_at DESC
LIMIT 1;
```

### Получить CRM данные звонка

```sql
SELECT 
    ism.id_item_set,
    ism.processing_parameters->'extra_processing_data'->'crm_data' as crm_data,
    ipm.processing_parameters->>'file_duration' as file_duration
FROM processing_metadata.item_set_processing_metadata ism
LEFT JOIN object.item i ON i.id_item_set = ism.id_item_set
LEFT JOIN processing_metadata.item_processing_metadata ipm ON ipm.id_item = i.id
WHERE ism.id_item_set = 50
LIMIT 1;
```

### Получить результаты формул

```sql
SELECT 
    fo.id,
    fo.id_item_set,
    fo.result,
    fo.error,
    pf.name as formula_name,
    pf.formula as formula_text,
    pf.is_default
FROM output.formula_output fo
JOIN object.project_formula pf ON pf.id = fo.id_formula
WHERE fo.id_item_set = 50;
```

### Статистика по проекту

```sql
SELECT 
    p.id,
    p.name,
    p.active_status,
    COUNT(DISTINCT iss.id) FILTER (WHERE iss.status_within_project = 'processed') as analyzed_calls,
    COUNT(DISTINCT iss.id) FILTER (WHERE iss.status_within_project = 'processing') as in_progress,
    COUNT(DISTINCT iss.id) FILTER (WHERE iss.status_within_project = 'processing_failed') as failed,
    SUM(
        CEIL((ipm.processing_parameters->>'file_duration')::float / 60)
    ) FILTER (WHERE iss.status_within_project = 'processed') as total_minutes
FROM object.project p
LEFT JOIN object.item_set iss ON iss.id_project = p.id
LEFT JOIN object.item i ON i.id_item_set = iss.id
LEFT JOIN processing_metadata.item_processing_metadata ipm ON ipm.id_item = i.id
WHERE p.id_base_user = 1
GROUP BY p.id, p.name, p.active_status;
```

### Звонки за период с критериями

```sql
WITH criteria_parsed AS (
    SELECT 
        piso.id_item_set,
        jsonb_array_elements(
            (jsonb_array_elements(piso.output)->'response'->0->'message'->>'content')::jsonb
        ) as criterion
    FROM output.project_item_set_processing_output piso
    WHERE piso.id_project = 1
)
SELECT 
    iss.id,
    iss.name,
    iss.created_at,
    AVG((cp.criterion->>'score')::int) FILTER (WHERE cp.criterion->>'score' ~ '^\d+$') as avg_score,
    COUNT(cp.criterion) as criteria_count
FROM object.item_set iss
LEFT JOIN criteria_parsed cp ON cp.id_item_set = iss.id
WHERE iss.id_project = 1
  AND iss.status_within_project = 'processed'
  AND iss.created_at >= '2025-01-01'
  AND iss.created_at < '2025-02-01'
GROUP BY iss.id, iss.name, iss.created_at
ORDER BY iss.created_at DESC;
```

---

## Диаграмма связей

```
user.base_user
    │
    ├──> object.project (id_base_user)
    │       │
    │       ├──> object.item_set (id_project)
    │       │       │
    │       │       ├──> object.item (id_item_set)
    │       │       │       │
    │       │       │       └──> output.item_processing_output (id_item)
    │       │       │       └──> processing_metadata.item_processing_metadata (id_item)
    │       │       │
    │       │       ├──> output.item_set_processing_output (id_item_set)
    │       │       ├──> output.project_item_set_processing_output (id_item_set, id_project)
    │       │       ├──> output.formula_output (id_item_set)
    │       │       │
    │       │       └──> processing_metadata.item_set_processing_metadata (id_item_set)
    │       │       └──> processing_metadata.project_item_set_processing_metadata (id_item_set, id_project)
    │       │
    │       ├──> object.project_formula (id_project)
    │       └──> output.project_processing_output (id_project)
    │
    └──> user.balance_replenishment (user_id)
```

---

## Python ORM модели

Если нужно использовать SQLAlchemy модели напрямую:

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Project(Base):
    __tablename__ = "project"
    __table_args__ = {"schema": "object"}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    created_at = Column(DateTime, nullable=False)
    id_base_user = Column(Integer, ForeignKey("user.base_user.id"))
    active_status = Column(String(250), default="active")
    
    item_sets = relationship("ItemSet", back_populates="project")

class ItemSet(Base):
    __tablename__ = "item_set"
    __table_args__ = {"schema": "object"}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    created_at = Column(DateTime, nullable=False)
    id_project = Column(Integer, ForeignKey("object.project.id"))
    status = Column(String(250), nullable=False)
    status_within_project = Column(String(250), nullable=False)
    
    project = relationship("Project", back_populates="item_sets")
    criteria_outputs = relationship("ProjectItemSetProcessingOutput", back_populates="item_set")

class ProjectItemSetProcessingOutput(Base):
    __tablename__ = "project_item_set_processing_output"
    __table_args__ = {"schema": "output"}
    
    id = Column(Integer, primary_key=True)
    id_item_set = Column(Integer, ForeignKey("object.item_set.id"))
    id_project = Column(Integer, ForeignKey("object.project.id"))
    output = Column(JSONB)
    created_at = Column(DateTime, nullable=False)
    
    item_set = relationship("ItemSet", back_populates="criteria_outputs")
```

---

## Безопасность

⚠️ **Важно:**
- Используйте read-only пользователя БД для аналитики
- Не модифицируйте данные напрямую — используйте API
- Храните credentials безопасно (не в коде)
- Ограничьте доступ по IP если возможно
