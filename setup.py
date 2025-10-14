"""
Скрипт для быстрой настройки проекта
"""
import os
import sys
from pathlib import Path


def create_env_file():
    """Создание .env файла из примера"""
    env_example = Path("env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        response = input(".env файл уже существует. Перезаписать? (y/n): ")
        if response.lower() != 'y':
            print("Пропуск создания .env файла")
            return
    
    if not env_example.exists():
        print("❌ env.example не найден!")
        return
    
    # Копируем содержимое
    with open(env_example, 'r') as f:
        content = f.read()
    
    print("\n📝 Настройка переменных окружения\n")
    
    # Запрашиваем значения
    bot_token = input("Введите TELEGRAM_BOT_TOKEN: ").strip()
    admin_ids = input("Введите ваш Telegram ID (ADMIN_IDS): ").strip()
    mongodb_uri = input("Введите MONGODB_URI (Enter для localhost): ").strip() or "mongodb://localhost:27017"
    email_token = input("Введите EMAIL_API_TOKEN (Enter для дефолтного): ").strip() or "O8M7ZEw5F9RogIp2TEW6c7WaZyMOz9Z3"
    
    # Заменяем значения
    content = content.replace("your_telegram_bot_token_here", bot_token)
    content = content.replace("123456789", admin_ids)
    content = content.replace("mongodb://localhost:27017", mongodb_uri)
    content = content.replace("O8M7ZEw5F9RogIp2TEW6c7WaZyMOz9Z3", email_token)
    
    # Сохраняем
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("\n✅ .env файл создан успешно!")


def create_directories():
    """Создание необходимых директорий"""
    directories = ['cookies', 'logs', 'temp']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Директория {directory}/ создана")


def check_dependencies():
    """Проверка установленных зависимостей"""
    print("\n🔍 Проверка зависимостей...\n")
    
    required_packages = [
        'telegram',
        'playwright',
        'motor',
        'dotenv',
        'aiohttp',
        'loguru'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package if package != 'dotenv' else 'dotenv')
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Отсутствующие пакеты: {', '.join(missing_packages)}")
        print("Установите их командой: pip install -r requirements.txt")
        return False
    
    print("\n✅ Все зависимости установлены!")
    return True


def install_playwright():
    """Установка браузеров Playwright"""
    response = input("\n🌐 Установить браузеры Playwright? (y/n): ")
    if response.lower() == 'y':
        print("Установка Chromium для Playwright...")
        os.system("playwright install chromium")
        print("✅ Playwright настроен!")


def main():
    """Главная функция"""
    print("=" * 50)
    print("🚀 Настройка Fiverr Bot")
    print("=" * 50)
    
    # Создаем директории
    print("\n1️⃣ Создание директорий...")
    create_directories()
    
    # Создаем .env файл
    print("\n2️⃣ Настройка переменных окружения...")
    create_env_file()
    
    # Проверяем зависимости
    print("\n3️⃣ Проверка зависимостей...")
    if not check_dependencies():
        sys.exit(1)
    
    # Устанавливаем Playwright
    print("\n4️⃣ Настройка Playwright...")
    install_playwright()
    
    print("\n" + "=" * 50)
    print("✅ Настройка завершена!")
    print("=" * 50)
    print("\n📚 Следующие шаги:")
    print("1. Проверьте файл .env")
    print("2. Убедитесь, что MongoDB запущена")
    print("3. Запустите бота: python main.py")
    print("\n💡 Подробная документация в README.md")


if __name__ == "__main__":
    main()

