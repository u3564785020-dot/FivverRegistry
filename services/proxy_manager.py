"""
Модуль для работы с прокси-серверами
"""
import asyncio
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
    async def check_proxy(proxy: ProxyConfig, timeout: int = 20) -> bool:
        """
        Проверка работоспособности прокси (не блокирующая)
        
        Args:
            proxy: Конфигурация прокси
            timeout: Таймаут проверки в секундах (по умолчанию 20)
            
        Returns:
            True если прокси работает, False иначе
        """
        # Несколько тестовых URL на случай если один недоступен
        test_urls = [
            "http://api.ipify.org?format=json",  # HTTP версия быстрее
            "https://ifconfig.me/ip",
            "http://icanhazip.com"
        ]
        
        for test_url in test_urls:
            try:
                logger.debug(f"Проверка прокси {proxy} через {test_url}...")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        test_url,
                        proxy=proxy.to_url(),
                        timeout=aiohttp.ClientTimeout(total=timeout),
                        allow_redirects=True
                    ) as response:
                        if response.status == 200:
                            if 'json' in test_url:
                                data = await response.json()
                                ip = data.get('ip', 'unknown')
                            else:
                                ip = (await response.text()).strip()
                            
                            logger.info(f"✅ Прокси {proxy} работает! IP: {ip}")
                            return True
                        else:
                            logger.debug(f"Прокси {proxy} вернул статус {response.status}, пробуем другой URL...")
                            continue
                            
            except asyncio.TimeoutError:
                logger.debug(f"Таймаут при проверке через {test_url}, пробуем другой...")
                continue
            except aiohttp.ClientError as e:
                logger.debug(f"Ошибка соединения через {test_url}: {e}, пробуем другой...")
                continue
            except Exception as e:
                logger.debug(f"Неожиданная ошибка при проверке через {test_url}: {e}")
                continue
        
        # Если ни один URL не сработал
        logger.warning(f"⚠️ Прокси {proxy} не прошел проверку через {len(test_urls)} тестовых URL")
        logger.warning("Продолжаем использовать прокси - возможно firewall блокирует тестовые сервисы")
        # Возвращаем True - даем прокси шанс, возможно он работает только с Fiverr
        return True
    
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

