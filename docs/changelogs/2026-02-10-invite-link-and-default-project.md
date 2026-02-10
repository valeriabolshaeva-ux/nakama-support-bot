# Changelog: Ссылка для коллег и проект по умолчанию

**Дата:** 2026-02-10

## Проблема

Коллеги заходили по ссылке или вводили код «1» — бот отвечал «Код не найден», так как в базе на Railway не было ни одного проекта (и кода «1» в том числе).

## Что сделано

1. **Поиск по invite-коду**
   - В `get_project_by_invite_code` код обрезается от пробелов и сравнивается без учёта регистра (nakama = NAKAMA = Nakama).

2. **Проект по умолчанию при первом запуске**
   - Добавлена функция `ensure_default_project` в `app/database/operations.py`.
   - При старте бота, если в базе нет ни одного проекта, создаются клиент «Nakama» и проект с invite-кодом **nakama**.
   - Вызов из `on_startup` в `app/main.py` после `init_db()`.

3. **Документация**
   - В `docs/deployment.md` добавлена ссылка для коллег: `t.me/<бот>?start=nakama` и пояснение про регистр.

## Изменённые файлы

- `backend/app/database/operations.py` — нормализация кода, `ensure_default_project`
- `backend/app/main.py` — вызов `ensure_default_project` при старте
- `docs/deployment.md` — раздел про ссылку и первый запуск
- `docs/changelogs/2026-02-10-invite-link-and-default-project.md`

## Как пользоваться

Ссылка для коллег (подставить имя бота):  
**https://t.me/Nakama_support_bot?start=nakama**

После деплоя с этим коммитом при пустой базе проект «nakama» создаётся автоматически.
