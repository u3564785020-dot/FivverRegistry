# 📦 Подробное руководство по установке

## 🎯 Выберите способ установки

### 1️⃣ Локальная установка (Windows/Linux/Mac)
### 2️⃣ Деплой на Railway (рекомендуется)
### 3️⃣ Docker установка

---

## 1️⃣ Локальная установка

### Требования

- Python 3.11 или выше
- MongoDB (локально или Atlas)
- Git
- 2GB свободного места

### Шаг 1: Установка Python

**Windows:**
```powershell
# Скачайте с python.org
# Установите, отметьте "Add Python to PATH"
python --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3-pip
python3 --version
```

**macOS:**
```bash
brew install python@3.11
python3 --version
```

### Шаг 2: Установка MongoDB

**Windows:**
```powershell
# Скачайте MongoDB Community Server с mongodb.com
# Установите как сервис
# Запустите MongoDB
```

**Linux:**
```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community@6.0
brew services start mongodb-community@6.0
```

**Альтернатива: MongoDB Atlas (облачная)**
1. Зарегистрируйтесь на [mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas)
2. Создайте бесплатный кластер
3. Получите строку подключения

### Шаг 3: Клонирование репозитория

```bash
# Клонируйте репозиторий
git clone https://github.com/your-username/fiverr-bot.git
cd fiverr-bot
```

### Шаг 4: Создание виртуального окружения

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Шаг 5: Установка зависимостей

```bash
# Обновите pip
pip install --upgrade pip

# Установите зависимости
pip install -r requirements.txt

# Установите браузер для Playwright
playwright install chromium
```

### Шаг 6: Настройка переменных окружения

**Автоматическая настройка:**
```bash
python setup.py
```

**Ручная настройка:**
```bash
# Скопируйте файл примера
cp env.example .env

# Отредактируйте .env в текстовом редакторе
# Windows: notepad .env
# Linux/Mac: nano .env
```

Заполните следующие переменные:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
MONGODB_URI=mongodb://localhost:27017
EMAIL_API_TOKEN=your_email_api_token
ADMIN_IDS=your_telegram_id
```

### Шаг 7: Получение токенов

**Telegram Bot Token:**
1. Откройте [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Придумайте имя и username бота
4. Скопируйте токен

**Ваш Telegram ID:**
1. Откройте [@userinfobot](https://t.me/userinfobot)
2. Скопируйте ваш ID

**Email API Token:**
1. Зарегистрируйтесь на [anymessage.shop](https://anymessage.shop)
2. Пополните баланс
3. Скопируйте токен из личного кабинета

### Шаг 8: Запуск бота

```bash
# Проверьте, что MongoDB запущена
# Windows: services.msc → MongoDB
# Linux: sudo systemctl status mongod

# Запустите бота
python main.py
```

**Вы должны увидеть:**
```
Запуск Telegram бота...
Успешное подключение к MongoDB: fiverr_bot
Индексы созданы успешно
Бот успешно инициализирован
Бот запущен и готов к работе!
```

### Шаг 9: Проверка работы

1. Откройте вашего бота в Telegram
2. Отправьте `/start`
3. Проверьте баланс: `/balance`
4. Попробуйте зарегистрировать тестовый аккаунт

---

## 2️⃣ Деплой на Railway

### Преимущества Railway
- ✅ Бесплатные $5/месяц
- ✅ Автоматический деплой
- ✅ Встроенная MongoDB
- ✅ SSL сертификаты
- ✅ Логи и мониторинг

### Шаг 1: Подготовка

1. Создайте аккаунт на [railway.app](https://railway.app)
2. Подключите ваш GitHub аккаунт

### Шаг 2: Создание репозитория

```bash
# Инициализируйте Git (если еще не сделано)
git init

# Добавьте все файлы
git add .

# Закоммитьте
git commit -m "Initial commit"

# Создайте репозиторий на GitHub
# Добавьте remote
git remote add origin https://github.com/your-username/fiverr-bot.git

# Запушьте
git push -u origin main
```

### Шаг 3: Создание проекта в Railway

1. **Dashboard → New Project**
2. **Deploy from GitHub repo**
3. Выберите ваш репозиторий
4. Railway начнет деплой

### Шаг 4: Добавление MongoDB

1. В вашем проекте: **New Service**
2. **Database → MongoDB**
3. Railway автоматически создаст базу

### Шаг 5: Настройка переменных

1. Откройте ваш основной сервис
2. **Variables → Add Variable**

Добавьте переменные:
```
TELEGRAM_BOT_TOKEN = ваш_токен_бота
EMAIL_API_TOKEN = ваш_токен_email_api
ADMIN_IDS = ваш_telegram_id
MONGODB_DATABASE = fiverr_bot
LOG_LEVEL = INFO
BROWSER_HEADLESS = true
```

**Важно:** `MONGODB_URI` установится автоматически!

### Шаг 6: Проверка деплоя

1. **Deployments → Latest Deploy**
2. Проверьте статус: должен быть "Success"
3. Откройте **Logs** и убедитесь, что бот запустился

### Шаг 7: Тестирование

1. Откройте бота в Telegram
2. Отправьте `/start`
3. Проверьте `/balance`

### Автоматические обновления

```bash
# Внесите изменения в код
git add .
git commit -m "Update feature"
git push

