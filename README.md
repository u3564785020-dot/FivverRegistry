# 🤖 Fiverr Account Registrator Bot

Telegram бот для автоматической регистрации аккаунтов на платформе Fiverr с поддержкой прокси и многопоточности.

## ✨ Возможности

- ✅ **Автоматическая регистрация** аккаунтов на Fiverr
- 🔒 **Поддержка прокси** для каждого аккаунта
- ⚡ **Асинхронная работа** - регистрация нескольких аккаунтов одновременно
- 📧 **Автоматическая покупка email** через API (anymessage.shop)
- 🍪 **Автоматическое сохранение cookies** после регистрации
- 💾 **MongoDB** для хранения данных
- 📊 **История всех операций** и статистика
- 🚀 **Простой деплой** на Railway

## 📋 Требования

- Python 3.11+
- MongoDB (можно использовать MongoDB Atlas или Railway MongoDB)
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))
- API токен для anymessage.shop
- Прокси-серверы

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <your-repo-url>
cd fiverr-bot
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Настройка окружения

Создайте файл `.env` на основе `env.example`:

```bash
cp env.example .env
```

Заполните переменные окружения:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=fiverr_bot

# Email API Configuration
EMAIL_API_TOKEN=your_api_token_here
EMAIL_API_BASE_URL=https://api.anymessage.shop

# Fiverr Configuration
FIVERR_SITE=fiverr.com

# Admin User IDs (comma separated)
ADMIN_IDS=123456789,987654321

# Logs
LOG_LEVEL=INFO
```

### 4. Запуск бота

```bash
python main.py
```

## 🌐 Деплой на Railway

Railway - это простая платформа для деплоя приложений. [Подробнее](https://railway.app)

### Шаг 1: Подготовка

1. Зарегистрируйтесь на [Railway](https://railway.app)
2. Установите [Railway CLI](https://docs.railway.app/develop/cli) (опционально)
3. Подключите ваш GitHub репозиторий к Railway

### Шаг 2: Создание проекта

1. Создайте новый проект в Railway
2. Добавьте MongoDB сервис:
   - В дашборде нажмите "New Service"
   - Выберите "Database" → "MongoDB"
   - Railway автоматически создаст базу данных

### Шаг 3: Настройка переменных окружения

В настройках вашего сервиса добавьте переменные окружения:

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен вашего Telegram бота |
| `MONGODB_URI` | Автоматически заполнится Railway |
| `EMAIL_API_TOKEN` | Токен API anymessage.shop |
| `ADMIN_IDS` | ID администраторов через запятую |

### Шаг 4: Деплой

Railway автоматически задетектит `Dockerfile` и `railway.json` и начнет деплой.

После успешного деплоя бот автоматически запустится и будет работать 24/7.

## 📖 Использование

### Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветственное сообщение |
| `/help` | Подробная справка |
| `/balance` | Проверка баланса API почт |
| `/register` | Начать регистрацию аккаунтов |
| `/tasks` | Просмотр ваших задач |
| `/accounts` | Список зарегистрированных аккаунтов |

### Процесс регистрации

1. Отправьте команду `/register`
2. Укажите количество аккаунтов (1-50)
3. Отправьте прокси в формате `username:password@ip:port` (по одному на строку)
4. Бот начнет регистрацию
5. После завершения вы получите cookies файлы для каждого аккаунта

### Формат прокси

```
username:password@ip:port
```

**Пример:**
```
b66AnDhC0l9xFOTj:b66AnDhC0l9xFOTj@109.104.153.193:14534
```

## 🏗️ Структура проекта

```
fiverr-bot/
├── bot/                    # Telegram бот
│   ├── __init__.py
│   └── handlers.py        # Обработчики команд
├── services/              # Сервисы
│   ├── __init__.py
│   ├── database.py        # Работа с MongoDB
│   ├── email_api.py       # API покупки почт
│   ├── fiverr_registrator.py  # Автоматизация регистрации
│   └── proxy_manager.py   # Управление прокси
├── utils/                 # Утилиты
│   ├── __init__.py
│   └── logger.py          # Логирование
├── cookies/               # Сохраненные cookies
├── logs/                  # Логи
├── config.py              # Конфигурация
├── main.py                # Точка входа
├── requirements.txt       # Зависимости
├── Dockerfile             # Docker образ
├── railway.json           # Конфигурация Railway
├── .dockerignore
├── .gitignore
└── README.md
```

## 🔧 API анимессаге

Бот использует API сервиса [anymessage.shop](https://api.anymessage.shop) для покупки временных почт.

### Основные методы:

- `GET /user/balance` - Получение баланса
- `GET /email/quantity` - Доступные почты
- `GET /email/order` - Заказать почту
- `GET /email/getmessage` - Получить сообщение
- `GET /email/cancel` - Отменить активацию

Подробная документация доступна в коде (`services/email_api.py`).

## ⚙️ Конфигурация

### Основные настройки (config.py)

```python
# Максимальное количество параллельных регистраций
MAX_CONCURRENT_REGISTRATIONS = 5

