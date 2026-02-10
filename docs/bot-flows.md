# User Flows: Telegram Support Bot

## 1. Идентификация (invite-code)

### 1.1 /start с валидным кодом

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    participant D as БД
    
    C->>B: /start CODE123
    B->>D: SELECT * FROM projects WHERE invite_code = 'CODE123'
    D-->>B: Project found
    B->>D: INSERT INTO user_bindings (tg_user_id, project_id)
    B->>C: "Привет! Я бот поддержки..."
    B->>C: [Меню категорий]
```

**Текст бота:**
> Привет! Я бот поддержки. Я аккуратно соберу детали и передам задачу команде — ничего не потеряется.
>
> Выберите, что случилось:

---

### 1.2 /start без кода (новый пользователь)

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    participant D as БД
    
    C->>B: /start
    B->>D: SELECT * FROM user_bindings WHERE tg_user_id = X
    D-->>B: Not found
    B->>C: "Нужен код проекта..."
    B->>C: [Ввести код] [Нет кода]
```

**Текст бота:**
> Привет! Чтобы я направил запрос правильно, нужен код проекта.
>
> Если кода нет — нажмите «Нет кода», мы разберёмся.

---

### 1.3 /start без кода (известный пользователь)

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    participant D as БД
    
    C->>B: /start
    B->>D: SELECT * FROM user_bindings WHERE tg_user_id = X
    D-->>B: Binding found (project_id = 1)
    B->>C: "С возвращением!"
    B->>C: [Меню категорий]
```

**Текст бота:**
> С возвращением! Выберите, что случилось:

---

### 1.4 /start с predefined username

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    participant D as БД
    
    C->>B: /start (без кода)
    B->>D: SELECT * FROM user_bindings WHERE tg_user_id = X
    D-->>B: Not found
    B->>D: SELECT * FROM predefined_users WHERE tg_username = '@user'
    D-->>B: Found (client_id = 1)
    B->>D: SELECT project FROM projects WHERE client_id = 1 LIMIT 1
    D-->>B: Project found
    B->>D: INSERT INTO user_bindings
    B->>C: "Добро пожаловать! Проект: Project Name"
    B->>C: [Меню категорий]
```

**Как это работает:**
1. Администратор заранее добавляет usernames пользователей в таблицу `predefined_users`
2. При `/start` бот проверяет username пользователя в этой таблице
3. Если найден — автоматически привязывает к первому проекту клиента

**Добавление пользователей:**
```bash
cd backend
python ../scripts/init_data.py add-user vbolshaeva "Demo Company"
python ../scripts/init_data.py list-users
```

---

### 1.5 Triage flow (нет кода)

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    participant D as БД
    participant G as Support Group
    
    C->>B: [Нажал "Нет кода"]
    B->>C: "Укажите компанию/проект"
    C->>B: "Компания ABC"
    B->>C: "Контакт (email/телефон)? Можно пропустить"
    C->>B: "user@mail.com"
    B->>D: CREATE triage ticket
    B->>G: Создать topic "TRIAGE | Компания ABC"
    B->>C: "Спасибо! Мы свяжемся с вами"
```

---

## 2. Создание тикета

### 2.1 Стандартный flow с превью

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    participant D as БД
    participant G as Support Group
    
    Note over C,B: Шаг 1: Категория
    C->>B: [Выбрал "Не работает / ошибка"]
    B->>C: "Опишите проблему подробнее"
    
    Note over C,B: Шаг 2: Описание
    C->>B: "Не могу войти в личный кабинет"
    B->>C: "Можно прикрепить скрин/видео/файл"
    B->>C: [Пропустить]
    
    Note over C,B: Шаг 3: Вложения
    alt Клиент прикрепил файл
        C->>B: [Фото]
        B->>C: "Ещё? [📋 Превью и отправить]"
        C->>B: [📋 Превью и отправить]
    else Клиент пропустил
        C->>B: [Пропустить]
    end
    
    Note over C,B: Шаг 4: Превью (Summary)
    B->>C: "📋 Превью вашего обращения:<br/>Категория: 🐛 Не работает<br/>Описание: Не могу войти...<br/>Вложения: 1 файл(ов)"
    B->>C: [✏️ Категория] [✏️ Описание]
    B->>C: [✏️ Вложения]
    B->>C: [❌ Отмена] [✅ Отправить]
    
    alt Клиент редактирует
        C->>B: [✏️ Описание]
        B->>C: "Введите новое описание:"
        C->>B: "Исправленное описание"
        B->>C: [Показывает превью снова]
    end
    
    C->>B: [✅ Отправить]
    
    Note over C,B: Шаг 5: Создание
    B->>D: CREATE ticket (number=123)
    B->>D: GET/CREATE client topic
    B->>G: Отправить в topic клиента "#Client"
    B->>G: Карточка тикета + [Взять] [Закрыть] [Детали]
    B->>G: Переслать описание + вложения
    B->>C: "Готово, обращение #123 принято!"
```

