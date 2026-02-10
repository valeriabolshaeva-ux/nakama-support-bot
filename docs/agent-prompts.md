# Промпты для AI-агентов

## Общие правила

1. **ПЕРЕД НАЧАЛОМ РАБОТЫ** изучи:
   - `docs/product-requirements.md` — полное ТЗ
   - `docs/database-schema.md` — схема БД
   - `docs/bot-flows.md` — user flows
   - `docs/message-templates.md` — тексты сообщений

2. **Язык:**
   - Код, комментарии — английский
   - Документация, changelog — русский
   - Тексты бота для клиентов — русский

3. **После выполнения** создай changelog в `docs/changelogs/`

---

## Фаза 1: Базовая инфраструктура

### 1.1 Database Models

**Задача:** Создать SQLAlchemy модели для SQLite

**Файлы:**
- `backend/app/database/models.py`
- `backend/app/database/connection.py`

**Требования:**
```
1. Изучи docs/database-schema.md
2. Создай Base class
3. Создай модели: Client, Project, UserBinding, Ticket, Message, Feedback
4. Все поля с type hints
5. Relationships между моделями
6. Индексы согласно схеме
```

**Пример:**
```python
class Ticket(Base):
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True)
    # ... остальные поля
```

---

### 1.2 Database Operations

**Задача:** Создать CRUD функции

**Файл:** `backend/app/database/operations.py`

**Требования:**
```
1. Async функции
2. Принимают AsyncSession
3. Type hints везде
4. Docstrings с описанием

Функции:
- get_project_by_invite_code(code: str) -> Project | None
- get_user_binding(tg_user_id: int) -> UserBinding | None
- create_user_binding(...) -> UserBinding
- get_active_ticket(tg_user_id: int) -> Ticket | None
- create_ticket(...) -> Ticket
- update_ticket_status(...) -> None
- save_message(...) -> Message
- save_feedback(...) -> Feedback
```

---

### 1.3 Pydantic Settings

**Задача:** Создать конфигурацию

**Файл:** `backend/app/config/settings.py`

**Требования:**
```
1. Наследоваться от BaseSettings
2. Поля:
   - bot_token: str
   - support_chat_id: int
   - operators: list[int]
   - timezone: str = "Europe/Madrid"
   - db_path: str = "./data/support.sqlite"
   - log_level: str = "info"
   - work_hours_start: int = 10
   - work_hours_end: int = 19
   - work_days: list[int] = [1,2,3,4,5]
3. Загрузка из .env
```

---

### 1.4 Message Texts

**Задача:** Создать тексты бота

**Файл:** `backend/app/config/texts.py`

**Требования:**
```
1. Изучи docs/message-templates.md
2. Создай dataclass Texts со всеми текстами
3. Методы для текстов с плейсхолдерами
```

---

## Фаза 2: Handlers

### 2.1 Start Handler

**Задача:** Обработка /start с invite-code

**Файл:** `backend/app/bot/handlers/start.py`

**Требования:**
```
1. Изучи docs/bot-flows.md раздел "Идентификация"
2. Router с именем "start"
3. Handlers:
   - /start с deep_link (invite code)
   - /start без кода
4. Логика:
   - Проверить код в БД
   - Создать user_binding
   - Показать меню категорий или triage
```

---

### 2.2 Ticket Creation

**Задача:** FSM для создания тикета

**Файлы:**
- `backend/app/bot/states/ticket.py`
- `backend/app/bot/handlers/ticket.py`
- `backend/app/bot/keyboards/categories.py`

**Требования:**
```
1. Изучи docs/bot-flows.md раздел "Создание тикета"
2. States: waiting_category, waiting_description, waiting_attachments
3. Для "Срочно": доп. states waiting_urgency_level, waiting_urgency_details
4. Сохранять данные в state.data
5. После завершения:
   - Создать topic в группе
   - Отправить карточку тикета
   - Переслать описание и вложения
   - Отправить подтверждение клиенту
```

---

### 2.3 Operator Handler

**Задача:** Обработка действий операторов

**Файл:** `backend/app/bot/handlers/operator.py`

**Требования:**
```
1. Изучи docs/bot-flows.md раздел "Работа оператора"
2. Filter: IsOperator (проверка user_id в OPERATORS)
3. Filter: IsSupportGroup (проверка chat_id)
4. Callbacks:
   - take_ticket:{id} → статус in_progress
   - close_ticket:{id} → статус closed + CSAT
   - request_details:{id} → шаблон клиенту
5. Пересылка сообщений операторов клиенту
```

---

### 2.4 CSAT Handler

**Задача:** Сбор обратной связи

**Файл:** `backend/app/bot/handlers/csat.py`

**Требования:**
```
1. Изучи docs/bot-flows.md раздел "CSAT"
2. Callbacks:
   - csat_positive:{ticket_id}
   - csat_negative:{ticket_id}
3. При negative: запросить комментарий
4. Сохранить в БД
5. Отправить в topic тикета
```

---

## Фаза 3: Services

### 3.1 Ticket Service

**Задача:** Бизнес-логика тикетов

**Файл:** `backend/app/services/ticket.py`

**Требования:**
```
Функции:
- create_ticket(user_id, project_id, category, description, attachments)
- close_ticket(ticket_id, operator_id)
- reopen_ticket(ticket_id)
- get_or_create_active_ticket(user_id)
- check_recent_closed(user_id) -> Ticket | None (< 48h)
```

---

### 3.2 Notification Service

**Задача:** Отправка в Support Group

**Файл:** `backend/app/services/notification.py`

**Требования:**
```
Функции:
- create_topic(bot, ticket) -> topic_id
- send_ticket_card(bot, ticket, topic_id)
- forward_to_topic(bot, ticket, message)
- update_ticket_card(bot, ticket)
- send_feedback_to_topic(bot, ticket, feedback)
```

---

## Шаблон Changelog

```markdown
# Changelog: [Дата] — [Название]

## Что сделано
- Создан файл X
- Добавлена функция Y
- Исправлен баг Z

## Изменённые файлы
- `backend/app/...`

## Как проверить
1. Запустить бота
2. Отправить /start
3. Ожидаемый результат: ...

## Известные ограничения
- Не реализовано: ...
- Требует доработки: ...
```

---

*Актуально для: 2026-02-05*
