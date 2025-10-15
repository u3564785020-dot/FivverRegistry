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
    def __init__(self, proxy: Optional[ProxyConfig] = None, use_proxy: bool = True):
        self.proxy = proxy
        self.use_proxy = use_proxy
        self.session = None
        self.csrf_token = None
        self.cookies = {}
        
        # Список реалистичных User-Agent
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"
        ]
    
    def _get_random_user_agent(self) -> str:
        """Получить случайный User-Agent"""
        return random.choice(self.user_agents)
        
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        connector = None
        if self.proxy and self.use_proxy:
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
                'User-Agent': self._get_random_user_agent(),
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
                'User-Agent': self._get_random_user_agent(),
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
        """Проверка доступности имени пользователя - упрощенная версия"""
        # Пропускаем проверку через API, так как она может не работать
        # Fiverr сам проверит доступность при регистрации
        return True
    
    async def _send_confirmation_code(self, email: str) -> bool:
        """Отправка кода подтверждения на email"""
        try:
            url = "https://it.fiverr.com/api/v1/users/send_confirmation"
            headers = {
                'User-Agent': self._get_random_user_agent(),
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
            
            # Получаем CSRF токен и cookies
            csrf_token = await self._get_csrf_token()
            if not csrf_token:
                logger.warning("CSRF токен не найден, продолжаем без него")
            
            # Добавляем дополнительные cookies для имитации реального браузера
            additional_cookies = {
                '_pxvid': f'px_{random.randint(100000, 999999)}',
                '_pxff': f'{random.randint(100000, 999999)}',
                '_px3': f'{random.randint(100000, 999999)}',
                'pxvid': f'px_{random.randint(100000, 999999)}',
                'pxff': f'{random.randint(100000, 999999)}',
                'px3': f'{random.randint(100000, 999999)}',
                'sessionid': f'session_{random.randint(100000, 999999)}',
                'csrftoken': csrf_token if csrf_token else f'token_{random.randint(100000, 999999)}'
            }
            
            # Обновляем cookies
            self.cookies.update(additional_cookies)
            
            # Генерируем username и проверяем доступность
            # Генерируем username (без проверки доступности)
            username = self._generate_username()
            logger.info(f"Сгенерирован username: {username}")
            
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
            
            # Подготавливаем заголовки (улучшенные для обхода PerimeterX)
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9,it;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW',
                'Origin': 'https://it.fiverr.com',
                'Referer': 'https://it.fiverr.com/',
                'X-Requested-With': 'XMLHttpRequest',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Priority': 'u=1, i',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Ch-Ua': '"Not:A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'DNT': '1',
                'Connection': 'keep-alive'
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
            
            # Добавляем задержку для имитации человеческого поведения
            await asyncio.sleep(random.uniform(1, 3))
            
            # Выполняем запрос регистрации
            proxy_url = self.proxy.to_url() if (self.proxy and self.use_proxy) else None
            async with self.session.post(url, data=form_data, headers=headers, proxy=proxy_url) as response:
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
                            if confirmation_result and confirmation_result.get("value"):
                                confirmation_code = confirmation_result.get("value")
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
                            if confirmation_result and confirmation_result.get("value"):
                                confirmation_code = confirmation_result.get("value")
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
                elif response.status == 403 and "px-captcha" in response_text:
                    logger.warning("Обнаружена капча PerimeterX - HTTP регистрация заблокирована")
                    return {
                        "success": False,
                        "error": "❌ Обнаружена защита PerimeterX (капча). HTTP регистрация заблокирована. Попробуйте:\n• Использовать другой прокси\n• Повторить через несколько минут\n• Использовать VPN",
                        "method": "http_blocked"
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
    proxy: Optional[ProxyConfig] = None,
    use_proxy: bool = True
) -> list:
    """Пакетная регистрация аккаунтов"""
    results = []
    
    async with FiverrWorkingRegistrator(proxy, use_proxy) as registrator:
        for i in range(count):
            try:
                logger.info(f"Регистрация аккаунта {i+1}/{count}")
                
                # Получаем доступные домены и выбираем первый доступный
                available_domains = await email_service.get_available_emails("fiverr.com")
                if not available_domains:
                    logger.error("Нет доступных доменов для fiverr.com")
                    results.append({
                        "success": False,
                        "error": "Нет доступных доменов для fiverr.com"
                    })
                    continue
                
                # Выбираем первый доступный домен с количеством > 0
                selected_domain = None
                for domain, info in available_domains.items():
                    if info.get("count", 0) > 0:
                        selected_domain = domain
                        break
                
                if not selected_domain:
                    logger.error("Нет доступных доменов с почтами")
                    results.append({
                        "success": False,
                        "error": "Нет доступных доменов с почтами"
                    })
                    continue
                
                logger.info(f"Выбран домен: {selected_domain}")
                
                # Заказываем email
                email_result = await email_service.order_email("fiverr.com", selected_domain)
                logger.info(f"Результат заказа email: {type(email_result)} - {email_result}")
                
                if not isinstance(email_result, dict) or not email_result.get("email"):
                    error_msg = email_result.get('value', 'Неизвестная ошибка') if isinstance(email_result, dict) else str(email_result)
                    logger.error(f"Не удалось заказать email: {error_msg}")
                    results.append({
                        "success": False,
                        "error": f"Ошибка заказа email: {error_msg}"
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
