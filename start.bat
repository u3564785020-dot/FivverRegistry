@echo off
REM Скрипт для быстрого запуска бота (Windows)

echo ==================================
echo 🚀 Запуск Fiverr Bot
echo ==================================

REM Проверка .env файла
if not exist .env (
    echo ⚠️  .env файл не найден!
    echo Запустите: python setup.py
    pause
    exit /b 1
)

REM Проверка зависимостей
echo 📦 Проверка зависимостей...
pip install -r requirements.txt --quiet

REM Запуск бота
echo ✅ Запуск бота...
python main.py

pause

