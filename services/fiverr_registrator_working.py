#!/usr/bin/env python3
"""
РАБОЧИЙ РЕГИСТРАТОР FIVERR НА ОСНОВЕ РЕАЛЬНЫХ ДАННЫХ
Создан на основе анализа реального процесса регистрации
"""

import asyncio
import aiohttp
import random
import string
import re
from typing import Optional, Dict, Any
import logging
logger = logging.getLogger(__name__)
from services.email_api import EmailAPIService
from services.proxy_manager import ProxyConfig

class FiverrWorkingRegistrator:
    def __init__(self, proxy: Optional[ProxyConfig] = None):
        self.proxy = proxy
        self.session = None
        self.csrf_token = None
        self.cookies = {}
        
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        connector = None
        if self.proxy:
            connector = aiohttp.TCPConnector()
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        if self.session:
            await self.session.close()
    
    async def _get_csrf_token(self) -> Optional[str]:
        """Получение CSRF токена с главной страницы"""
        try:
            # Сначала получаем главную страницу
            url = "https://it.fiverr.com/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'it,it-IT;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Not:A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Ищем CSRF токен в HTML
                    csrf_patterns = [
                        r'name="csrf_token"\s+value="([^"]+)"',
                        r'name="_token"\s+value="([^"]+)"',
                        r'name="authenticity_token"\s+value="([^"]+)"',
                        r'"csrf_token":"([^"]+)"',
                        r'"csrfToken":"([^"]+)"',
                        r'"authenticity_token":"([^"]+)"',
                        r'window\.csrf_token\s*=\s*["\']([^"\']+)["\']',
                        r'window\._token\s*=\s*["\']([^"\']+)["\']',
                        r'<meta name="csrf-token" content="([^"]+)"',
                        r'<meta name="_token" content="([^"]+)"'
                    ]
                    
                    for pattern in csrf_patterns:
                        match = re.search(pattern, html)
                        if match:
                            self.csrf_token = match.group(1)
                            logger.info(f"CSRF токен найден: {self.csrf_token[:20]}...")
                            return self.csrf_token
                    
                    # Если не нашли в HTML, пробуем получить через API
                    return await self._get_csrf_from_api()
                else:
                    logger.error(f"Ошибка получения главной страницы: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка получения CSRF токена: {e}")
            return None
    
    async def _get_csrf_from_api(self) -> Optional[str]:
        """Получение CSRF токена через API"""
        try:
            # Пробуем разные API эндпоинты для получения CSRF
            api_urls = [
                "https://it.fiverr.com/api/v1/auth/csrf",
                "https://it.fiverr.com/api/v1/csrf",
                "https://it.fiverr.com/csrf",
                "https://it.fiverr.com/api/csrf"
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'it,it-IT;q=0.9,en-US;q=0.8,en;q=0.7',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'https://it.fiverr.com',
                'Referer': 'https://it.fiverr.com/'
            }
            
            for url in api_urls:
                try:
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'csrf_token' in data:
                                self.csrf_token = data['csrf_token']
                                logger.info(f"CSRF токен получен через API: {self.csrf_token[:20]}...")
                                return self.csrf_token
                            elif 'token' in data:
                                self.csrf_token = data['token']
                                logger.info(f"CSRF токен получен через API: {self.csrf_token[:20]}...")
                                return self.csrf_token
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения CSRF через API: {e}")
            return None
    
    def _generate_username(self) -> str:
        """Генерация случайного имени пользователя в формате text_text"""
        # Генерируем два слова по 4-8 символов каждое
        word1 = ''.join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
        word2 = ''.join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
        return f"{word1}_{word2}"
    
    def _generate_password(self) -> str:
        """Генерация надежного пароля"""
        # Минимум 8 символов, включая заглавные, строчные буквы и цифры
        length = random.randint(8, 12)
        
        # Обязательные символы
        uppercase = random.choice(string.ascii_uppercase)
        lowercase = random.choice(string.ascii_lowercase)
        digit = random.choice(string.digits)
        
        # Остальные символы
        remaining = ''.join(random.choices(
            string.ascii_letters + string.digits,
            k=length - 3
        ))
        
        # Смешиваем все символы
        password = list(uppercase + lowercase + digit + remaining)
        random.shuffle(password)
        
        return ''.join(password)
    
    async def _check_username_availability(self, username: str) -> bool:
        """Проверка доступности имени пользователя"""
        try:
            url = "https://it.fiverr.com/api/v1/users/validate_username"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'it,it-IT;q=0.9,en-US;q=0.8,en;q=0.7',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'https://it.fiverr.com',
                'Referer': 'https://it.fiverr.com/',
                'Content-Type': 'application/json'
            }
            
            data = {'username': username}
            
            async with self.session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    # Если username доступен, сервер должен вернуть success: true
                    return result.get('available', False)
                return False
                
        except Exception as e:
            logger.error(f"Ошибка проверки username: {e}")
            return False
    
    async def _send_confirmation_code(self, email: str) -> bool:
        """Отправка кода подтверждения на email"""
        try:
            url = "https://it.fiverr.com/api/v1/users/send_confirmation"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'it,it-IT;q=0.9,en-US;q=0.8,en;q=0.7',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'https://it.fiverr.com',
                'Referer': 'https://it.fiverr.com/',
                'Content-Type': 'application/json'
            }
            
            data = {'email': email}
            
            async with self.session.post(url, json=data, headers=headers) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Ошибка отправки кода подтверждения: {e}")
            return False
    
    async def register_account(self, email: str, email_service: EmailAPIService, email_id: str = None) -> Dict[str, Any]:
        """Регистрация аккаунта на основе реальных данных"""
        try:
            logger.info(f"Начинаем регистрацию аккаунта с email: {email}")
            
            # Получаем CSRF токен
            csrf_token = await self._get_csrf_token()
            if not csrf_token:
                logger.warning("CSRF токен не найден, продолжаем без него")
            
            # Генерируем username и проверяем доступность
            username = self._generate_username()
            max_attempts = 5
            attempts = 0
            
            while attempts < max_attempts:
                if await self._check_username_availability(username):
                    logger.info(f"Username {username} доступен")
                    break
                else:
                    logger.info(f"Username {username} занят, генерируем новый")
                    username = self._generate_username()
                    attempts += 1
            
            if attempts >= max_attempts:
                logger.warning("Не удалось найти доступный username")
                return {"success": False, "error": "Username недоступен"}
            
            # Генерируем пароль
            password = self._generate_password()
            logger.info(f"Сгенерирован пароль: {password}")
            
            # Подготавливаем данные для регистрации
            registration_data = {
                'user[email]': email,
                'user[password]': password,
                'user[username]': username,
                'funnel': 'standard'
            }
            
            # Подготавливаем заголовки
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'it,it-IT;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Content-Type': 'multipart/form-data',
                'Origin': 'https://it.fiverr.com',
                'Referer': 'https://it.fiverr.com/login?source=top_nav',
                'X-Requested-With': 'XMLHttpRequest',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Priority': 'u=1, i'
            }
            
            # Добавляем CSRF токен если есть
            if csrf_token:
                headers['X-Csrf-Token'] = csrf_token
            
            # URL для регистрации
            url = "https://it.fiverr.com/users"
            
            # Создаем FormData для multipart/form-data
            form_data = aiohttp.FormData()
            for key, value in registration_data.items():
                form_data.add_field(key, str(value))
            
            # Выполняем запрос регистрации
            async with self.session.post(url, data=form_data, headers=headers) as response:
                response_text = await response.text()
                logger.info(f"Ответ сервера: {response.status}")
                logger.info(f"Тело ответа: {response_text[:200]}...")
                
                if response.status == 200:
                    try:
                        response_data = await response.json()
                        logger.info("Регистрация успешна!")
                        
                        # Сохраняем cookies
                        for cookie in response.cookies:
                            self.cookies[cookie.key] = cookie.value
                        
                        # Если нужен код подтверждения, получаем его
                        confirmation_code = None
                        if email_id and email_service:
                            logger.info("Получаем код подтверждения...")
                            confirmation_result = await email_service.get_message(email_id)
                            if confirmation_result["success"]:
                                confirmation_code = confirmation_result.get("code")
                                logger.info(f"Код подтверждения получен: {confirmation_code}")
                            else:
                                logger.warning("Не удалось получить код подтверждения")
                        
                        return {
                            "success": True,
                            "email": email,
                            "username": username,
                            "password": password,
                            "cookies": dict(self.cookies),
                            "confirmation_code": confirmation_code,
                            "response": response_data
                        }
                    except:
                        # Если ответ не JSON, но статус 200
                        logger.info("Регистрация успешна (не JSON ответ)")
                        
                        # Если нужен код подтверждения, получаем его
                        confirmation_code = None
                        if email_id and email_service:
                            logger.info("Получаем код подтверждения...")
                            confirmation_result = await email_service.get_message(email_id)
                            if confirmation_result["success"]:
                                confirmation_code = confirmation_result.get("code")
                                logger.info(f"Код подтверждения получен: {confirmation_code}")
                        
                        return {
                            "success": True,
                            "email": email,
                            "username": username,
                            "password": password,
                            "cookies": dict(self.cookies),
                            "confirmation_code": confirmation_code,
                            "response": response_text
                        }
                else:
                    logger.error(f"Ошибка регистрации: {response.status}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "response": response_text
                    }
                    
        except Exception as e:
            logger.error(f"Критическая ошибка при регистрации: {e}")
            return {"success": False, "error": str(e)}

