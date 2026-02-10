# Архитектура: Telegram Support Bot

## Общая схема системы

```mermaid
graph TB
    subgraph "Клиенты"
        C1[Клиент 1]
        C2[Клиент 2]
        C3[Клиент N]
    end
    
    subgraph "Telegram"
        BOT[Support Bot]
        GROUP[Support Group<br/>with Topics]
    end
    
    subgraph "Backend"
        APP[Python App<br/>aiogram 3.x]
        DB[(SQLite)]
    end
    
    subgraph "Операторы"
        OP1[Оператор 1]
        OP2[Оператор 2]
    end
    
    C1 -->|"личный чат"| BOT
    C2 -->|"личный чат"| BOT
    C3 -->|"личный чат"| BOT
    
    BOT --> APP
    APP --> DB
    APP -->|"создаёт topic"| GROUP
    APP -->|"пересылает"| GROUP
    
    OP1 -->|"отвечает в topic"| GROUP
    OP2 -->|"отвечает в topic"| GROUP
    GROUP -->|"ответ"| APP
    APP -->|"пересылает клиенту"| BOT
```

## Схема обработки сообщения клиента

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Bot
    participant A as App (aiogram)
    participant D as SQLite
    participant G as Support Group
    participant O as Оператор
    
    C->>B: Сообщение
    B->>A: Update
    A->>D: Найти активный тикет
    
    alt Тикет существует
        A->>D: Сохранить сообщение
        A->>G: Переслать в topic тикета
    else Нет активного тикета
        A->>C: Показать меню категорий
        C->>B: Выбор категории
        B->>A: Callback
        A->>D: Создать тикет
        A->>G: Создать topic + карточка
        A->>C: "Обращение #N принято"
    end
    
    O->>G: Ответ в topic
    G->>A: Update из группы
    A->>D: Сохранить ответ
    A->>C: Переслать ответ клиенту
```

## Идентификация через invite-code

```mermaid
sequenceDiagram
    participant C as Клиент
    participant B as Bot
    participant A as App
    participant D as SQLite
    
    C->>B: /start CODE123
    B->>A: Message с deep link
    A->>D: Найти project по invite_code
    
    alt Код валиден
        A->>D: Создать user_binding
        A->>C: "Привет! Выберите категорию..."
    else Код невалиден
        A->>C: "Код не найден"
        A->>C: Кнопки: [Ввести код] [Нет кода]
    end
    
    Note over C,D: Triage flow
    C->>B: "Нет кода"
    B->>A: Callback
    A->>C: "Укажите компанию/проект"
    C->>B: "Компания X"
    A->>D: Создать triage тикет
    A->>A: Отправить в TRIAGE topic
```

## Жизненный цикл тикета

```mermaid
stateDiagram-v2
    [*] --> New: Клиент создаёт
    
    New --> InProgress: Оператор нажал<br/>"Взять в работу"
    New --> Closed: Оператор нажал<br/>"Закрыть"
    
    InProgress --> Closed: Оператор нажал<br/>"Закрыть"
    InProgress --> InProgress: Переписка
    
    Closed --> InProgress: Клиент написал<br/>(reopen, < 48h)
    Closed --> New: Клиент создал<br/>новый тикет
    Closed --> CSAT: Запрос оценки
    
    CSAT --> [*]: Оценка получена
    
    note right of New
        Topic создан в группе
        Карточка отправлена
    end note
    
    note right of Closed
        closed_at записан
        CSAT отправлен клиенту
    end note
```

## Структура компонентов

```mermaid
graph TD
    subgraph "app/bot/"
        H[handlers/]
        K[keyboards/]
        S[states/]
        M[middlewares/]
        F[filters/]
    end
    
    subgraph "app/database/"
        MOD[models.py]
        OPS[operations.py]
        CON[connection.py]
    end
    
    subgraph "app/services/"
        TS[ticket.py]
        NS[notification.py]
    end
    
    subgraph "app/config/"
        SET[settings.py]
        TXT[texts.py]
        CAT[categories.py]
    end
    
    H --> K
    H --> S
    H --> TS
    H --> NS
    TS --> OPS
    NS --> OPS
    OPS --> MOD
    OPS --> CON
    H --> TXT
    H --> CAT
    H --> SET
```

## Handlers структура

```mermaid
graph LR
    subgraph "handlers/"
        START[start.py<br/>/start, invite-code]
        TICKET[ticket.py<br/>создание тикета]
        OPERATOR[operator.py<br/>действия в группе]
        COMMON[common.py<br/>/help, /project]
        CLIENT[client_msg.py<br/>сообщения клиента]
    end
    
    subgraph "Routers"
        R1[private_router<br/>личные чаты]
        R2[group_router<br/>Support Group]
    end
    
    R1 --> START
    R1 --> TICKET
    R1 --> COMMON
    R1 --> CLIENT
    R2 --> OPERATOR
```

## Схема базы данных

```mermaid
erDiagram
    clients ||--o{ projects : has
    projects ||--o{ user_bindings : has
    projects ||--o{ tickets : has
    tickets ||--o{ messages : contains
    tickets ||--o| feedback : has
    
    clients {
        int id PK
        string name
        datetime created_at
    }
    
    projects {
        int id PK
        int client_id FK
        string name
        string invite_code UK
        bool is_active
        datetime created_at
    }
    
    user_bindings {
        int id PK
        bigint tg_user_id
        string tg_username
        string tg_name
        int project_id FK
        datetime created_at
        datetime updated_at
    }
    
    tickets {
        int id PK
        int number UK
        int project_id FK
        bigint tg_user_id
        string category
        string priority
        string status
        bigint support_chat_id
        int topic_id
        bigint assigned_to
        datetime created_at
        datetime first_response_at
        datetime closed_at
    }
    
    messages {
        int id PK
        int ticket_id FK
        string direction
        bigint tg_message_id
        string type
        text content
        string file_id
        bigint author_tg_user_id
        datetime created_at
    }
    
    feedback {
        int id PK
        int ticket_id FK
        string csat
        text comment
        datetime created_at
    }
```

## Flow обработки в группе

```mermaid
sequenceDiagram
    participant O as Оператор
    participant G as Support Group
    participant A as App
    participant D as SQLite
    participant C as Клиент
    
    Note over G: Topic тикета #123
    
    O->>G: Нажимает "Взять в работу"
    G->>A: Callback query
    A->>D: UPDATE ticket SET status='in_progress'
    A->>G: Обновить карточку
    A->>C: "Ваш запрос взят в работу"
    
    O->>G: Пишет ответ в topic
    G->>A: Message в topic
    A->>A: Проверить: operator в OPERATORS?
    A->>D: Сохранить message
    A->>C: Переслать ответ
    
    O->>G: Нажимает "Закрыть"
    G->>A: Callback query
    A->>D: UPDATE ticket SET status='closed'
    A->>G: Обновить карточку
    A->>C: "Решили! Оцените: 👍 👎"
```

---

*Диаграммы отображаются в GitHub/GitLab и в VS Code с расширением Mermaid.*
