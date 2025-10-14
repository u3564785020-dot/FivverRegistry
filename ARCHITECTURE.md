# 🏗️ Архитектура проекта

## 📊 Общая схема

```
┌─────────────────────────────────────────────────────────────────┐
│                         Пользователь                            │
│                      (Telegram Client)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Telegram Bot API                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       bot/handlers.py                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │  /start    │  │ /register  │  │ /balance   │  ...          │
│  └────────────┘  └────────────┘  └────────────┘               │
└────────┬────────────────┬────────────────┬─────────────────────┘
         │                │                │
         ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Database   │  │   Email     │  │   Proxy     │
│   Service   │  │   Service   │  │   Manager   │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       ▼                ▼                ▼
┌────────────────────────────────────────────────┐
│         Fiverr Registrator Service             │
│                                                 │
│  ┌──────────────────────────────────────────┐ │
│  │        Playwright Browser                │ │
│  │  ┌────────┐  ┌────────┐  ┌────────┐    │ │
│  │  │Navigate│  │ Fill   │  │Confirm │    │ │
│  │  │  Form  │  │ Form   │  │ Email  │    │ │
│  │  └────────┘  └────────┘  └────────┘    │ │
│  └──────────────────────────────────────────┘ │
└────────────────────┬───────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│              Fiverr.com                         │
└─────────────────────────────────────────────────┘
```

## 🔄 Поток данных при регистрации

```
1. Пользователь → /register
   │
   ├─> Указывает количество аккаунтов
   │
   └─> Отправляет прокси
       │
       ▼
2. Bot Handler
   │
   ├─> Создает задачу в MongoDB
   │
   └─> Запускает регистрацию асинхронно
       │
       ▼
3. Email API Service
   │
   ├─> Проверяет баланс
   │
   ├─> Заказывает email
   │
   └─> Возвращает email + activation_id
       │
       ▼
4. Proxy Manager
   │
   ├─> Парсит прокси строку
   │
   ├─> Проверяет работоспособность
   │
   └─> Конвертирует в формат Playwright
       │
       ▼
5. Fiverr Registrator
   │
   ├─> Инициализирует браузер с прокси
   │
   ├─> Переходит на страницу регистрации
   │
   ├─> Заполняет форму (email, password, username)
   │
   ├─> Отправляет форму
   │
   └─> Ждет письмо с подтверждением
       │
       ▼
6. Email API Service
   │
   ├─> Запрашивает письмо (polling)
   │
   ├─> Получает код подтверждения
   │
   └─> Возвращает код
       │
       ▼
7. Fiverr Registrator
   │
   ├─> Вводит код подтверждения
   │
   ├─> Получает cookies браузера
   │
   ├─> Сохраняет cookies в файл
   │
   └─> Возвращает результат
       │
       ▼
8. Database Service
   │
   ├─> Сохраняет данные аккаунта
   │
   ├─> Обновляет статус задачи
   │
   └─> Инкрементирует счетчики
       │
       ▼
9. Bot Handler
   │
   ├─> Отправляет cookies пользователю
   │
   └─> Отправляет итоговый отчет
```

## 🧩 Компоненты системы

### 1. Bot Layer (Telegram интерфейс)

```
bot/handlers.py
├── Command Handlers
│   ├── start_command()
│   ├── register_command()
│   ├── balance_command()
│   ├── tasks_command()
│   └── accounts_command()
│
├── Message Handlers
│   └── handle_message()
│       ├── waiting_count
│       └── waiting_proxies
│
└── Background Tasks
    └── run_registration_task()
```

**Ответственность:**
- Прием команд от пользователя
- Валидация ввода
- Управление состоянием диалога
- Запуск фоновых задач
- Отправка результатов пользователю

### 2. Service Layer (Бизнес-логика)

```
services/
├── email_api.py
│   └── EmailAPIService
│       ├── get_balance()
│       ├── get_available_emails()
│       ├── order_email()
│       ├── get_message()
│       └── cancel_email()
│
├── proxy_manager.py
│   ├── ProxyConfig
│   │   ├── from_string()
│   │   ├── to_playwright_format()
│   │   └── to_url()
│   │
│   └── ProxyManager
│       ├── check_proxy()
│       └── get_proxy_ip()
│
├── fiverr_registrator.py
│   └── FiverrRegistrator
│       ├── _init_browser()
│       ├── _close_browser()
│       ├── register_account()
│       └── register_multiple_accounts()
│
└── database.py
    └── Database
        ├── User Methods
        ├── Task Methods
        └── Account Methods
```

**Ответственность:**
- Изолированная бизнес-логика
- Интеграция с внешними сервисами
- Управление данными
- Обработка ошибок

### 3. Data Layer (Хранение данных)

