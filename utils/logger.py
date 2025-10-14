"""
Модуль для настройки логирования
"""
import sys
from loguru import logger
from config import LOGS_DIR, LOG_LEVEL

# Удаляем стандартный обработчик
logger.remove()

# Добавляем обработчик для консоли
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=LOG_LEVEL,
    colorize=True
)

# Добавляем обработчик для файла
logger.add(
    LOGS_DIR / "bot_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=LOG_LEVEL,
    rotation="00:00",  # Новый файл каждый день
    retention="30 days",  # Хранить логи 30 дней
    compression="zip"  # Сжимать старые логи
)

# Добавляем обработчик для ошибок
logger.add(
    LOGS_DIR / "errors_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="00:00",
    retention="60 days",
    compression="zip"
)

__all__ = ["logger"]

