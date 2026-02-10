# Техническое описание: Telegram Support Bot

## Обзор

Telegram Support Bot — бот для поддержки клиентов, написанный на Python с использованием aiogram 3.x.

### Ключевые особенности:
- Async/await архитектура
- SQLite для хранения данных
- FSM для управления состояниями диалога
- Pydantic для валидации конфигурации
- Topic-based маршрутизация в Support Group

---

## Технологический стек

| Компонент | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| Runtime | Python | 3.11+ | Основной язык |
| Bot Framework | aiogram | 3.x | Telegram Bot API |
| ORM | SQLAlchemy | 2.0+ | Работа с БД |
| Database | SQLite | 3 | Хранение данных |
| Config | Pydantic | 2.x | Валидация настроек |
| Testing | pytest | 8.x | Тестирование |
| Async | asyncio | stdlib | Асинхронность |

---

## Структура проекта

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Entry point, bot startup
│   │
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers/              # Message & callback handlers
│   │   │   ├── __init__.py
│   │   │   ├── start.py           # /start, invite-code flow
│   │   │   ├── ticket.py          # Ticket creation FSM
│   │   │   ├── client_message.py  # Messages from clients
│   │   │   ├── operator.py        # Operator actions in group
│   │   │   └── common.py          # /help, /project, errors
│   │   │
│   │   ├── keyboards/             # Inline keyboards builders
│   │   │   ├── __init__.py
│   │   │   ├── categories.py      # Category selection
│   │   │   ├── ticket.py          # Ticket actions (skip, confirm)
│   │   │   ├── operator.py        # Operator buttons
│   │   │   ├── triage.py          # Triage flow buttons
│   │   │   └── csat.py            # Feedback buttons
│   │   │
│   │   ├── states/                # FSM state groups
│   │   │   ├── __init__.py
│   │   │   ├── ticket.py          # TicketCreation states
│   │   │   └── triage.py          # Triage states
│   │   │
│   │   ├── middlewares/           # Request middlewares
│   │   │   ├── __init__.py
│   │   │   ├── database.py        # Inject DB session
│   │   │   └── logging.py         # Request logging
│   │   │
│   │   └── filters/               # Custom message filters
│   │       ├── __init__.py
│   │       ├── operator.py        # IsOperator filter
│   │       └── group.py           # IsSupportGroup filter
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py          # Engine, session factory
│   │   ├── models.py              # SQLAlchemy models
│   │   └── operations.py          # CRUD functions
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ticket.py              # Ticket business logic
│   │   ├── user.py                # User binding logic
│   │   └── notification.py        # Group notifications
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py            # Pydantic Settings
│   │   ├── texts.py               # Bot message templates
│   │   └── categories.py          # Ticket categories
│   │
│   └── utils/
│       ├── __init__.py
│       ├── timezone.py            # Working hours utils
│       └── formatting.py          # Message formatting
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Fixtures
│   ├── unit/
│   │   ├── test_ticket_service.py
│   │   └── test_user_service.py
│   └── integration/
│       └── test_handlers.py
│
├── data/                          # SQLite DB (gitignored)
│   └── support.sqlite
│
├── requirements.txt
├── .env
└── .env.example
```

---

## Конфигурация (Pydantic Settings)

```python
# app/config/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Telegram
    bot_token: str = Field(..., description="Telegram Bot Token")
    support_chat_id: int = Field(..., description="Support Group ID")
    operators: list[int] = Field(default_factory=list, description="Operator user IDs")
    
    # Application
    timezone: str = Field(default="Europe/Madrid")
    db_path: str = Field(default="./data/support.sqlite")
    log_level: str = Field(default="info")
    
    # Working Hours
    work_hours_start: int = Field(default=10)
    work_hours_end: int = Field(default=19)
    work_days: list[int] = Field(default=[1, 2, 3, 4, 5])  # Mon-Fri
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

settings = Settings()
```

---

## База данных (SQLite + SQLAlchemy 2.0)

### Connection

```python
# app/database/connection.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.db_path}",
    echo=settings.log_level == "debug"
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
```

### Models (основные)

```python
# app/database/models.py
from sqlalchemy import String, Integer, BigInteger, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Client(Base):
    __tablename__ = "clients"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    projects: Mapped[list["Project"]] = relationship(back_populates="client")

class Ticket(Base):
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    tg_user_id: Mapped[int] = mapped_column(BigInteger)
    category: Mapped[str] = mapped_column(String(50))
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    status: Mapped[str] = mapped_column(String(20), default="new")
    support_chat_id: Mapped[int] = mapped_column(BigInteger)
    topic_id: Mapped[int] = mapped_column(Integer, nullable=True)
    assigned_to_tg_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

---

## Bot Handlers

### Router Structure

```python
# app/main.py
from aiogram import Bot, Dispatcher
from app.bot.handlers import start, ticket, operator, common, client_message

dp = Dispatcher()

# Private chat handlers
dp.include_router(start.router)
dp.include_router(ticket.router)
dp.include_router(common.router)
dp.include_router(client_message.router)

# Group handlers
dp.include_router(operator.router)
```

