# Техническое описание: Customer Support

## 1. Архитектура

См. [docs/architecture.md](architecture.md) для диаграмм.

### Стек технологий

#### Backend
| Компонент | Технология | Версия |
|-----------|------------|--------|
| Framework | FastAPI | 0.109+ |
| Python | Python | 3.11+ |
| Database | PostgreSQL | 16+ |
| ORM | SQLAlchemy | 2.0+ |
| Cache/Queue | Redis | 7+ |
| Background Tasks | Celery | 5.3+ |
| Validation | Pydantic | 2.5+ |

#### Frontend
| Компонент | Технология | Версия |
|-----------|------------|--------|
| Library | React | 18+ |
| Language | TypeScript | 5.6+ |
| Bundler | Vite | 6.0+ |
| Styling | Tailwind CSS | 3.4+ |
| UI Components | shadcn/ui | latest |
| Routing | React Router | 6+ |
| State | TanStack Query | 5+ |

---

## 2. Структура проекта

### Backend (`backend/`)

```
backend/
├── app/
│   ├── __init__.py           # Версия пакета
│   ├── main.py               # FastAPI entry point
│   ├── settings.py           # Pydantic Settings
│   ├── api/                  # API endpoints
│   │   ├── __init__.py
│   │   └── v1/               # API version 1
│   ├── models/               # SQLAlchemy models
│   ├── services/             # Business logic
│   ├── schemas/              # Pydantic schemas
│   └── utils/                # Helpers
├── tests/
│   ├── conftest.py           # Pytest fixtures
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── alembic/                  # Database migrations
├── requirements.txt
├── .env                      # Environment (не коммитим!)
└── .env.example              # Example environment
```

### Frontend (`frontend/`)

```
frontend/src/
├── app/                      # App initialization
│   ├── providers/            # Context providers
│   │   └── ThemeProvider.tsx # Theme management
│   └── styles/
│       └── globals.css       # Tailwind + CSS variables
├── components/
│   └── ui/                   # shadcn/ui components
│       ├── button.tsx
│       ├── card.tsx
│       └── input.tsx
├── entities/                 # Business entities
├── features/                 # User scenarios
├── lib/
│   └── utils.ts              # cn() utility
├── pages/
│   └── HomePage.tsx          # Home page
├── shared/
│   ├── components/           # Shared components
│   │   └── ThemeToggle.tsx
│   └── hooks/                # Custom hooks
├── widgets/                  # Widget components
├── App.tsx                   # Root component
└── main.tsx                  # Entry point
```

---

## 3. Конфигурация

### Environment Variables

Все переменные определены в `backend/.env.example` и `frontend/.env.example`.

**Backend (Pydantic Settings):**

```python
from app.settings import settings

# Database
db_url = settings.db.url

# OpenAI
api_key = settings.openai.api_key

# Environment
is_debug = settings.debug
env = settings.environment
```

**Frontend (Vite):**

```typescript
// Access env variables
const apiUrl = import.meta.env.VITE_API_BASE_URL
```

---

## 4. API Endpoints

### Health Check
```
GET /health
```
Возвращает статус приложения.

### Root
```
GET /
```
Возвращает приветственное сообщение.

### API Docs (только в debug режиме)
```
GET /docs      — Swagger UI
GET /redoc     — ReDoc
```

---

## 5. База данных

### Подключение

```python
# Async
DATABASE_URL = "postgresql+asyncpg://user:pass@host:port/db"

# Sync (для Alembic)
DATABASE_URL = "postgresql://user:pass@host:port/db"
```

### Миграции (Alembic)

```bash
# Создать миграцию
alembic revision --autogenerate -m "add users table"

# Применить миграции
alembic upgrade head

# Откатить последнюю
alembic downgrade -1
```

---

## 6. Тестирование

### Backend

```bash
# Все тесты
pytest -v

# Только unit
pytest -v -m unit

# С покрытием
pytest --cov=app --cov-report=html
```

### Frontend

```bash
# Все тесты
npm run test

# С покрытием
npm run test:coverage
```

---

## 7. Docker

### Development

```bash
docker-compose -f docker-compose-dev.yml up -d
```

**Сервисы:**
- `app` — FastAPI (port 8000)
- `db` — PostgreSQL (port 5432)
- `redis` — Redis (port 6379)
- `celery` — Celery worker
- `celery-beat` — Celery scheduler

### Production

```bash
docker-compose up -d --build
```

---

## 8. Внешние интеграции

### OpenAI

```python
from app.settings import settings
import openai

openai.api_key = settings.openai.api_key
```

### Supabase

```python
from app.settings import settings
from supabase import create_client

supabase = create_client(
    settings.supabase.url,
    settings.supabase.secret_key
)
```

---

## 9. Мониторинг

### Health Check
```
GET /health
```

### Logs
- Structured logging via `structlog`
- JSON format for production
- Console format for development

---

*Последнее обновление: 2026-02-05*