**Текст бота (превью):**
> 📋 Превью вашего обращения:
>
> 📁 Категория: 🐛 Не работает / ошибка
>
> 📝 Описание:
> Не могу войти в личный кабинет
>
> 📎 Вложения: 1 файл(ов)
>
> Всё верно?

**Текст бота (подтверждение):**
> ✅ Готово, обращение **#123** принято!
>
> Рабочие часы: Пн–Пт 10:00–19:00 (Europe/Madrid)
> Обычно отвечаем за 2–4 часа.

---

### 2.2 Topic per Client архитектура

Все тикеты от одной компании-клиента направляются в один и тот же topic (тему) в Support Group:

```mermaid
flowchart LR
    subgraph old [Было: Topic per Ticket]
        T1[Ticket 1] --> Topic1[Topic 1]
        T2[Ticket 2] --> Topic2[Topic 2]
        T3[Ticket 3] --> Topic3[Topic 3]
    end
    
    subgraph new_arch [Стало: Topic per Client]
        C1[Client A] --> TopicA[🏢 Client A]
        TA1[Ticket 1] --> TopicA
        TA2[Ticket 2] --> TopicA
        C2[Client B] --> TopicB[🏢 Client B]
        TB1[Ticket 3] --> TopicB
    end
```

**Преимущества:**
- Вся история клиента в одном месте
- Операторы видят контекст предыдущих обращений
- Несколько пользователей от одной компании попадают в один topic

---

### 2.3 Flow "Срочно"

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    
    C->>B: [Выбрал "Срочно"]
    
    Note over C,B: Доп. вопрос 1
    B->>C: "Насколько блокирует работу?"
    B->>C: [Полностью] [Частично] [Не блокирует]
    C->>B: [Полностью блокирует]
    
    Note over C,B: Доп. вопрос 2
    B->>C: "Что именно не работает?"
    C->>B: "Весь сайт недоступен"
    
    Note over C,B: Вложения
    B->>C: "Скрин/видео? [Пропустить]"
    C->>B: [Пропустить]
    
    Note over C,B: Превью + Создание с priority=urgent
    B->>B: Показать превью, затем создать тикет priority=urgent
```

---

## 3. Активное обращение

### 3.1 Сообщение при открытом тикете

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    participant D as БД
    participant G as Support Group
    
    C->>B: "Добавлю: проблема только в Chrome"
    B->>D: SELECT active ticket for user
    D-->>B: Ticket #123 (status=in_progress)
    B->>D: INSERT message
    B->>G: Переслать в topic #123
```

---

