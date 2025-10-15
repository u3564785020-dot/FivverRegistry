"""
Главный файл запуска Telegram бота
"""
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)
from utils.logger import logger
from config import TELEGRAM_BOT_TOKEN
from services.database import db
from bot.handlers import (
    start_command,
    help_command,
    proxy_toggle_command,
    balance_command,
    register_command,
    tasks_command,
    accounts_command,
    handle_message,
    error_handler
)


async def post_init(application: Application):
    """Инициализация после запуска бота"""
    logger.info("Инициализация бота...")
    
    # Подключаемся к базе данных
    await db.connect()
    
    logger.info("Бот успешно инициализирован")


async def post_shutdown(application: Application):
    """Очистка перед остановкой бота"""
    logger.info("Остановка бота...")
    
    # Отключаемся от базы данных
    await db.disconnect()
    
    logger.info("Бот остановлен")


def main():
    """Главная функция"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен в переменных окружения!")
        return
    
    logger.info("Запуск Telegram бота...")
    
    # Создаем приложение
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("proxy_toggle", proxy_toggle_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("register", register_command))
    application.add_handler(CommandHandler("tasks", tasks_command))
    application.add_handler(CommandHandler("accounts", accounts_command))
    
    # Обработчик текстовых сообщений
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()

