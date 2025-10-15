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
        """Проверка доступности имени пользователя - упрощенная версия"""
        # Пропускаем проверку через API, так как она может не работать
        # Fiverr сам проверит доступность при регистрации
        return True
    
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
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
                    logger.info("Обнаружена капча PerimeterX, переключаемся на браузерную автоматизацию...")
                    return await self._handle_captcha_with_browser(email, username, password, email_service, email_id)
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
    
    async def _handle_captcha_with_browser(self, email: str, username: str, password: str, email_service: EmailAPIService, email_id: str = None) -> Dict[str, Any]:
        """Обработка капчи через браузерную автоматизацию"""
        try:
            logger.info("Запускаем браузер для обхода капчи...")
            
            # Импортируем selenium только когда нужен
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            import time
            
            # Настройки браузера для обхода детекции
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")
            
            # Явно отключаем user-data-dir и используем incognito
            options.add_argument("--incognito")
            options.add_argument("--no-user-data-dir")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            options.add_argument("--no-first-run")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-translate")
            options.add_argument("--disable-logging")
            options.add_argument("--disable-gpu-logging")
            options.add_argument("--silent")
            options.add_argument("--log-level=3")
            
            # Настройка прокси если есть
            if self.proxy:
                proxy_url = f"http://{self.proxy.username}:{self.proxy.password}@{self.proxy.host}:{self.proxy.port}"
                options.add_argument(f"--proxy-server={proxy_url}")
            
            # Агрессивная очистка процессов Chrome перед запуском
            import subprocess
            import os
            try:
                # Убиваем все процессы Chrome
                subprocess.run(["pkill", "-9", "-f", "chrome"], check=False)
                subprocess.run(["pkill", "-9", "-f", "chromedriver"], check=False)
                subprocess.run(["pkill", "-9", "-f", "google-chrome"], check=False)
                
                # Очищаем временные файлы Chrome
                temp_dirs = ["/tmp/.com.google.Chrome*", "/tmp/chrome_user_data*", "/tmp/.X*"]
                for temp_dir in temp_dirs:
                    subprocess.run(["rm", "-rf", temp_dir], check=False)
                
                time.sleep(3)
            except:
                pass
            
            # Пробуем запустить Chrome с минимальными настройками
            try:
                driver = webdriver.Chrome(options=options)
            except Exception as e:
                logger.error(f"Ошибка запуска Chrome: {e}")
                # Пробуем без прокси если есть
                if self.proxy:
                    logger.info("Пробуем запустить Chrome без прокси...")
                    options_no_proxy = Options()
                    options_no_proxy.add_argument("--no-sandbox")
                    options_no_proxy.add_argument("--disable-dev-shm-usage")
                    options_no_proxy.add_argument("--incognito")
                    options_no_proxy.add_argument("--no-user-data-dir")
                    options_no_proxy.add_argument("--disable-blink-features=AutomationControlled")
                    options_no_proxy.add_experimental_option("excludeSwitches", ["enable-automation"])
                    options_no_proxy.add_experimental_option('useAutomationExtension', False)
                    options_no_proxy.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")
                    
                    driver = webdriver.Chrome(options=options_no_proxy)
                else:
                    raise e
            
            try:
                # Убираем признаки автоматизации
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                # Переходим на страницу регистрации
                driver.get("https://it.fiverr.com/")
                time.sleep(3)
                
                # Ищем и кликаем на кнопку регистрации
                try:
                    register_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='register'], button[data-track-tag*='register']"))
                    )
                    register_button.click()
                    time.sleep(2)
                except:
                    logger.warning("Не удалось найти кнопку регистрации, пробуем прямой переход")
                    driver.get("https://it.fiverr.com/register")
                    time.sleep(3)
                
                # Заполняем форму регистрации
                email_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name*='email'], input[id*='email']"))
                )
                email_field.clear()
                email_field.send_keys(email)
                time.sleep(1)
                
                # Ищем поле username
                try:
                    username_field = driver.find_element(By.CSS_SELECTOR, "input[name*='username'], input[id*='username']")
                    username_field.clear()
                    username_field.send_keys(username)
                    time.sleep(1)
                except:
                    logger.warning("Поле username не найдено")
                
                # Ищем поле password
                password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name*='password'], input[id*='password']")
                password_field.clear()
                password_field.send_keys(password)
                time.sleep(1)
                
                # Ищем и кликаем кнопку регистрации
                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], button[data-track-tag*='submit']")
                submit_button.click()
                time.sleep(5)
                
                # Проверяем, появилась ли капча
                if "px-captcha" in driver.page_source or "captcha" in driver.page_source.lower():
                    logger.info("Обнаружена капча, ждем решения...")
                    
                    # Ждем решения капчи (максимум 60 секунд)
                    for i in range(60):
                        if "px-captcha" not in driver.page_source and "captcha" not in driver.page_source.lower():
                            logger.info("Капча решена!")
                            break
                        time.sleep(1)
                    
                    # Проверяем успешность регистрации
                    if "success" in driver.page_source.lower() or "welcome" in driver.page_source.lower():
                        logger.info("Регистрация успешна через браузер!")
                        
                        # Получаем cookies
                        browser_cookies = {}
                        for cookie in driver.get_cookies():
                            browser_cookies[cookie['name']] = cookie['value']
                        
                        # Получаем код подтверждения если нужен
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
                            "cookies": browser_cookies,
                            "confirmation_code": confirmation_code,
                            "method": "browser_captcha"
                        }
                    else:
                        logger.error("Регистрация не удалась через браузер")
                        return {
                            "success": False,
                            "error": "Не удалось зарегистрироваться через браузер",
                            "method": "browser_captcha"
                        }
                else:
                    logger.info("Капча не обнаружена, регистрация прошла успешно")
                    return {
                        "success": True,
                        "email": email,
                        "username": username,
                        "password": password,
                        "cookies": {cookie['name']: cookie['value'] for cookie in driver.get_cookies()},
                        "confirmation_code": None,
                        "method": "browser_direct"
                    }
                    
            finally:
                driver.quit()
                
        except Exception as e:
            logger.error(f"Ошибка при обработке капчи через браузер: {e}")
            return {
                "success": False,
                "error": f"Ошибка браузера: {str(e)}",
                "method": "browser_captcha"
            }

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