### 3.2 Сообщение после закрытия (< 48h)

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    participant D as БД
    
    C->>B: "Проблема вернулась"
    B->>D: SELECT recent closed ticket (< 48h)
    D-->>B: Ticket #123 (closed 2h ago)
    
    B->>C: "Открыть новый или продолжить #123?"
    B->>C: [Новый тикет] [Открыть #123]
    
    alt Открыть старый
        C->>B: [Открыть #123]
        B->>D: UPDATE ticket SET status='in_progress'
        B->>B: Уведомить операторов
    else Новый тикет
        C->>B: [Новый тикет]
        B->>C: [Меню категорий]
    end
```

---

### 3.3 Сообщение после закрытия (> 48h)

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    
    C->>B: "Привет, есть вопрос"
    B->>B: Нет активных, нет недавних closed
    B->>C: "Выберите категорию"
    B->>C: [Меню категорий]
```

---

## 4. Работа оператора

### 4.1 Взять в работу

```mermaid
sequenceDiagram
    participant O as Оператор
    participant G as Support Group
    participant B as Бот
    participant D as БД
    participant C as Клиент
    
    O->>G: [Нажал "Взять в работу"]
    G->>B: Callback: take_ticket:123
    B->>D: UPDATE ticket SET status='in_progress', assigned_to=O
    B->>G: Обновить карточку (статус, assigned)
    B->>C: "Ваш запрос взят в работу"
```

---

### 4.2 Ответ клиенту

```mermaid
sequenceDiagram
    participant O as Оператор
    participant G as Support Group (topic)
    participant B as Бот
    participant D as БД
    participant C as Клиент
    
    O->>G: "Проверьте, пожалуйста, кэш браузера"
    G->>B: Message in topic
    B->>B: Проверить: O в OPERATORS?
    
    alt Оператор в списке
        B->>D: INSERT message (direction=operator)
        B->>C: "Ответ поддержки: Проверьте кэш..."
    else Не оператор
        B->>B: Игнорировать
    end
```

---

### 4.3 Запросить детали

```mermaid
sequenceDiagram
    participant O as Оператор
    participant G as Support Group
    participant B as Бот
    participant C as Клиент
    
    O->>G: [Нажал "Запросить детали"]
    G->>B: Callback: request_details:123
    B->>C: "Нужно чуть больше деталей:
           1. что вы делали перед проблемой
           2. ссылка/экран/раздел
           3. скрин/видео (если можно)"
```

---

### 4.4 Закрыть тикет

```mermaid
sequenceDiagram
    participant O as Оператор
    participant G as Support Group
    participant B as Бот
    participant D as БД
    participant C as Клиент
    
    O->>G: [Нажал "Закрыть"]
    G->>B: Callback: close_ticket:123
    B->>D: UPDATE ticket SET status='closed', closed_at=NOW()
    B->>G: Обновить карточку
    B->>C: "Кажется, решили. Если что — напишите."
    B->>C: "Оцените: [👍] [👎]"
```

---

## 5. CSAT

### 5.1 Положительная оценка

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    participant D as БД
    participant G as Support Group
    
    C->>B: [Нажал 👍]
    B->>D: INSERT feedback (csat='positive')
    B->>C: "Спасибо за оценку!"
    B->>G: "📊 Feedback: 👍"
```

---

### 5.2 Негативная оценка

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    participant D as БД
    participant G as Support Group
    
    C->>B: [Нажал 👎]
    B->>C: "Что было не так?"
    C->>B: "Долго ждал ответа"
    B->>D: INSERT feedback (csat='negative', comment='...')
    B->>C: "Спасибо, учтём!"
    B->>G: "📊 Feedback: 👎
           Комментарий: Долго ждал ответа"
```

---

## 6. Команда /project

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    participant D as БД
    
    C->>B: /project
    B->>D: SELECT projects for user
    D-->>B: [Project A, Project B]
    
    alt Несколько проектов
        B->>C: "Ваши проекты:"
        B->>C: [Project A ✓] [Project B]
        C->>B: [Project B]
        B->>D: UPDATE active project
        B->>C: "Переключено на Project B"
    else Один проект
        B->>C: "Вы привязаны к: Project A"
    end
```

---

## 7. Edge Cases

### 7.1 Пользователь без username

```mermaid
sequenceDiagram
    participant C as Клиент (без @username)
    participant B as Бот
    participant D as БД
    
    C->>B: /start CODE
    B->>D: INSERT user_binding (tg_username=NULL, tg_name="Иван")
    B->>C: [Обычный flow]
    
    Note over B: В карточке: "Иван (id: 123456)"
```

---

### 7.2 Два оператора нажали "Взять"

```mermaid
sequenceDiagram
    participant O1 as Оператор 1
    participant O2 as Оператор 2
    participant G as Support Group
    participant B as Бот
    participant D as БД
    
    O1->>G: [Взять в работу]
    O2->>G: [Взять в работу]
    
    B->>D: UPDATE ticket SET assigned=O1 (первый)
    B->>G: "Тикет взял @operator1"
    
    B->>D: SELECT ticket (уже assigned)
    B->>G: "Тикет уже в работе у @operator1"
```

---

### 7.3 Несколько вложений подряд

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Бот
    participant G as Support Group
    
    Note over C,B: В режиме ожидания вложений
    C->>B: [Фото 1]
    B->>B: Сохранить, показать [Ещё] [Готово]
    C->>B: [Фото 2]
    B->>B: Сохранить
    C->>B: [Документ]
    B->>B: Сохранить
    C->>B: [Готово]
    B->>B: Создать тикет
    B->>G: Переслать все 3 вложения
```

---

*Актуально для: 2026-02-05*