# Railway автоматически:
# 1. Обнаружит изменения
# 2. Пересоберет образ
# 3. Задеплоит новую версию
```

---

## 3️⃣ Docker установка

### Требования
- Docker
- Docker Compose (опционально)

### Вариант 1: Только Docker

```bash
# Соберите образ
docker build -t fiverr-bot .

# Создайте .env файл
cp env.example .env
# Отредактируйте .env

# Запустите контейнер
docker run -d \
  --name fiverr-bot \
  --env-file .env \
  -v $(pwd)/cookies:/app/cookies \
  -v $(pwd)/logs:/app/logs \
  fiverr-bot
```

### Вариант 2: Docker Compose

Создайте `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: fiverr-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongo-data:/data/db
    environment:
      MONGO_INITDB_DATABASE: fiverr_bot

  bot:
    build: .
    container_name: fiverr-bot
    depends_on:
      - mongodb
    env_file:
      - .env
    environment:
      MONGODB_URI: mongodb://mongodb:27017
    volumes:
      - ./cookies:/app/cookies
      - ./logs:/app/logs
    restart: unless-stopped

volumes:
  mongo-data:
```

Запустите:
```bash
docker-compose up -d
```

---

## ✅ Проверка установки

### Тест 1: Проверка зависимостей

```bash
python -c "import telegram; print('✅ python-telegram-bot')"
python -c "import playwright; print('✅ Playwright')"
python -c "import motor; print('✅ Motor')"
python -c "import aiohttp; print('✅ aiohttp')"
```

### Тест 2: Проверка MongoDB

```bash
# Локально
mongo --eval "db.stats()"

# MongoDB Atlas
mongosh "your-connection-string" --eval "db.stats()"
```

### Тест 3: Проверка Email API

```bash
python tests/test_email_api.py
```

### Тест 4: Проверка прокси

```bash
python tests/test_proxy.py
```

---

## 🐛 Решение проблем

### Проблема: Python не найден

**Решение:**
```bash
# Проверьте установку
python --version
python3 --version

# Добавьте в PATH (Windows)
setx PATH "%PATH%;C:\Python311"

# Или используйте полный путь
C:\Python311\python.exe main.py
```

### Проблема: MongoDB не запускается

**Windows:**
```powershell
# Запустите как администратор
net start MongoDB
```

**Linux:**
```bash
sudo systemctl start mongod
sudo systemctl status mongod
```

### Проблема: Playwright не установился

```bash
# Переустановите
pip uninstall playwright
pip install playwright==1.40.0
playwright install chromium

# Linux: установите зависимости
sudo playwright install-deps chromium
```

### Проблема: "Permission denied" при запуске

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

### Проблема: Порт 27017 занят

```bash
# Проверьте, что использует порт
# Windows
netstat -ano | findstr :27017

# Linux/macOS
lsof -i :27017

# Измените порт в .env
MONGODB_URI=mongodb://localhost:27018
```

---

## 📚 Следующие шаги

После успешной установки:

1. ✅ Прочитайте [README.md](README.md)
2. ✅ Изучите [FAQ.md](FAQ.md)
3. ✅ Попробуйте [примеры](EXAMPLES.md)
4. ✅ Зарегистрируйте первый тестовый аккаунт

---

## 💡 Полезные советы

### Автозапуск при старте системы

**Windows (Task Scheduler):**
1. Создайте задачу в планировщике
2. Триггер: При входе в систему
3. Действие: Запустить `start.bat`

**Linux (systemd):**
```bash
# Создайте сервис
sudo nano /etc/systemd/system/fiverr-bot.service

[Unit]
Description=Fiverr Bot
After=network.target mongodb.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/fiverr-bot
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target

# Активируйте
sudo systemctl enable fiverr-bot
sudo systemctl start fiverr-bot
```

### Обновление зависимостей

```bash
# Обновите все пакеты
pip install --upgrade -r requirements.txt

# Обновите Playwright
playwright install chromium
```

### Backup базы данных

```bash
# Экспорт
mongodump --db fiverr_bot --out backup/

# Импорт
mongorestore --db fiverr_bot backup/fiverr_bot/
```

---

**Готово! Бот установлен и готов к работе! 🎉**

Если возникли проблемы, проверьте:
- [FAQ](FAQ.md) - частые вопросы
- [Issues на GitHub](../../issues) - известные проблемы
- Логи в `logs/` директории

