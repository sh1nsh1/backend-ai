# Portfolio Backend API

Backend-сервис для лендинг-презентации разработчика с AI-интеграцией.

## Стек технологий

| Компонент | Технология |
|---|---|
| **Backend** | Python 3.13, FastAPI |
| **AI** | DeepSeek API (через OpenAI SDK) |
| **Rate Limiting** | SlowAPI + Redis |
| **Email** | aiosmtplib |
| **Database** | PostgreSQL 16, SQLAlchemy 2.0 (async) + asyncpg |
| **Config** | pydantic-settings (.env) |
| **Logging** | colorlog + RotatingFileHandler |
| **ASGI Server** | Uvicorn |
| **Containerization** | Docker, Docker Compose |

## Как запустить

### Локально

```bash
# Создание и активация виртуального окружения
python -m venv .venv
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# заполните .env своими данными

# Требуется запущенный Redis и PostgreSQL
# или используйте Docker Compose для инфраструктуры:
docker compose up -d redis postgres

# Запуск
uvicorn main:app --reload
```

### Docker Compose (полностью)

```bash
cp .env.example .env
# заполните .env
docker compose up --build
```

Сервер будет доступен на `http://localhost:8000`.
Swagger-документация: `http://localhost:8000/docs`.

## Переменные окружения

| Переменная | Обязательная | Дефолт | Описание |
|---|---|---|---|
| `LOG_FILE` | нет | — | Путь к файлу логов |
| `REDIS_URL` | да | `redis:6379` | Адрес Redis (rate limiting) |
| `POSTGRES_HOST` | да | `localhost` | Хост PostgreSQL |
| `POSTGRES_PORT` | да | `5432` | Порт PostgreSQL |
| `POSTGRES_USER` | да | `app` | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | да | `app` | Пароль PostgreSQL |
| `POSTGRES_DB` | да | `app` | База данных PostgreSQL |
| `EMAIL_SMTP_HOST` | да | — | SMTP сервер |
| `EMAIL_SMTP_PORT` | да | — | Порт SMTP |
| `EMAIL_SMTP_USER` | да | — | Логин SMTP |
| `EMAIL_SMTP_PASSWORD` | да | — | Пароль SMTP |
| `DEEPSEEK_API_KEY` | да | — | API ключ DeepSeek |
| `DEEPSEEK_BASE_URL` | нет | `https://api.deepseek.com` | Базовый URL API |
| `DEEPSEEK_MODEL` | нет | `deepseek-chat` | Модель DeepSeek |

## Архитектура

```
main.py               ← Точка входа, lifespan, middleware, error handlers
│
controllers/          ← HTTP слой (роуты, валидация)
└── router.py         ← Эндпоинты /api/*
│
services/             ← Бизнес-логика
├── ai_service.py     ← DeepSeek AI (анализ обращений, чат)
├── email_service.py  ← SMTP-отправка писем
└── metrics_service.py← Статистика запросов
│
repositories/         ← Работа с данными
└── metrics_repository.py ← SQLAlchemy запросы к request_logs
│
models/               ← ORM-модели
├── __init__.py
└── request_log.py    ← Модель RequestLog
│
database.py           ← Async engine, Session, init_db()
config.py             ← Конфигурация из .env (pydantic-settings)
logger.py             ← Настройка логирования (console + file)
rate_limiter.py       ← SlowAPI + Redis
schemas.py            ← Pydantic схемы запросов/ответов
```

**Поток запроса:**

```
Request → Router (валидация) → Service (бизнес-логика) → Repository (БД) → Response
```

**Паттерны:**
- Dependency Injection (FastAPI Depends)
- Service layer + Repository layer
- Graceful fallback для AI
- Хранение метрик в PostgreSQL (SQLAlchemy async)

## API Endpoints

### `GET /api/health`
Проверка работоспособности сервиса.

**Response 200:**
```json
{ "healthy": true }
```

### `GET /api/metrics`
Статистика запросов (агрегация из PostgreSQL).

**Response 200:**
```json
{
  "total_requests": 42,
  "endpoints": {
    "contact": { "count": 10, "last_at": "2024-01-01T12:00:00" }
  },
  "started_at": "2024-01-01T00:00:00",
  "last_request_at": "2024-01-01T12:00:00"
}
```

### `POST /api/contact`
Отправка формы обратной связи с AI-анализом.

**Rate limit:** 3 запроса в минуту с одного IP.

**Request:**
```json
{
  "name": "Иван Иванов",
  "email": "ivan@example.com",
  "phone": "+79991234567",
  "message": "Хочу сотрудничать!"
}
```

**Response 200:**
```json
{
  "message": "Contact request sent successfully",
  "analysis": {
    "category": "Collaboration",
    "sentiment": "positive",
    "suggested_reply": "Здравствуйте! Спасибо за ваш интерес..."
  }
}
```

**Response 429:**
```json
{ "detail": "Too many requests. Please try again later." }
```

**Логика обработки:**
1. Валидация входных данных (Pydantic)
2. AI-анализ: категория + тональность + suggested reply (graceful fallback при ошибке)
3. Email владельцу с AI-анализом
4. Email-копия пользователю с вежливым ответом
5. Сохранение в метрики (PostgreSQL)

## AI-интеграция

- **Провайдер:** DeepSeek (совместим с OpenAI API)
- **SDK:** `openai` (AsyncOpenAI)
- **Функция:** анализ обращений — категория, тональность, suggested reply

### Fallback

При любой ошибке (сеть, таймаут, невалидный JSON) сервис возвращает значения по умолчанию:

```json
{
  "category": "Other",
  "sentiment": "neutral",
  "suggested_reply": "Здравствуйте! Спасибо за ваше обращение. Мы получили ваше сообщение и свяжемся с вами в ближайшее время."
}
```

Email отправляется в любом случае.

### Промпт

```
Analyze the following contact form submission and return a JSON with:
- "category": one of ["Collaboration", "Support", "Feedback", "Other"]
- "sentiment": one of ["positive", "neutral", "negative"]
- "suggested_reply": a short, polite response in Russian

Contact data:
Name: {name}
Email: {email}
Message: {message}
```

## Обработка ошибок

| Ситуация | HTTP Status | Детали |
|---|---|---|
| Валидация данных | 400 | Pydantic validation error |
| Rate limit превышен | 429 | RateLimitExceeded → SlowAPI |
| SMTP недоступен | 503 | aiosmtplib.SMTPException |
| AI недоступен | 200 | Graceful fallback |
| Любая другая | 500 | Global exception handler (логируется в файл) |

Все ошибки логируются в файл (если `LOG_FILE` указан) и в stdout с цветным форматированием.

## curl-примеры

```bash
# Health check
curl http://localhost:8000/api/health

# Metrics
curl http://localhost:8000/api/metrics

# Contact form
curl -X POST http://localhost:8000/api/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Иван",
    "email": "ivan@example.com",
    "phone": "+79991234567",
    "message": "Хочу предложить сотрудничество"
  }'
```

## Хранение данных

- **Метрики:** PostgreSQL, таблица `request_logs` (endpoint, requested_at)
- **Rate limiting:** Redis (через SlowAPI)
- **Логи:** файловая система (RotatingFileHandler, 50MB, 5 бэкапов)
- **Статистика:** агрегация на лету через SQL (COUNT, MIN, MAX, GROUP BY)
