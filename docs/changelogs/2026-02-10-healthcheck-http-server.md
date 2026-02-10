# Changelog: HTTP healthcheck для деплоя (Railway)

**Дата:** 2026-02-10

## Проблема

При деплое на Railway (и подобных платформах) healthcheck идёт по HTTP на путь `/`. Бот — только long polling, HTTP-сервера не было, поэтому все попытки проверки возвращали "service unavailable" и деплой падал с "1/1 replicas never became healthy".

## Что сделано

1. **Настройка**  
   В `app/config/settings.py` добавлено опциональное поле `healthcheck_port` (читается из переменной окружения `PORT`). На Railway `PORT` задаётся автоматически.

2. **Модуль health**  
   Добавлен `app/health.py`: минимальный asyncio TCP-сервер без внешних зависимостей. На запрос `GET /` отвечает `200 OK`, на остальные пути — `404`.

3. **Запуск в main**  
   В `app/main.py`: если задан `healthcheck_port` (т.е. задан `PORT`), при старте бота поднимается HTTP-сервер на `0.0.0.0:PORT`. Сервер работает вместе с polling и закрывается при остановке бота.

4. **Документация**  
   В `backend/.env.example` добавлен комментарий про `PORT`.

## Изменённые/новые файлы

- `backend/app/config/settings.py` — поле `healthcheck_port` (alias `PORT`)
- `backend/app/health.py` — новый модуль
- `backend/app/main.py` — запуск/остановка health-сервера
- `backend/.env.example` — комментарий про PORT
- `docs/changelogs/2026-02-10-healthcheck-http-server.md` — этот changelog

## Как проверить

- **Локально:** без `PORT` в `.env` бот работает как раньше, HTTP-сервер не стартует.
- **На Railway:** переменная `PORT` задаётся платформой, при деплое поднимается HTTP-сервер, healthcheck по `/` получает 200, реплика переходит в healthy.

## Ограничения

- Healthcheck только проверяет, что процесс слушает порт и отвечает HTTP 200. Проверки БД или Telegram API в healthcheck не делаются.
