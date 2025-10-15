"""
Модуль для работы с API сервиса покупки почт (anymessage.shop)
"""
import asyncio
from typing import Optional, Dict, Any
import aiohttp
from utils.logger import logger
from config import EMAIL_API_TOKEN, EMAIL_API_BASE_URL, FIVERR_SITE


class EmailAPIService:
    """Сервис для работы с API покупки временных почт"""
    
    def __init__(self, token: str = EMAIL_API_TOKEN):
        self.token = token
        self.base_url = EMAIL_API_BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Инициализация асинхронного контекстного менеджера"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнение HTTP запроса к API
        
        Args:
            endpoint: Конечная точка API
            params: Параметры запроса
            
        Returns:
            Словарь с результатом запроса
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}{endpoint}"
        params['token'] = self.token
        
        try:
            async with self.session.get(url, params=params, timeout=30) as response:
                data = await response.json()
                logger.debug(f"API ответ от {endpoint}: {data}")
                return data
        except asyncio.TimeoutError:
            logger.error(f"Таймаут при запросе к {endpoint}")
            return {"status": "error", "value": "timeout"}
        except Exception as e:
            logger.error(f"Ошибка при запросе к {endpoint}: {e}")
            return {"status": "error", "value": str(e)}
    
    async def get_balance(self) -> Optional[float]:
        """
        Получение баланса аккаунта
        
        Returns:
            Баланс в виде числа или None в случае ошибки
        """
        data = await self._make_request("/user/balance", {})
        
        if data.get("status") == "success":
            balance = float(data.get("balance", 0))
            logger.info(f"Баланс аккаунта: {balance}")
            return balance
        else:
            logger.error(f"Ошибка получения баланса: {data.get('value')}")
            return None
    
    async def get_available_emails(self, site: str = FIVERR_SITE) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Получение списка доступных почтовых доменов для сайта
        
        Args:
            site: Название сайта (по умолчанию fiverr.com)
            
        Returns:
            Словарь с доступными доменами и их параметрами
        """
        data = await self._make_request("/email/quantity", {"site": site})
        
        if data.get("status") == "success":
            domains_data = data.get("data", {})
            logger.info(f"Доступные домены для {site}: {list(domains_data.keys())}")
            return domains_data
        else:
            logger.error(f"Ошибка получения списка почт: {data.get('value')}")
            return None
    
    async def get_available_domains(self, site: str = FIVERR_SITE) -> Optional[Dict[str, Any]]:
        """
        Получение списка доступных доменов для сайта (упрощенная версия)
        
        Args:
            site: Название сайта (по умолчанию fiverr.com)
            
        Returns:
            Словарь с результатом и списком доменов
        """
        data = await self._make_request("/email/quantity", {"site": site})
        
        if data.get("status") == "success":
            domains_data = data.get("data", {})
            domains_list = list(domains_data.keys())
            logger.info(f"Доступные домены для {site}: {domains_list}")
            return {
                "status": "success",
                "data": domains_list
            }
        else:
            logger.error(f"Ошибка получения доменов: {data.get('value')}")
            return {
                "status": "error",
                "value": data.get('value', 'Unknown error')
            }
    
    async def order_email(
        self, 
        site: str = FIVERR_SITE,
        domain: str = "gmx.com",
        regex: Optional[str] = None,
        subject: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Заказ почты для регистрации
        
        Args:
            site: Название сайта
            domain: Почтовый домен
            regex: Регулярное выражение для парсинга (опционально)
            subject: Тема письма для поиска (опционально)
            
        Returns:
            Словарь с id активации и email адресом
        """
        params = {
            "site": site,
            "domain": domain
        }
        
        if regex:
            params["regex"] = regex
        if subject:
            params["subject"] = subject
        
        data = await self._make_request("/email/order", params)
        
        if data.get("status") == "success":
            result = {
                "id": data.get("id"),
                "email": data.get("email")
            }
            logger.info(f"Заказана почта: {result['email']} (ID: {result['id']})")
            return result
        else:
            error = data.get("value")
            logger.error(f"Ошибка заказа почты: {error}")
            return None
    
    async def get_message(
        self, 
        activation_id: str,
        preview: bool = False,
        max_retries: int = 60,
        retry_interval: int = 5
    ) -> Optional[Dict[str, str]]:
        """
        Получение сообщения из почты
        
        Args:
            activation_id: ID активации
            preview: Получить HTML версию письма
            max_retries: Максимальное количество попыток
            retry_interval: Интервал между попытками в секундах
            
        Returns:
            Словарь с кодом подтверждения и сообщением
        """
        params = {
            "id": activation_id
        }
        
        if preview:
            params["preview"] = "1"
        
        for attempt in range(max_retries):
            data = await self._make_request("/email/getmessage", params)
            
            # ЛОГИРУЕМ ПОЛНЫЙ ОТВЕТ для debug
            if attempt % 6 == 0:  # Каждые 30 секунд (6 * 5 сек)
                logger.info(f"Попытка {attempt + 1}/{max_retries} - Ответ API: {data}")
            
            if data.get("status") == "success":
                result = {
                    "value": data.get("value"),
                    "message": data.get("message", "")
                }
                logger.info(f"✅ Получено сообщение для активации {activation_id}: код={result['value']}")
                return result
            elif data.get("status") == "error" and data.get("value") == "wait message":
                logger.debug(f"⏳ Ожидание письма... Попытка {attempt + 1}/{max_retries}")
                await asyncio.sleep(retry_interval)
            else:
                logger.error(f"❌ Неожиданный ответ API: {data}")
                # Не прерываем - продолжаем ждать
                await asyncio.sleep(retry_interval)
        
        logger.error(f"❌ Письмо не пришло после {max_retries} попыток (3 минуты)")
        return None
    
    async def reorder_email(
        self,
        activation_id: Optional[str] = None,
        email: Optional[str] = None,
        site: str = FIVERR_SITE,
        regex: Optional[str] = None,
        subject: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Повторный заказ почты
        
        Args:
            activation_id: ID активации (если известен)
            email: Email адрес (альтернатива activation_id)
            site: Название сайта
            regex: Регулярное выражение для парсинга
            subject: Тема письма
            
        Returns:
            Словарь с новым id активации и email
        """
        params = {}
        
        if activation_id:
            params["id"] = activation_id
        elif email:
            params["email"] = email
            params["site"] = site
        else:
            logger.error("Необходимо указать либо activation_id, либо email")
            return None
        
        if regex:
            params["regex"] = regex
        if subject:
            params["subject"] = subject
        
        data = await self._make_request("/email/reorder", params)
        
        if data.get("status") == "success":
            result = {
                "id": data.get("id"),
                "email": data.get("email")
            }
            logger.info(f"Повторно заказана почта: {result['email']} (ID: {result['id']})")
            return result
        else:
            logger.error(f"Ошибка повторного заказа: {data.get('value')}")
            return None
    
    async def cancel_email(self, activation_id: str) -> bool:
        """
        Отмена активации почты
        
        Args:
            activation_id: ID активации
            
        Returns:
            True если успешно, False иначе
        """
        data = await self._make_request("/email/cancel", {"id": activation_id})
        
        if data.get("status") == "success":
            logger.info(f"Активация {activation_id} отменена")
            return True
        else:
            logger.error(f"Ошибка отмены активации: {data.get('value')}")
            return False