# Таймаут регистрации (секунды)
REGISTRATION_TIMEOUT = 300

# Режим браузера (headless)
BROWSER_HEADLESS = True

# Таймаут браузера (миллисекунды)
BROWSER_TIMEOUT = 60000
```

## 📊 База данных

### Коллекции MongoDB:

1. **users** - Пользователи бота
   - user_id (Telegram ID)
   - username
   - total_accounts
   - created_at

2. **tasks** - Задачи на регистрацию
   - task_id
   - user_id
   - total_accounts
   - completed_accounts
   - status
   - proxies

3. **accounts** - Зарегистрированные аккаунты
   - email
   - password
   - user_id
   - cookies
   - proxy
   - created_at

## 🐛 Отладка

### Просмотр логов

Логи сохраняются в директории `logs/`:
- `bot_YYYY-MM-DD.log` - Общие логи
- `errors_YYYY-MM-DD.log` - Ошибки

### Локальная отладка

```bash
# Установите переменные окружения
export TELEGRAM_BOT_TOKEN=your_token
export MONGODB_URI=mongodb://localhost:27017

# Запустите бота
python main.py
```

## ⚠️ Важные замечания

1. **Прокси**: Один прокси = один аккаунт. Используйте разные прокси для каждого аккаунта.

2. **Баланс API**: Убедитесь, что на балансе API достаточно средств (≈ $0.002 на аккаунт).

3. **Лимиты**: Fiverr может иметь ограничения на регистрацию. Рекомендуется делать паузы между массовыми регистрациями.

4. **Селекторы**: Fiverr может изменить структуру сайта. В этом случае нужно обновить селекторы в `services/fiverr_registrator.py`.

5. **Headless режим**: Для продакшена рекомендуется использовать headless режим (`BROWSER_HEADLESS=true`).

## 🔐 Безопасность

- ❌ **Никогда** не коммитьте `.env` файл
- ✅ Храните API токены в секретах Railway
- ✅ Ограничьте доступ к боту через `ADMIN_IDS`
- ✅ Используйте приватные прокси
- ✅ Регулярно обновляйте зависимости

## 📝 Лицензия

MIT License

## 🤝 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте логи в директории `logs/`
2. Убедитесь, что все переменные окружения установлены правильно
3. Проверьте баланс API anymessage.shop
4. Убедитесь, что прокси работают

## 🚀 Roadmap

- [ ] Поддержка капчи (2Captcha, Anti-Captcha)
- [ ] Web интерфейс для управления
- [ ] Поддержка других платформ (Upwork, Freelancer)
- [ ] Автоматическое пополнение баланса API
- [ ] Статистика и аналитика
- [ ] Система уведомлений

## 📚 Дополнительные ресурсы

- [Railway Docs](https://docs.railway.app)
- [Playwright Docs](https://playwright.dev/python/)
- [python-telegram-bot Docs](https://python-telegram-bot.org/)
- [MongoDB Motor Docs](https://motor.readthedocs.io/)

---

**Создано с ❤️ для автоматизации рутинных задач**

