# Промпты для AI агентов

## Общие правила

Перед выполнением любой задачи агент ОБЯЗАН:

1. Прочитать `docs/project-plan.md` — понять общий план
2. Прочитать `docs/technical-summary.md` — понять архитектуру
3. Прочитать `.cursorrules` — запомнить правила кодирования
4. Осознать своё место и задачу в контексте всего проекта
5. **Только после этого приступать к выполнению!**

---

## Фаза 1: MVP

### Wave 1 — База данных и модели

#### Agent 1.1 — Database Models

```markdown
## Agent 1.1 — Создание моделей базы данных

### Контекст
Ты — AI-агент в Cursor IDE. Твоя задача: создать SQLAlchemy модели для основных сущностей системы.

### ⚠️ ОБЯЗАТЕЛЬНО СНАЧАЛА
**Прежде чем писать код — изучи проект:**
1. Прочитай `docs/project-plan.md` — пойми общий план
2. Прочитай `docs/technical-summary.md` — пойми архитектуру
3. Прочитай `.cursorrules` — запомни правила кодирования

### Твоя зона ответственности
- `backend/app/models/` — создать модели
- `backend/tests/unit/models/` — написать тесты

### НЕ ТРОГАЙ
- `backend/app/api/` — это зона другого агента
- `frontend/` — это зона frontend агентов

### Задачи
1. [ ] Создать базовый класс модели в `models/base.py`
2. [ ] Создать модель User в `models/user.py`
3. [ ] Создать миграцию через Alembic
4. [ ] Написать unit тесты для моделей
5. [ ] Создать changelog в `docs/changelogs/wave-1-agent-1.md`

### Definition of Done
- [ ] Все модели имеют docstrings
- [ ] Все поля имеют type hints
- [ ] Тесты проходят
- [ ] Миграция применяется успешно
```

---

### Wave 2 — API и сервисы

#### Agent 2.1 — Auth Service

```markdown
## Agent 2.1 — Сервис аутентификации

### Контекст
Ты — AI-агент. Твоя задача: реализовать JWT аутентификацию.

### Твоя зона ответственности
- `backend/app/api/v1/auth.py` — эндпоинты
- `backend/app/services/auth.py` — бизнес-логика
- `backend/app/schemas/auth.py` — Pydantic схемы
- `backend/tests/unit/services/test_auth.py` — тесты

### Задачи
1. [ ] Создать схемы: LoginRequest, TokenResponse, UserCreate
2. [ ] Создать AuthService с методами: register, login, refresh
3. [ ] Создать эндпоинты: POST /login, POST /register, POST /refresh
4. [ ] Написать тесты (минимум 5 на эндпоинт)
5. [ ] Создать changelog
```

---

## Фаза 2: Интеграции

### Wave 3 — Внешние сервисы

#### Agent 3.1 — OpenAI Integration

```markdown
## Agent 3.1 — Интеграция с OpenAI

### Контекст
Ты — AI-агент. Твоя задача: создать сервис для работы с OpenAI API.

### Твоя зона ответственности
- `backend/app/services/openai_service.py`
- `backend/tests/unit/services/test_openai.py`

### Задачи
1. [ ] Создать OpenAIService с методами: chat_completion, embeddings
2. [ ] Реализовать retry логику с exponential backoff
3. [ ] Обработать rate limits и ошибки API
4. [ ] Написать тесты с моками
5. [ ] Создать changelog
```

---

## Шаблон changelog

```markdown
# Changelog: Wave X, Agent Y

## Задача
[Краткое описание]

## Что сделано
- Создал `app/module/file.py`
- Добавил тесты в `tests/unit/`
- Обновил `requirements.txt` (если нужно)

## Как проверить
\`\`\`bash
pytest tests/unit/module/ -v
\`\`\`

## Известные ограничения
- [Если есть]
```

---

*Обновляйте этот файл по мере добавления новых волн агентов.*
