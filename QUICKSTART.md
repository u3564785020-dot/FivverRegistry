# ⚡ Быстрый старт

## 5 минут до запуска

### Локальный запуск

```bash
# 1. Клонируйте репозиторий
git clone <your-repo-url>
cd fiverr-bot

# 2. Установите зависимости
pip install -r requirements.txt
playwright install chromium

# 3. Автоматическая настройка
python setup.py

# 4. Запустите MongoDB (если не используете Atlas)
# Инструкция: https://docs.mongodb.com/manual/installation/

# 5. Запустите бота
python main.py
```

### Деплой на Railway (рекомендуется)

```bash
# 1. Создайте аккаунт на railway.app

# 2. Создайте новый проект
# Dashboard → New Project → Deploy from GitHub

# 3. Добавьте MongoDB
# New Service → Database → MongoDB

# 4. Настройте переменные окружения
# Settings → Variables → Add:
# - TELEGRAM_BOT_TOKEN
# - EMAIL_API_TOKEN
# - ADMIN_IDS

# 5. Деплой произойдет автоматически!
```

## Необходимые токены

### 1. Telegram Bot Token
- Откройте [@BotFather](https://t.me/BotFather)
- Отправьте `/newbot`
- Сохраните токен

### 2. Ваш Telegram ID
- Откройте [@userinfobot](https://t.me/userinfobot)
- Сохраните ваш ID

### 3. Email API Token
- Зарегистрируйтесь на [anymessage.shop](https://anymessage.shop)
- Пополните баланс (~$5 на старт)
- Скопируйте токен из личного кабинета

### 4. Прокси (минимум 1)
Формат: `username:password@ip:port`

Купить можно на:
- [Webshare.io](https://webshare.io)
- [Brightdata](https://brightdata.com)
- Или у вашего провайдера

## Первая регистрация

1. Откройте вашего бота в Telegram
2. Отправьте `/start`
3. Проверьте баланс: `/balance`
4. Начните регистрацию: `/register`
5. Укажите количество: `1`
6. Отправьте прокси: `user:pass@ip:port`
7. Дождитесь завершения (~2-3 минуты)
8. Получите cookies файл!

## Структура

```
fiverr-bot/
├── bot/              # Telegram бот
├── services/         # Бизнес-логика
├── utils/            # Утилиты
├── config.py         # Настройки
└── main.py           # Запуск
```

## Помощь

- 📖 [Полная документация](README.md)
- 🚀 [Деплой на Railway](DEPLOYMENT.md)
- ❓ [FAQ](FAQ.md)
- 💡 [Примеры](EXAMPLES.md)

## Troubleshooting

**Бот не запускается?**
```bash
# Проверьте логи
cat logs/bot_*.log

# Убедитесь, что MongoDB запущена
# Проверьте переменные окружения
cat .env
```

**Ошибки при регистрации?**
- Проверьте баланс API: `/balance`
- Проверьте прокси: `python tests/test_proxy.py`
- Посмотрите логи: `logs/errors_*.log`

---

**Готово! 🎉**

Теперь вы можете массово регистрировать аккаунты на Fiverr.

Следующие шаги:
- [ ] Настройте несколько прокси
- [ ] Пополните баланс API
- [ ] Зарегистрируйте первые 10 аккаунтов
- [ ] Задеплойте на Railway