### Example Handler

```python
# app/bot/handlers/start.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from app.config.texts import Texts
from app.config.settings import settings
from app.database.operations import get_user_binding, create_user_binding
from app.bot.keyboards.categories import get_categories_keyboard
from app.bot.keyboards.triage import get_triage_keyboard

router = Router(name="start")

@router.message(CommandStart(deep_link=True))
async def handle_start_with_code(message: Message, command: CommandStart) -> None:
    """Handle /start with invite code deep link."""
    code = command.args
    project = await get_project_by_invite_code(code)
    
    if project:
        await create_user_binding(
            tg_user_id=message.from_user.id,
            tg_username=message.from_user.username,
            tg_name=message.from_user.full_name,
            project_id=project.id
        )
        await message.answer(
            Texts.WELCOME,
            reply_markup=get_categories_keyboard()
        )
    else:
        await message.answer(
            Texts.INVALID_CODE,
            reply_markup=get_triage_keyboard()
        )

@router.message(CommandStart())
async def handle_start_no_code(message: Message) -> None:
    """Handle /start without invite code."""
    binding = await get_user_binding(message.from_user.id)
    
    if binding:
        await message.answer(
            Texts.WELCOME_BACK,
            reply_markup=get_categories_keyboard()
        )
    else:
        await message.answer(
            Texts.NO_CODE_PROMPT,
            reply_markup=get_triage_keyboard()
        )
```

---

## FSM States

```python
# app/bot/states/ticket.py
from aiogram.fsm.state import State, StatesGroup

class TicketCreation(StatesGroup):
    """States for ticket creation flow."""
    waiting_category = State()      # User selecting category
    waiting_description = State()    # User typing description
    waiting_attachments = State()    # User attaching files
    waiting_urgency = State()        # For "Urgent" category only
    
class TriageFlow(StatesGroup):
    """States for unknown user triage."""
    waiting_company = State()        # User typing company name
    waiting_contact = State()        # User typing contact info
```

---

## Keyboards

```python
# app/bot/keyboards/categories.py
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.config.categories import CATEGORIES

def get_categories_keyboard() -> InlineKeyboardMarkup:
    """Build category selection inline keyboard."""
    builder = InlineKeyboardBuilder()
    
    for cat in CATEGORIES:
        builder.button(
            text=cat["emoji"] + " " + cat["label"],
            callback_data=f"category:{cat['id']}"
        )
    
    builder.adjust(1)  # One button per row
    return builder.as_markup()
```

---

## Services

```python
# app/services/ticket.py
from datetime import datetime
from app.database.operations import create_ticket, get_next_ticket_number
from app.services.notification import send_ticket_to_group

async def create_new_ticket(
    tg_user_id: int,
    project_id: int,
    category: str,
    description: str,
    priority: str = "normal"
) -> Ticket:
    """
    Create new support ticket.
    
    1. Generate ticket number
    2. Save to database
    3. Create topic in Support Group
    4. Send ticket card to topic
    """
    number = await get_next_ticket_number()
    
    ticket = await create_ticket(
        number=number,
        project_id=project_id,
        tg_user_id=tg_user_id,
        category=category,
        priority=priority,
        status="new"
    )
    
    topic_id = await send_ticket_to_group(ticket, description)
    
    await update_ticket(ticket.id, topic_id=topic_id)
    
    return ticket
```

---

## Entry Point

```python
# app/main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.config.settings import settings
from app.database.connection import init_db
from app.bot.handlers import start, ticket, operator, common, client_message
from app.bot.middlewares.database import DatabaseMiddleware

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)

async def main():
    # Initialize database
    await init_db()
    
    # Create bot instance
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Create dispatcher
    dp = Dispatcher()
    
    # Setup middlewares
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    
    # Include routers
    dp.include_router(start.router)
    dp.include_router(ticket.router)
    dp.include_router(common.router)
    dp.include_router(client_message.router)
    dp.include_router(operator.router)
    
    # Start polling
    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Тестирование

### Fixtures

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

@pytest.fixture
async def db_session():
    """Create in-memory SQLite for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session = async_sessionmaker(engine)()
    yield session
    await session.close()
```

### Example Test

```python
# tests/unit/test_ticket_service.py
import pytest
from app.services.ticket import create_new_ticket

@pytest.mark.asyncio
async def test_create_ticket(db_session):
    """Test ticket creation with all required fields."""
    ticket = await create_new_ticket(
        tg_user_id=123456,
        project_id=1,
        category="bug",
        description="Test description"
    )
    
    assert ticket.number == 1
    assert ticket.status == "new"
    assert ticket.priority == "normal"
```

---

## Запуск

```bash
# Development
cd backend
source .venv/bin/activate
python -m app.main

# With logging
LOG_LEVEL=debug python -m app.main

# Tests
pytest -v --tb=short
```

---

*Актуально для: 2026-02-05*
