"""
Конфигурация для бота регистрации аккаунтов Fiverr
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).parent
COOKIES_DIR = BASE_DIR / "cookies"
LOGS_DIR = BASE_DIR / "logs"

# Создаем необходимые директории
COOKIES_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

# MongoDB Configuration
# Railway автоматически создает MONGO_URL, используем её если MONGODB_URI не установлена
MONGODB_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "fiverr_bot")

# Email API Configuration
EMAIL_API_TOKEN = os.getenv("EMAIL_API_TOKEN", "O8M7ZEw5F9RogIp2TEW6c7WaZyMOz9Z3")
EMAIL_API_BASE_URL = os.getenv("EMAIL_API_BASE_URL", "https://api.anymessage.shop")

# Fiverr Configuration
FIVERR_SITE = os.getenv("FIVERR_SITE", "fiverr.com")
FIVERR_URL = "https://www.fiverr.com"
FIVERR_SIGNUP_URL = f"{FIVERR_URL}/join"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Browser Configuration
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "60000"))  # milliseconds

# Registration Settings
MAX_CONCURRENT_REGISTRATIONS = int(os.getenv("MAX_CONCURRENT_REGISTRATIONS", "5"))
REGISTRATION_TIMEOUT = int(os.getenv("REGISTRATION_TIMEOUT", "300"))  # seconds

