#!/bin/bash

# Скрипт для быстрого запуска бота (Linux/Mac)

echo "=================================="
echo "🚀 Запуск Fiverr Bot"
echo "=================================="

# Проверка .env файла
if [ ! -f .env ]; then
    echo "⚠️  .env файл не найден!"
    echo "Запустите: python setup.py"
    exit 1
fi

# Проверка зависимостей
echo "📦 Проверка зависимостей..."
pip install -r requirements.txt --quiet

# Проверка Playwright
if ! command -v playwright &> /dev/null; then
    echo "📥 Установка Playwright..."
    playwright install chromium
fi

# Запуск бота
echo "✅ Запуск бота..."
python main.py

