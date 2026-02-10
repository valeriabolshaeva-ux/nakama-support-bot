# Деплой Telegram Support Bot

## Требования

- Python 3.9+ (рекомендуется 3.11)
- Telegram Bot Token (от @BotFather)
- Telegram группа с включёнными Topics

## Подготовка Telegram

### 1. Создание бота

1. Откройте [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Сохраните **Bot Token**

### 2. Настройка группы поддержки

1. Создайте группу (или используйте существующую)
2. Включите Topics: Settings → Topics → Enable
3. Добавьте бота в группу как администратора
4. Дайте боту права:
   - Manage Topics
   - Post Messages
   - Edit Messages
   - Delete Messages
   - Pin Messages

### 3. Получение Chat ID группы

Отправьте сообщение в группу, затем откройте:
```
https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
```

Найдите `"chat": {"id": -100...}` — это ваш `SUPPORT_CHAT_ID`.

---

## Вариант 1: Docker (рекомендуется)

### Установка

```bash
# Клонировать репозиторий
git clone <repo-url> /opt/support-bot
cd /opt/support-bot

# Создать .env файл
cp backend/.env.example backend/.env
nano backend/.env  # заполнить переменные

# Запустить
docker-compose up -d

# Проверить логи
docker-compose logs -f
```

### Команды

```bash
# Остановить
docker-compose down

# Перезапустить
docker-compose restart

# Обновить
git pull
docker-compose build
docker-compose up -d

# Посмотреть логи
docker-compose logs -f bot
```

---

## Вариант 2: Systemd

### Установка

```bash
# Создать пользователя
sudo useradd -r -s /bin/false botuser

# Клонировать репозиторий
sudo git clone <repo-url> /opt/support-bot
sudo chown -R botuser:botuser /opt/support-bot

# Создать виртуальное окружение
cd /opt/support-bot/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Создать .env
cp .env.example .env
nano .env  # заполнить переменные

# Создать директорию для данных
mkdir -p data
chown botuser:botuser data

# Установить systemd сервис
sudo cp support-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable support-bot
sudo systemctl start support-bot
```

### Команды

```bash
# Статус
sudo systemctl status support-bot

# Логи
sudo journalctl -u support-bot -f

# Перезапуск
sudo systemctl restart support-bot

# Остановка
sudo systemctl stop support-bot
```

---

## Вариант 3: Локальный запуск

```bash
cd backend

# Создать виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Создать .env
cp .env.example .env
# Заполнить переменные

# Инициализировать тестовые данные (опционально)
python scripts/init_data.py

# Запустить бота
python -m app.main
```

---

## Конфигурация (.env)

```bash
# Обязательные
BOT_TOKEN=123456:ABC...         # Token от BotFather
SUPPORT_CHAT_ID=-100123456789   # ID группы поддержки

# Операторы (Telegram user IDs через запятую)
OPERATORS=123456,789012

# Опциональные
TIMEZONE=Europe/Madrid          # Часовой пояс (по умолчанию Europe/Madrid)
WORK_HOURS_START=10             # Начало рабочего дня (по умолчанию 10)
WORK_HOURS_END=19               # Конец рабочего дня (по умолчанию 19)
DB_PATH=data/support.db         # Путь к SQLite базе
LOG_LEVEL=INFO                  # Уровень логирования
```

---

## Инициализация данных

**При первом запуске** (например на Railway), если в базе нет ни одного проекта, бот автоматически создаёт клиента «Nakama» и проект с кодом **nakama**. Коллеги могут заходить по ссылке:

`https://t.me/<имя_вашего_бота>?start=nakama`

(подставьте имя бота из @BotFather). Код вводится без учёта регистра: подойдут `nakama`, `NAKAMA`, `Nakama`.

Для создания нескольких тестовых клиентов и проектов локально:

```bash
python scripts/init_data.py
```

Это создаст клиентов и проекты с кодами `DEMO001`, `DEMO002`, `TEST001`, `TEST002`, `ACME001`.

---

## Проверка работоспособности

1. Откройте бота в Telegram
2. Отправьте `/start nakama` или перейдите по ссылке `t.me/<бот>?start=nakama`
3. Должно появиться сообщение о привязке к проекту
4. Выберите категорию и создайте тестовый тикет
5. Проверьте, что в группе поддержки создался topic

---

## Бэкап

SQLite база хранится в `backend/data/support.db`.

```bash
# Создать бэкап
cp backend/data/support.db backend/data/support.db.backup

# Для Docker
docker cp support-bot:/app/data/support.db ./backup.db
```

---

## Обновление

### Docker

```bash
cd /opt/support-bot
git pull
docker-compose build
docker-compose up -d
```

### Systemd

```bash
cd /opt/support-bot
git pull
cd backend
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart support-bot
```

---

## Troubleshooting

### Бот не отвечает

1. Проверьте логи: `docker-compose logs -f` или `journalctl -u support-bot -f`
2. Убедитесь, что BOT_TOKEN корректный
3. Проверьте сетевое соединение

### Тикеты не создаются в группе

1. Проверьте SUPPORT_CHAT_ID (должен начинаться с -100)
2. Убедитесь, что бот — администратор группы
3. Проверьте, что Topics включены в группе

### Ошибки базы данных

1. Проверьте права на директорию `data/`
2. Убедитесь, что DB_PATH указан верно
3. При критических ошибках — удалите БД и перезапустите (данные будут потеряны)

---

## Мониторинг

Рекомендуется настроить мониторинг:

1. **Uptime**: Проверка, что бот отвечает на `/start`
2. **Логи**: Отслеживание ERROR уровня
3. **Алерты**: Telegram/Email при падении

Пример с uptimerobot.com:
- Тип: Keyword
- URL: `https://api.telegram.org/bot<TOKEN>/getMe`
- Keyword: `"ok":true`
