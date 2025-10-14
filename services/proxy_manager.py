"""
Модуль для работы с прокси-серверами
"""
import aiohttp
from typing import Optional, Dict
from dataclasses import dataclass
from utils.logger import logger


@dataclass
class ProxyConfig:
    """Класс для хранения конфигурации прокси"""
    username: str
    password: str
    host: str
    port: int
    
    @classmethod
    def from_string(cls, proxy_string: str) -> Optional['ProxyConfig']:
        """
        Создание конфигурации прокси из строки формата username:password@host:port
        
        Args:
            proxy_string: Строка с прокси в формате username:password@host:port
            
        Returns:
            Объект ProxyConfig или None в случае ошибки
        """
        try:
            # Разбираем строку формата username:password@host:port
            auth_part, server_part = proxy_string.split('@')
            username, password = auth_part.split(':')
            host, port = server_part.split(':')
            
            return cls(
                username=username.strip(),
                password=password.strip(),
                host=host.strip(),
                port=int(port.strip())
            )
        except Exception as e:
            logger.error(f"Ошибка парсинга прокси '{proxy_string}': {e}")
            return None
    
    def to_playwright_format(self) -> Dict[str, str]:
        """
        Конвертация в формат для Playwright
        
        Returns:
            Словарь с настройками прокси для Playwright
        """
        return {
            "server": f"http://{self.host}:{self.port}",
            "username": self.username,
            "password": self.password
        }
    
    def to_url(self) -> str:
        """
        Конвертация в URL формат
        
        Returns:
            Строка с прокси в URL формате
        """
        return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
    
    def __str__(self) -> str:
        """Строковое представление"""
        return f"{self.username}:***@{self.host}:{self.port}"


class ProxyManager:
    """Менеджер для работы с прокси"""
    
    @staticmethod
    async def check_proxy(proxy: ProxyConfig, timeout: int = 10) -> bool:
        """
        Проверка работоспособности прокси
        
        Args:
            proxy: Конфигурация прокси
            timeout: Таймаут проверки в секундах
            
        Returns:
            True если прокси работает, False иначе
        """
        test_url = "https://api.ipify.org?format=json"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    test_url,
                    proxy=proxy.to_url(),
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        ip = data.get('ip')
                        logger.info(f"Прокси {proxy} работает. IP: {ip}")
                        return True
                    else:
                        logger.warning(f"Прокси {proxy} вернул статус {response.status}")
                        return False
        except asyncio.TimeoutError:
            logger.error(f"Таймаут при проверке прокси {proxy}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке прокси {proxy}: {e}")
            return False
    
    @staticmethod
    async def get_proxy_ip(proxy: ProxyConfig) -> Optional[str]:
        """
        Получение IP адреса прокси
        
        Args:
            proxy: Конфигурация прокси
            
        Returns:
            IP адрес или None в случае ошибки
        """
        test_url = "https://api.ipify.org?format=json"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    test_url,
                    proxy=proxy.to_url(),
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('ip')
        except Exception as e:
            logger.error(f"Ошибка получения IP прокси {proxy}: {e}")
        
        return None


# Импорт для исправления ошибки asyncio
import asyncio

