# 🚀 Customer Support — Универсальный проект

> Универсальный шаблон полноценного full-stack приложения с бэкендом (FastAPI) и фронтендом (React + shadcn/ui).

---

## 📋 Содержание

- [Быстрый старт](#-быстрый-старт)
- [Структура проекта](#-структура-проекта)
- [Технологический стек](#-технологический-стек)
- [Разработка](#-разработка)
- [Docker](#-docker)
- [Тестирование](#-тестирование)
- [Документация](#-документация)

---

## 🚀 Быстрый старт

### Требования

- **Python** 3.11+
- **Node.js** 18+
- **Docker** и **Docker Compose** (опционально)
- **PostgreSQL** 16+ (или через Docker)
- **Redis** 7+ (опционально, для Celery)

### Установка

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd CustomerSupport

# 2. Настроить переменные окружения
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Отредактировать .env файлы с вашими данными

# 3. Установить зависимости бэкенда
cd backend
python -m venv .venv
source .venv/bin/activate  # или .venv\Scripts\activate на Windows
pip install -r requirements.txt

# 4. Установить зависимости фронтенда
cd ../frontend
npm install

# 5. Запустить приложение
# Backend (в одном терминале)
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend (в другом терминале)
cd frontend && npm run dev
```

### Docker (рекомендуется)

```bash
# Запуск в режиме разработки
docker-compose -f docker-compose-dev.yml up -d

# Логи
docker-compose -f docker-compose-dev.yml logs -f

# Остановка
docker-compose -f docker-compose-dev.yml down
```

---

## 📁 Структура проекта

```
CustomerSupport/
├── .cursorrules              # Правила для Cursor AI
├── .cursor/rules/            # Детальные правила для агентов
│   ├── backend.mdc
│   └── frontend.mdc
├── .gitignore
├── .flake8
├── README.md
├── docker-compose.yml        # Production
├── docker-compose-dev.yml    # Development
├── Dockerfile
│
├── backend/                  # 🐍 Python/FastAPI
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # Business logic
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── utils/            # Helpers
│   │   ├── main.py           # Entry point
│   │   └── settings.py       # Configuration
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
│
├── frontend/                 # ⚛️ React/TypeScript
│   ├── src/
│   │   ├── app/              # App initialization
│   │   ├── components/ui/    # shadcn/ui components
│   │   ├── entities/         # Business entities
│   │   ├── features/         # User scenarios
│   │   ├── lib/              # Utilities
│   │   ├── pages/            # Pages
│   │   ├── shared/           # Shared components
│   │   └── widgets/          # Widgets
│   ├── package.json
│   ├── vite.config.ts
│   ├── .env
│   └── .env.example
│
├── docs/                     # 📚 Документация
│   ├── project-plan.md
│   ├── technical-summary.md
│   ├── architecture.md
│   ├── agent-prompts.md
│   ├── changelogs/
│   └── production/
│
├── scripts/                  # 🛠️ Вспомогательные скрипты
└── temporary/                # 📝 Временные файлы (не коммитим)
```

---

## 🛠️ Технологический стек

### Backend
| Технология | Назначение |
|------------|------------|
| **FastAPI** | REST API фреймворк |
| **PostgreSQL** | Основная база данных |
| **SQLAlchemy** | ORM |
| **Pydantic** | Валидация и сериализация |
| **Celery + Redis** | Фоновые задачи |
| **pytest** | Тестирование |

### Frontend
| Технология | Назначение |
|------------|------------|
| **React 18** | UI библиотека |
| **TypeScript** | Типизация |
| **Vite** | Сборщик |
| **Tailwind CSS** | Стилизация |
| **shadcn/ui** | UI компоненты |
| **React Router** | Роутинг |
| **TanStack Query** | Управление состоянием |

---

## 💻 Разработка

### Backend

```bash
cd backend

# Активировать виртуальное окружение
source .venv/bin/activate

# Запуск с hot-reload
uvicorn app.main:app --reload --port 8000

# Swagger UI
open http://localhost:8000/docs
```

### Frontend

```bash
cd frontend

# Запуск dev server
npm run dev

# Добавление shadcn компонента
npx shadcn add button input card

# Сборка
npm run build
```

---

## 🐳 Docker

### Development

```bash
# Запуск всех сервисов
docker-compose -f docker-compose-dev.yml up -d

# Отдельные сервисы
docker-compose -f docker-compose-dev.yml up -d db redis

# Просмотр логов
docker-compose -f docker-compose-dev.yml logs -f app
```

### Production

```bash
# Сборка и запуск
docker-compose up -d --build

# Проверка статуса
docker-compose ps
```

---

## 🧪 Тестирование

### Backend

```bash
cd backend

# Все тесты
pytest -v

# Только unit тесты
pytest -v -m unit

# С покрытием
pytest --cov=app --cov-report=html
```

### Frontend

```bash
cd frontend

# Все тесты
npm run test

# С покрытием
npm run test:coverage
```

---

## 📖 Документация

| Документ | Описание |
|----------|----------|
| [docs/project-plan.md](docs/project-plan.md) | План проекта по фазам |
| [docs/technical-summary.md](docs/technical-summary.md) | Техническое описание |
| [docs/architecture.md](docs/architecture.md) | Архитектурные диаграммы |
| [docs/agent-prompts.md](docs/agent-prompts.md) | Промпты для AI агентов |

---

## 🔐 Переменные окружения

См. файлы `.env.example` в директориях `backend/` и `frontend/`.

**Важно:**
- Файл `.env` никогда не коммитится в репозиторий
- Только `.env.example` с плейсхолдерами

---

## 📝 Лицензия

MIT

---

*Создано с использованием Cursor IDE и AI-агентов*