async def register_accounts_batch(
    email_service: EmailAPIService,
    count: int,
    proxy: Optional[ProxyConfig] = None
) -> list:
    """Пакетная регистрация аккаунтов"""
    results = []
    
    async with FiverrWorkingRegistrator(proxy) as registrator:
        for i in range(count):
            try:
                logger.info(f"Регистрация аккаунта {i+1}/{count}")
                
                # Заказываем email
                email_result = await email_service.order_email("fiverr.com")
                logger.info(f"Результат заказа email: {type(email_result)} - {email_result}")
                
                if not isinstance(email_result, dict) or not email_result.get("success"):
                    error_msg = email_result.get('error', 'Неизвестная ошибка') if isinstance(email_result, dict) else str(email_result)
                    logger.error(f"Не удалось заказать email: {error_msg}")
                    results.append({
                        "success": False,
                        "error": f"Ошибка заказа email: {error_msg}"
                    })
                    continue
                
                if "email" not in email_result:
                    logger.error(f"Email не найден в результате: {email_result}")
                    results.append({
                        "success": False,
                        "error": "Email не найден в результате заказа"
                    })
                    continue
                
                email = email_result["email"]
                logger.info(f"Получен email: {email}")
                
                # Регистрируем аккаунт
                logger.info(f"Начинаем регистрацию аккаунта {i+1}...")
                result = await registrator.register_account(email, email_service, email_result.get("id"))
                logger.info(f"Результат регистрации: {type(result)} - {result}")
                results.append(result)
                
                if isinstance(result, dict) and result.get("success"):
                    logger.info(f"✅ Аккаунт {i+1} зарегистрирован успешно!")
                else:
                    error_msg = result.get('error', 'Неизвестная ошибка') if isinstance(result, dict) else str(result)
                    logger.error(f"❌ Ошибка регистрации аккаунта {i+1}: {error_msg}")
                
            except Exception as e:
                logger.error(f"❌ Критическая ошибка при регистрации аккаунта {i+1}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                results.append({
                    "success": False,
                    "error": str(e)
                })
    
    return results
