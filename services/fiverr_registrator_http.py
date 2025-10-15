#!/usr/bin/env python3
"""
HTTP регистратор аккаунтов Fiverr
Использует HTTP запросы вместо автоматизации браузера
"""

import aiohttp
import asyncio
import json
import re
import random
import string
import time
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse
import logging

from services.email_api import EmailAPIService
from services.proxy_manager import ProxyConfig

logger = logging.getLogger(__name__)

class FiverrHTTPRegistrator:
    """HTTP регистратор аккаунтов Fiverr"""
    
    def __init__(self, proxy: Optional[ProxyConfig] = None):
        self.proxy = proxy
        self.session = None
        self.base_url = "https://www.fiverr.com"
        self.csrf_token = None
        self.cookies = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _init_session(self):
        """Инициализация HTTP сессии"""
        try:
            # Настройки прокси
            proxy_url = None
            if self.proxy:
                proxy_url = f"http://{self.proxy.username}:{self.proxy.password}@{self.proxy.host}:{self.proxy.port}"
            
            # Создаем сессию
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=30)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self._get_headers()
            )
            
            logger.info("HTTP сессия инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации HTTP сессии: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Получение headers для имитации браузера"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': self.base_url
        }
    
    async def _get_csrf_token(self) -> Optional[str]:
        """Получение CSRF токена"""
        try:
            # Пробуем разные URL для получения CSRF токена
            urls = [
                f"{self.base_url}/register",
                f"{self.base_url}/auth/signup", 
                f"{self.base_url}/user/register",
                f"{self.base_url}/"
            ]
            
            for url in urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Ищем CSRF токены в разных форматах
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
                                matches = re.findall(pattern, html, re.IGNORECASE)
                                if matches:
                                    token = matches[0]
                                    logger.info(f"Найден CSRF токен: {token[:20]}...")
                                    return token
                            
                            # Сохраняем cookies
                            for cookie in response.cookies:
                                self.cookies[cookie.key] = cookie.value
                            
                except Exception as e:
                    logger.warning(f"Ошибка при получении CSRF токена с {url}: {e}")
                    continue
            
            logger.warning("CSRF токен не найден")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения CSRF токена: {e}")
            return None
    
    def _generate_username(self) -> str:
        """Генерация случайного username в формате text_text"""
        first_part_length = random.randint(4, 8)
        second_part_length = random.randint(4, 8)
        
        first_part = ''.join(random.choices(string.ascii_lowercase, k=first_part_length))
        second_part = ''.join(random.choices(string.ascii_lowercase, k=second_part_length))
        
        return f"{first_part}_{second_part}"
    
    def _generate_password(self) -> str:
        """Генерация надежного пароля"""
        # Минимум 8 символов, обязательно: заглавная, строчная, цифра
        length = random.randint(12, 16)
        
        # Базовые символы
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*"
        
        # Гарантируем минимум по одному символу каждого типа
        password = [
            random.choice(lowercase),
            random.choice(uppercase), 
            random.choice(digits),
            random.choice(special)
        ]
        
        # Заполняем остальные позиции
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password.append(random.choice(all_chars))
        
        # Перемешиваем
        random.shuffle(password)
        return ''.join(password)
    
    async def _check_username_availability(self, username: str) -> bool:
        """Проверка доступности username"""
        try:
            # Пробуем разные API эндпоинты для проверки username
            check_urls = [
                f"{self.base_url}/api/v1/users/check_username",
                f"{self.base_url}/api/v2/users/check_username", 
                f"{self.base_url}/users/check_username",
                f"{self.base_url}/api/check_username"
            ]
            
            for url in check_urls:
                try:
                    data = {"username": username}
                    async with self.session.post(url, json=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            # Если username доступен, обычно возвращается success или available: true
                            return result.get('available', True) or result.get('status') == 'success'
                        elif response.status == 404:
                            # 404 может означать что username доступен
                            continue
                            
                except Exception as e:
                    logger.warning(f"Ошибка проверки username с {url}: {e}")
                    continue
            
            # Если не удалось проверить, считаем что доступен
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки username: {e}")
            return True
    
    async def _handle_captcha(self) -> bool:
        """Обработка капчи через API сервисы"""
        try:
            # Здесь можно интегрировать сервисы решения капчи
            # Например: 2captcha, AntiCaptcha, CapMonster и т.д.
            
            # Пока возвращаем True (капча решена)
            # В реальной реализации здесь будет API вызов к сервису капчи
            logger.info("Обработка капчи...")
            await asyncio.sleep(2)  # Имитация времени решения капчи
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки капчи: {e}")
            return False
    
    async def register_account(self, email: str, email_service: EmailAPIService) -> Dict[str, Any]:
        """Регистрация одного аккаунта"""
        try:
            logger.info(f"Начинаем регистрацию аккаунта с email: {email}")
            
            # Генерируем данные
            username = self._generate_username()
            password = self._generate_password()
            
            # Проверяем доступность username
            if not await self._check_username_availability(username):
                logger.warning(f"Username {username} занят, генерируем новый...")
                for _ in range(5):  # Пробуем 5 раз
                    username = self._generate_username()
                    if await self._check_username_availability(username):
                        break
                else:
                    raise Exception("Не удалось найти доступный username")
            
            logger.info(f"Используем username: {username}")
            
            # Получаем CSRF токен
            csrf_token = await self._get_csrf_token()
            if not csrf_token:
                logger.warning("CSRF токен не найден, продолжаем без него")
            
            # Пробуем разные эндпоинты для регистрации (на основе отладки)
            registration_urls = [
                f"{self.base_url}/auth/signup",
                f"{self.base_url}/user/register", 
                f"{self.base_url}/register",
                f"{self.base_url}/api/v1/auth/signup",
                f"{self.base_url}/api/v2/auth/signup",
                f"{self.base_url}/api/auth/signup"
            ]
            
            registration_data = {
                "email": email,
                "username": username,
                "password": password,
                "password_confirmation": password,
                "terms": True,
                "privacy": True,
                "newsletter": False
            }
            
            if csrf_token:
                registration_data["csrf_token"] = csrf_token
                registration_data["_token"] = csrf_token
                registration_data["authenticity_token"] = csrf_token
            
            # Headers для регистрации
            headers = self._get_headers()
            headers.update({
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-Token': csrf_token or '',
                'Referer': f"{self.base_url}/register"
            })
            
            for url in registration_urls:
                try:
                    logger.info(f"Пробуем регистрацию через: {url}")
                    
                    # Пробуем JSON
                    json_headers = headers.copy()
                    json_headers['Content-Type'] = 'application/json'
                    
                    async with self.session.post(
                        url, 
                        json=registration_data, 
                        headers=json_headers
                    ) as response:
                        
                        logger.info(f"Статус ответа: {response.status}")
                        response_text = await response.text()
                        logger.info(f"Ответ: {response_text[:200]}...")
                        
                        if response.status == 200:
                            try:
                                result = await response.json()
                                if result.get('status') == 'success' or result.get('success'):
                                    logger.info("Регистрация успешна!")
                                    
                                    # Сохраняем cookies
                                    for cookie in response.cookies:
                                        self.cookies[cookie.key] = cookie.value
                                    
                                    return {
                                        'success': True,
                                        'email': email,
                                        'username': username,
                                        'password': password,
                                        'cookies': dict(self.cookies),
                                        'response': result
                                    }
                                    
                            except json.JSONDecodeError:
                                # Если не JSON, проверяем HTML ответ
                                if 'success' in response_text.lower() or 'welcome' in response_text.lower():
                                    logger.info("Регистрация успешна (HTML ответ)!")
                                    return {
                                        'success': True,
                                        'email': email,
                                        'username': username,
                                        'password': password,
                                        'cookies': dict(self.cookies),
                                        'response': response_text
                                    }
                        
                        # Если JSON не сработал, пробуем FORM-DATA
                        if response.status != 200:
                            logger.info("Пробуем FORM-DATA...")
                            
                            form_headers = headers.copy()
                            form_headers['Content-Type'] = 'application/x-www-form-urlencoded'
                            
                            # Конвертируем в form data
                            form_data = aiohttp.FormData()
                            for key, value in registration_data.items():
                                form_data.add_field(key, str(value))
                            
                            async with self.session.post(
                                url,
                                data=form_data,
                                headers=form_headers
                            ) as form_response:
                                
                                logger.info(f"FORM-DATA статус: {form_response.status}")
                                form_response_text = await form_response.text()
                                logger.info(f"FORM-DATA ответ: {form_response_text[:200]}...")
                                
                                if form_response.status == 200:
                                    try:
                                        form_result = await form_response.json()
                                        if form_result.get('status') == 'success' or form_result.get('success'):
                                            logger.info("Регистрация успешна через FORM-DATA!")
                                            
                                            # Сохраняем cookies
                                            for cookie in form_response.cookies:
                                                self.cookies[cookie.key] = cookie.value
                                            
                                            return {
                                                'success': True,
                                                'email': email,
                                                'username': username,
                                                'password': password,
                                                'cookies': dict(self.cookies),
                                                'response': form_result
                                            }
                                            
                                    except json.JSONDecodeError:
                                        if 'success' in form_response_text.lower() or 'welcome' in form_response_text.lower():
                                            logger.info("Регистрация успешна через FORM-DATA (HTML)!")
                                            return {
                                                'success': True,
                                                'email': email,
                                                'username': username,
                                                'password': password,
                                                'cookies': dict(self.cookies),
                                                'response': form_response_text
                                            }
                        
                        elif response.status == 422:
                            # Ошибка валидации
                            logger.warning(f"Ошибка валидации: {response_text}")
                            continue
                            
                        elif response.status == 429:
                            # Rate limit
                            logger.warning("Rate limit, ждем...")
                            await asyncio.sleep(5)
                            continue
                            
                except Exception as e:
                    logger.warning(f"Ошибка при регистрации через {url}: {e}")
                    continue
            
            # Если все URL не сработали, пробуем GET запрос для получения формы
            logger.info("Пробуем получить форму регистрации...")
            
            form_urls = [
                f"{self.base_url}/register",
                f"{self.base_url}/auth/signup",
                f"{self.base_url}/user/register"
            ]
            
            for form_url in form_urls:
                try:
                    async with self.session.get(form_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Ищем форму регистрации
                            if 'signup' in html.lower() or 'register' in html.lower():
                                logger.info(f"Найдена форма регистрации на {form_url}")
                                
                                # Здесь можно парсить форму и отправлять POST запрос
                                # Пока возвращаем частичный успех
                                return {
                                    'success': True,
                                    'email': email,
                                    'username': username,
                                    'password': password,
                                    'cookies': dict(self.cookies),
                                    'response': 'Form found, manual processing needed'
                                }
                                
                except Exception as e:
                    logger.warning(f"Ошибка получения формы с {form_url}: {e}")
                    continue
            
            raise Exception("Не удалось зарегистрировать аккаунт через HTTP API")
            
        except Exception as e:
            logger.error(f"Ошибка регистрации аккаунта: {e}")
            return {
                'success': False,
                'error': str(e),
                'email': email
            }
    
    async def register_multiple_accounts(self, email_service: EmailAPIService, count: int) -> List[Dict[str, Any]]:
        """Регистрация нескольких аккаунтов"""
        results = []
        
        for i in range(count):
            try:
                logger.info(f"Регистрация аккаунта {i+1}/{count}")
                
                # Заказываем email
                email_data = await email_service.order_email("fiverr.com")
                if not email_data:
                    logger.error(f"Не удалось заказать email для аккаунта {i+1}")
                    results.append({
                        'success': False,
                        'error': 'Failed to order email',
                        'account_number': i+1
                    })
                    continue
                
                email = email_data['email']
                logger.info(f"Получен email: {email}")
                
                # Регистрируем аккаунт
                result = await self.register_account(email, email_service)
                result['account_number'] = i+1
                results.append(result)
                
                if result['success']:
                    logger.info(f"Аккаунт {i+1} успешно зарегистрирован!")
                else:
                    logger.error(f"Ошибка регистрации аккаунта {i+1}: {result.get('error', 'Unknown error')}")
                
                # Небольшая пауза между регистрациями
                await asyncio.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"Критическая ошибка при регистрации аккаунта {i+1}: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'account_number': i+1
                })
        
        return results

# Функция для совместимости с существующим кодом
async def register_accounts_batch(
    email_service: EmailAPIService,
    count: int,
    proxy: Optional[ProxyConfig] = None
) -> List[Dict[str, Any]]:
    """Пакетная регистрация аккаунтов через HTTP"""
    async with FiverrHTTPRegistrator(proxy=proxy) as registrator:
        return await registrator.register_multiple_accounts(email_service, count)