```
MongoDB
├── users (collection)
│   ├── user_id: int (indexed)
│   ├── username: string
│   ├── total_accounts: int
│   ├── created_at: datetime
│   └── is_active: bool
│
├── tasks (collection)
│   ├── task_id: string (indexed)
│   ├── user_id: int (indexed)
│   ├── total_accounts: int
│   ├── completed_accounts: int
│   ├── failed_accounts: int
│   ├── status: string (indexed)
│   ├── proxies: array
│   ├── results: array
│   ├── created_at: datetime
│   └── completed_at: datetime
│
└── accounts (collection)
    ├── email: string (indexed, unique)
    ├── password: string
    ├── user_id: int (indexed)
    ├── task_id: string
    ├── cookies: object
    ├── proxy: string
    ├── created_at: datetime
    └── is_active: bool
```

## 🔐 Безопасность

### Уровни защиты:

1. **Аутентификация**
   - Проверка `user_id` в `ADMIN_IDS`
   - Валидация токенов

2. **Авторизация**
   - Проверка активности пользователя
   - Проверка баланса перед регистрацией

3. **Шифрование**
   - HTTPS для всех API запросов
   - Переменные окружения для секретов
   - Безопасное хранение в Railway

4. **Валидация**
   - Проверка формата прокси
   - Проверка количества аккаунтов (1-50)
   - Санитизация пользовательского ввода

## ⚡ Асинхронность и производительность

### Асинхронные операции:

```python
# Параллельное выполнение
async def register_accounts_batch():
    tasks = [
        registrator1.register_account(),
        registrator2.register_account(),
        registrator3.register_account(),
    ]
    results = await asyncio.gather(*tasks)
```

### Оптимизации:

1. **Connection Pooling**
   - Переиспользование HTTP соединений
   - Motor async driver для MongoDB

2. **Caching**
   - Кеширование доступных доменов
   - Кеширование user данных

3. **Lazy Loading**
   - Браузер создается только при необходимости
   - Отложенная загрузка resources

## 🔄 Обработка ошибок

### Уровни обработки:

```
1. Service Level
   ├── Try-Catch блоки
   ├── Логирование ошибок
   └── Возврат None/False

2. Handler Level
   ├── Проверка результатов сервисов
   ├── Уведомление пользователя
   └── Обновление статуса в БД

3. Application Level
   ├── Global error handler
   ├── Автоматический рестарт
   └── Логирование критических ошибок
```

### Retry механизмы:

```python
# Получение email с retry
for attempt in range(max_retries):
    result = await get_message(id)
    if result:
        return result
    await asyncio.sleep(retry_interval)
```

## 📊 Мониторинг

### Логирование:

```
logs/
├── bot_YYYY-MM-DD.log       # Все события
└── errors_YYYY-MM-DD.log    # Только ошибки
```

### Метрики:

- Успешные/неудачные регистрации
- Среднее время регистрации
- Использование прокси
- Баланс API

### Алерты:

- Низкий баланс API
- Частые ошибки регистрации
- Проблемы с прокси
- Падение сервисов

## 🚀 Масштабирование

### Вертикальное (Railway):

```
Resources:
├── RAM: 512MB → 2GB
├── CPU: 1 vCPU → 4 vCPU
└── Storage: auto-scaling
```

### Горизонтальное:

```
Multiple Instances
├── Instance 1 → Proxies 1-100
├── Instance 2 → Proxies 101-200
└── Instance 3 → Proxies 201-300

Shared MongoDB
```

## 🔌 API интеграции

### Внешние сервисы:

```
┌─────────────────┐
│  Telegram API   │ ← Bot commands/messages
└─────────────────┘

┌─────────────────┐
│ anymessage.shop │ ← Email purchasing
└─────────────────┘

┌─────────────────┐
│   Fiverr.com    │ ← Account registration
└─────────────────┘

┌─────────────────┐
│   MongoDB       │ ← Data storage
└─────────────────┘
```

## 🎯 Будущие улучшения

### v2.0 Architecture:

```
┌──────────────┐
│   Web UI     │ ← React/Vue dashboard
└──────┬───────┘
       │
┌──────▼───────┐
│  GraphQL API │ ← Unified API layer
└──────┬───────┘
       │
┌──────▼────────────────────────┐
│      Microservices            │
├───────────┬───────────────────┤
│ Auth      │ Registration      │
│ Service   │ Service           │
├───────────┼───────────────────┤
│ Email     │ Proxy             │
│ Service   │ Service           │
└───────────┴───────────────────┘
       │
┌──────▼───────┐
│  Message     │ ← RabbitMQ/Redis
│  Queue       │
└──────────────┘
```

---

**Документация:**
- [← Структура проекта](PROJECT_STRUCTURE.md)
- [→ FAQ](FAQ.md)

