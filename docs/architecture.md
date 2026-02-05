# Архитектура проекта: Customer Support

## Общая схема системы

```mermaid
graph TB
    subgraph "Frontend"
        WEB[React Web App]
    end
    
    subgraph "API Gateway"
        NGINX[Nginx / Reverse Proxy]
    end
    
    subgraph "Backend"
        API[FastAPI App]
        CELERY[Celery Workers]
        BEAT[Celery Beat]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        REDIS[(Redis)]
    end
    
    subgraph "External Services"
        OPENAI[OpenAI API]
        SUPABASE[Supabase]
        SMTP[SMTP Server]
        NAKAMA[Nakama API]
    end
    
    WEB --> NGINX
    NGINX --> API
    API --> PG
    API --> REDIS
    API --> CELERY
    CELERY --> PG
    CELERY --> REDIS
    CELERY --> OPENAI
    CELERY --> SUPABASE
    CELERY --> SMTP
    CELERY --> NAKAMA
    BEAT --> CELERY
```

## Схема обработки запроса

```mermaid
sequenceDiagram
    participant C as Client (React)
    participant A as API (FastAPI)
    participant D as Database (PostgreSQL)
    participant R as Redis
    participant W as Celery Worker
    participant E as External API
    
    C->>A: POST /api/v1/request
    A->>D: Validate & Save
    A->>R: Add task to queue
    A-->>C: 202 Accepted (task_id)
    
    R->>W: Get task
    W->>E: Call external service
    E-->>W: Response
    W->>D: Save result
    
    C->>A: GET /api/v1/result/{task_id}
    A->>D: Get result
    A-->>C: 200 OK (result)
```

## Структура Frontend (Feature-Sliced Design)

```mermaid
graph TD
    subgraph "Layers"
        APP[app/]
        PAGES[pages/]
        WIDGETS[widgets/]
        FEATURES[features/]
        ENTITIES[entities/]
        SHARED[shared/]
    end
    
    APP --> PAGES
    PAGES --> WIDGETS
    WIDGETS --> FEATURES
    FEATURES --> ENTITIES
    ENTITIES --> SHARED
    
    subgraph "app/"
        PROVIDERS[providers/]
        ROUTER[router/]
        STYLES[styles/]
    end
    
    subgraph "components/"
        UI[ui/ - shadcn]
    end
```

## Компоненты системы

### Backend

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| API Server | FastAPI | REST API endpoints |
| ORM | SQLAlchemy 2.0 | Database access |
| Validation | Pydantic | Data validation |
| Auth | python-jose | JWT tokens |
| Background | Celery | Async tasks |
| Cache | Redis | Caching & queue |

### Frontend

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| UI Library | React 18 | UI rendering |
| State | TanStack Query | Server state |
| Routing | React Router | Navigation |
| Styling | Tailwind CSS | Styling |
| Components | shadcn/ui | UI components |
| Forms | react-hook-form | Form handling |
| Validation | Zod | Schema validation |

### Infrastructure

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| Container | Docker | Containerization |
| Orchestration | Docker Compose | Multi-container |
| Proxy | Nginx | Reverse proxy |
| Database | PostgreSQL 16 | Primary database |
| Cache | Redis 7 | Cache & queue |

## Схема базы данных (пример)

```mermaid
erDiagram
    USER ||--o{ SESSION : has
    USER {
        int id PK
        string email UK
        string password_hash
        string name
        datetime created_at
        boolean is_active
    }
    SESSION {
        int id PK
        int user_id FK
        string token UK
        datetime expires_at
        datetime created_at
    }
```

## Потоки данных

### Аутентификация

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant D as Database
    
    U->>F: Enter credentials
    F->>A: POST /api/v1/auth/login
    A->>D: Verify user
    D-->>A: User data
    A->>A: Generate JWT
    A-->>F: Access + Refresh tokens
    F->>F: Store tokens
    F-->>U: Redirect to dashboard
```

### Protected Request

```mermaid
sequenceDiagram
    participant F as Frontend
    participant A as API
    participant D as Database
    
    F->>A: GET /api/v1/protected
    Note over F,A: Authorization: Bearer <token>
    A->>A: Verify JWT
    alt Token Valid
        A->>D: Get data
        D-->>A: Data
        A-->>F: 200 OK
    else Token Invalid
        A-->>F: 401 Unauthorized
    end
```

---

## Deployment

### Development

```
localhost:5173  → Frontend (Vite)
localhost:8000  → Backend (FastAPI)
localhost:5432  → PostgreSQL
localhost:6379  → Redis
```

### Production

```
example.com     → Nginx → Frontend static
api.example.com → Nginx → Backend API
```

---

*Диаграммы отображаются в GitHub/GitLab и в VS Code с расширением Mermaid.*
