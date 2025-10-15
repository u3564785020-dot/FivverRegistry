"""
Модуль для настройки логирования
"""
import sys
import logging

# Настраиваем базовое логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

__all__ = ["logger"]