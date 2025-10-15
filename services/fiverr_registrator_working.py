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
import time
import io
import base64
from datetime import datetime
from typing import Optional, Dict, Any
import logging
logger = logging.getLogger(__name__)
from services.email_api import EmailAPIService
from services.proxy_manager import ProxyConfig

# Импорты для Selenium (только для скриншотов)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium не установлен - скриншоты недоступны")

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
    
    async def _bypass_press_hold_captcha(self, driver) -> bool:
        """Обход капчи PRESS & HOLD"""
        try:
            logger.info("Пытаемся обойти капчу PRESS & HOLD...")
            
            # Ждем загрузки страницы
            await asyncio.sleep(2)
            
            # Ищем кнопку PRESS & HOLD по разным селекторам
            button_selectors = [
                "button[class*='press']",
                "button[class*='hold']", 
                "button[class*='captcha']",
                "div[class*='press']",
                "div[class*='hold']",
                "button:contains('PRESS')",
                "button:contains('HOLD')",
                "[data-testid*='captcha']",
                "[id*='captcha']",
                "button[style*='border']"
            ]
            
            button = None
            for selector in button_selectors:
                try:
                    if ":contains" in selector:
                        # Используем XPath для текстового поиска
                        xpath = f"//button[contains(text(), 'PRESS') or contains(text(), 'HOLD')]"
                        button = driver.find_element(By.XPATH, xpath)
                    else:
                        button = driver.find_element(By.CSS_SELECTOR, selector)
                    if button:
                        logger.info(f"Найдена кнопка капчи по селектору: {selector}")
                        break
                except:
                    continue
            
            if not button:
                logger.warning("Кнопка капчи не найдена")
                return False
            
            # Получаем размеры кнопки
            size = button.size
            logger.info(f"Размеры кнопки: {size}")
            
            # Нажимаем и удерживаем кнопку
            from selenium.webdriver.common.action_chains import ActionChains
            
            actions = ActionChains(driver)
            
            # Перемещаемся к кнопке
            actions.move_to_element(button)
            
            # Нажимаем и удерживаем
            actions.click_and_hold(button)
            
            # Удерживаем от 3 до 5 секунд (случайно)
            hold_time = random.uniform(3, 5)
            logger.info(f"Удерживаем кнопку {hold_time:.1f} секунд...")
            
            # Выполняем действие
            actions.perform()
            
            # Ждем указанное время
            await asyncio.sleep(hold_time)
            
            # Отпускаем кнопку
            actions.release(button).perform()
            
            logger.info("Кнопка отпущена, ждем результат...")
            
            # Ждем результата (до 10 секунд)
            for _ in range(20):
                await asyncio.sleep(0.5)
                
                # Проверяем, исчезла ли капча
                try:
                    current_url = driver.current_url
                    if "fiverr.com" in current_url and "px-captcha" not in current_url:
                        logger.info("Капча успешно пройдена!")
                        return True
                except:
                    pass
                
                # Проверяем, появились ли ошибки
                try:
                    page_source = driver.page_source
                    if "error" in page_source.lower() or "blocked" in page_source.lower():
                        logger.warning("Обнаружена ошибка на странице")
                        return False
                except:
                    pass
            
            logger.warning("Время ожидания истекло, капча не пройдена")
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при обходе капчи: {e}")
            return False

    async def _register_with_captcha_bypass(self, email: str, username: str, password: str, telegram_bot = None, chat_id: int = None) -> Dict[str, Any]:
        """Регистрация с обходом капчи через браузер"""
        if not SELENIUM_AVAILABLE:
            return {
                "success": False,
                "error": "Selenium недоступен - обход капчи невозможен"
            }
        
        driver = None
        try:
            logger.info("Запускаем браузер для обхода капчи...")
            
            # Настройки Chrome
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Случайный User-Agent
            user_agent = self._get_random_user_agent()
            options.add_argument(f'--user-agent={user_agent}')
            
            # Запускаем браузер
            driver = webdriver.Chrome(options=options)
            
            # Убираем признаки автоматизации
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
            
            # Переходим на главную страницу (где происходит регистрация)
            logger.info("Переходим на главную страницу Fiverr...")
            driver.get("https://it.fiverr.com/")
            
            # Ждем загрузки
            await asyncio.sleep(3)
            
            # Проверяем, есть ли капча
            page_source = driver.page_source
            if "PRESS" in page_source and "HOLD" in page_source:
                logger.info("Обнаружена капча PRESS & HOLD, пытаемся обойти...")
                
                # Делаем скриншот капчи
                if telegram_bot and chat_id:
                    try:
                        screenshot = driver.get_screenshot_as_png()
                        from io import BytesIO
                        screenshot_file = BytesIO(screenshot)
                        screenshot_file.name = f"captcha_before_{email}.png"
                        
                        await telegram_bot.send_photo(
                            chat_id=chat_id,
                            photo=screenshot_file,
                            caption=f"🚨 <b>Обнаружена капча PRESS & HOLD</b>\n\n"
                                   f"📧 Email: <code>{email}</code>\n"
                                   f"🌐 Страница: Главная страница Fiverr\n"
                                   f"🤖 Пытаемся обойти автоматически...",
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        logger.warning(f"Ошибка отправки скриншота: {e}")
                
                # Обходим капчу
                captcha_bypassed = await self._bypass_press_hold_captcha(driver)
                
                if not captcha_bypassed:
                    logger.warning("Не удалось обойти капчу")
                    return {
                        "success": False,
                        "error": "Не удалось обойти капчу PRESS & HOLD"
                    }
                
                logger.info("Капча успешно обойдена, продолжаем регистрацию...")
            
            # Теперь заполняем форму регистрации на главной странице
            try:
                # Ищем поля формы регистрации на главной странице
                # Пробуем разные селекторы для полей регистрации
                email_selectors = [
                    "input[type='email']",
                    "input[name*='email']", 
                    "input[id*='email']",
                    "input[placeholder*='email' i]",
                    "input[placeholder*='Email' i]",
                    "input[data-testid*='email']"
                ]
                
                password_selectors = [
                    "input[type='password']",
                    "input[name*='password']",
                    "input[id*='password']",
                    "input[placeholder*='password' i]",
                    "input[placeholder*='Password' i]",
                    "input[data-testid*='password']"
                ]
                
                username_selectors = [
                    "input[name*='username']",
                    "input[id*='username']",
                    "input[placeholder*='username' i]",
                    "input[placeholder*='Username' i]",
                    "input[data-testid*='username']"
                ]
                
                # Ищем поля по селекторам
                email_field = None
                for selector in email_selectors:
                    try:
                        email_field = driver.find_element(By.CSS_SELECTOR, selector)
                        logger.info(f"Найдено поле email по селектору: {selector}")
                        break
                    except:
                        continue
                
                password_field = None
                for selector in password_selectors:
                    try:
                        password_field = driver.find_element(By.CSS_SELECTOR, selector)
                        logger.info(f"Найдено поле password по селектору: {selector}")
                        break
                    except:
                        continue
                
                username_field = None
                for selector in username_selectors:
                    try:
                        username_field = driver.find_element(By.CSS_SELECTOR, selector)
                        logger.info(f"Найдено поле username по селектору: {selector}")
                        break
                    except:
                        continue
                
                if not email_field or not password_field:
                    logger.error("Не найдены обязательные поля email или password")
                    return {
                        "success": False,
                        "error": "Не найдены поля формы регистрации на главной странице"
                    }
                
                # Заполняем поля
                email_field.clear()
                email_field.send_keys(email)
                logger.info("Поле email заполнено")
                
                password_field.clear()
                password_field.send_keys(password)
                logger.info("Поле password заполнено")
                
                # Заполняем username если поле найдено
                if username_field:
                    username_field.clear()
                    username_field.send_keys(username)
                    logger.info("Поле username заполнено")
                else:
                    logger.info("Поле username не найдено - возможно необязательное")
                
                logger.info("Поля формы заполнены")
                
                # Ищем кнопку регистрации на главной странице
                submit_selectors = [
                    "button[type='submit']",
                    "button[class*='submit']",
                    "button[class*='register']",
                    "button[class*='signup']",
                    "button[class*='join']",
                    "button[class*='create']",
                    "input[type='submit']",
                    "button:contains('Sign up')",
                    "button:contains('Join')",
                    "button:contains('Register')",
                    "button:contains('Create')",
                    "[data-testid*='submit']",
                    "[data-testid*='register']",
                    "[data-testid*='signup']"
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    try:
                        if ":contains" in selector:
                            # Используем XPath для текстового поиска
                            text = selector.split("'")[1]
                            xpath = f"//button[contains(text(), '{text}')]"
                            submit_button = driver.find_element(By.XPATH, xpath)
                        else:
                            submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                        if submit_button:
                            logger.info(f"Найдена кнопка регистрации по селектору: {selector}")
                            break
                    except:
                        continue
                
                if not submit_button:
                    logger.error("Кнопка регистрации не найдена")
                    return {
                        "success": False,
                        "error": "Кнопка регистрации не найдена на главной странице"
                    }
                
                # Нажимаем кнопку
                submit_button.click()
                logger.info("Кнопка регистрации нажата")
                
                # Ждем результата
                await asyncio.sleep(5)
                
                # Проверяем успешность регистрации
                current_url = driver.current_url
                page_source = driver.page_source
                
                if "success" in page_source.lower() or "welcome" in page_source.lower() or "dashboard" in current_url:
                    logger.info("Регистрация успешна!")
                    
                    # Получаем cookies
                    cookies = {}
                    for cookie in driver.get_cookies():
                        cookies[cookie['name']] = cookie['value']
                    
                    return {
                        "success": True,
                        "email": email,
                        "username": username,
                        "password": password,
                        "cookies": cookies,
                        "method": "browser_with_captcha_bypass"
                    }
                else:
                    logger.warning("Регистрация не удалась")
                    return {
                        "success": False,
                        "error": "Регистрация не удалась после обхода капчи"
                    }
                    
            except Exception as e:
                logger.error(f"Ошибка при заполнении формы: {e}")
                return {
                    "success": False,
                    "error": f"Ошибка заполнения формы: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"Критическая ошибка при обходе капчи: {e}")
            return {
                "success": False,
                "error": f"Ошибка обхода капчи: {str(e)}"
            }
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.info("Браузер закрыт")
                except:
                    pass

    async def _take_captcha_screenshot(self, url: str = "https://it.fiverr.com/") -> Optional[bytes]:
        """Сделать скриншот страницы с капчей"""
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium недоступен - скриншот не может быть сделан")
            return None
        
        driver = None
        try:
            logger.info("Запускаем браузер для скриншота капчи...")
            
            # Настройки Chrome
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Добавляем прокси если есть (только для HTTP запросов, не для Selenium)
            # Chrome не поддерживает прокси с аутентификацией через --proxy-server
            # Прокси будет использоваться только в HTTP запросах
            
            # Случайный User-Agent
            user_agent = self._get_random_user_agent()
            options.add_argument(f'--user-agent={user_agent}')
            
            # Запускаем браузер
            driver = webdriver.Chrome(options=options)
            
            # Убираем признаки автоматизации
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
            
            # Переходим на страницу
            logger.info(f"Переходим на {url}...")
            driver.get(url)
            
            # Ждем загрузки
            await asyncio.sleep(3)
            
            # Делаем скриншот
            logger.info("Делаем скриншот...")
            screenshot = driver.get_screenshot_as_png()
            
            logger.info(f"Скриншот сделан, размер: {len(screenshot)} байт")
            return screenshot
            
        except Exception as e:
            logger.error(f"Ошибка при создании скриншота: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.info("Браузер закрыт")
                except:
                    pass
        
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
    
    async def register_account(self, email: str, email_service: EmailAPIService, email_id: str = None, telegram_bot = None, chat_id: int = None) -> Dict[str, Any]:
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
                        'csrftoken': csrf_token if csrf_token else f'token_{random.randint(100000, 999999)}',
                        '_ga': f'GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}',
                        '_gid': f'GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}',
                        '_fbp': f'fb.1.{int(time.time())}.{random.randint(100000000, 999999999)}',
                        '_gcl_au': f'1.1.{random.randint(100000000, 999999999)}.{int(time.time())}',
                        'NID': f'{random.randint(100000000, 999999999)}={random.randint(100000000, 999999999)}',
                        '1P_JAR': f'{datetime.now().strftime("%Y-%m-%d")}-{random.randint(1, 20)}',
                        'CONSENT': 'YES+cb.20210328-17-p0.en+FX+667',
                        'AEC': f'AakniG{random.randint(100000000, 999999999)}',
                        'SAPISID': f'{random.randint(100000000, 999999999)}/{int(time.time())}',
                        'APISID': f'{random.randint(100000000, 999999999)}/{int(time.time())}',
                        'SSID': f'{random.randint(100000000, 999999999)}/{int(time.time())}',
                        'HSID': f'{random.randint(100000000, 999999999)}/{int(time.time())}',
                        'SID': f'{random.randint(100000000, 999999999)}/{int(time.time())}',
                        'SIDCC': f'{random.randint(100000000, 999999999)}/{int(time.time())}',
                        '__Secure-1PSID': f'{random.randint(100000000, 999999999)}/{int(time.time())}',
                        '__Secure-3PSID': f'{random.randint(100000000, 999999999)}/{int(time.time())}',
                        '__Secure-1PAPISID': f'{random.randint(100000000, 999999999)}/{int(time.time())}',
                        '__Secure-3PAPISID': f'{random.randint(100000000, 999999999)}/{int(time.time())}',
                        '__Secure-1PSIDCC': f'{random.randint(100000000, 999999999)}/{int(time.time())}',
                        '__Secure-3PSIDCC': f'{random.randint(100000000, 999999999)}/{int(time.time())}'
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
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-GPC': '1',
                'X-Forwarded-For': f'192.168.{random.randint(1,255)}.{random.randint(1,255)}',
                'X-Real-IP': f'192.168.{random.randint(1,255)}.{random.randint(1,255)}'
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
            
            # Сначала делаем GET запрос для имитации реального браузера
            logger.info("Выполняем предварительный GET запрос...")
            user_agent = self._get_random_user_agent()
            get_headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9,it;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Referer': 'https://www.google.com/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Ch-Ua': '"Not:A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'DNT': '1',
                'Connection': 'keep-alive'
            }
            
            proxy_url = self.proxy.to_url() if (self.proxy and self.use_proxy) else None
            async with self.session.get('https://it.fiverr.com/', headers=get_headers, proxy=proxy_url) as get_response:
                logger.info(f"GET запрос выполнен: {get_response.status}")
                # Обновляем cookies из GET ответа
                for cookie in get_response.cookies:
                    try:
                        if hasattr(cookie, 'key') and hasattr(cookie, 'value'):
                            self.cookies[cookie.key] = cookie.value
                        elif hasattr(cookie, 'key'):
                            self.cookies[cookie.key] = str(cookie)
                        else:
                            # Если это строка, добавляем как есть
                            cookie_str = str(cookie)
                            if '=' in cookie_str:
                                key, value = cookie_str.split('=', 1)
                                self.cookies[key] = value
                    except Exception as e:
                        logger.warning(f"Ошибка обработки cookie: {e}")
            
            # Добавляем задержку для имитации человеческого поведения
            await asyncio.sleep(random.uniform(2, 5))
            
            # Делаем промежуточный запрос к странице регистрации
            logger.info("Переходим на страницу регистрации...")
            reg_headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9,it;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Referer': 'https://it.fiverr.com/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Ch-Ua': '"Not:A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'DNT': '1',
                'Connection': 'keep-alive'
            }
            
            async with self.session.get('https://it.fiverr.com/register', headers=reg_headers, proxy=proxy_url) as reg_response:
                logger.info(f"GET /register выполнен: {reg_response.status}")
                # Обновляем cookies из ответа
                for cookie in reg_response.cookies:
                    try:
                        if hasattr(cookie, 'key') and hasattr(cookie, 'value'):
                            self.cookies[cookie.key] = cookie.value
                        elif hasattr(cookie, 'key'):
                            self.cookies[cookie.key] = str(cookie)
                        else:
                            # Если это строка, добавляем как есть
                            cookie_str = str(cookie)
                            if '=' in cookie_str:
                                key, value = cookie_str.split('=', 1)
                                self.cookies[key] = value
                    except Exception as e:
                        logger.warning(f"Ошибка обработки cookie: {e}")
            
            # Еще одна задержка
            await asyncio.sleep(random.uniform(1, 3))
            
            # Выполняем запрос регистрации
            logger.info("Выполняем POST запрос регистрации...")
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
                            try:
                                if hasattr(cookie, 'key') and hasattr(cookie, 'value'):
                                    self.cookies[cookie.key] = cookie.value
                                elif hasattr(cookie, 'key'):
                                    self.cookies[cookie.key] = str(cookie)
                                else:
                                    # Если это строка, добавляем как есть
                                    cookie_str = str(cookie)
                                    if '=' in cookie_str:
                                        key, value = cookie_str.split('=', 1)
                                        self.cookies[key] = value
                            except Exception as e:
                                logger.warning(f"Ошибка обработки cookie: {e}")
                        
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
                    
                    # Делаем скриншот капчи если есть Telegram бот
                    screenshot_data = None
                    if telegram_bot and chat_id:
                        try:
                            logger.info("Делаем скриншот капчи...")
                            screenshot_data = await self._take_captcha_screenshot("https://it.fiverr.com/register")
                            
                            if screenshot_data:
                                # Отправляем скриншот в Telegram
                                from io import BytesIO
                                screenshot_file = BytesIO(screenshot_data)
                                screenshot_file.name = f"captcha_{email}.png"
                                
                                await telegram_bot.send_photo(
                                    chat_id=chat_id,
                                    photo=screenshot_file,
                                    caption=f"🚨 <b>Обнаружена капча PerimeterX</b>\n\n"
                                           f"📧 Email: <code>{email}</code>\n"
                                           f"🌐 URL: https://it.fiverr.com/register\n"
                                           f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
                                           f"<b>Рекомендации:</b>\n"
                                           f"• Использовать другой прокси\n"
                                           f"• Повторить через несколько минут\n"
                                           f"• Использовать VPN",
                                    parse_mode='HTML'
                                )
                                logger.info("Скриншот капчи отправлен в Telegram")
                            else:
                                logger.warning("Не удалось создать скриншот капчи")
                                
                        except Exception as e:
                            logger.error(f"Ошибка при отправке скриншота: {e}")
                    
                    # Пытаемся обойти капчу через браузер
                    logger.info("Пытаемся обойти капчу через браузер...")
                    browser_result = await self._register_with_captcha_bypass(
                        email=email,
                        username=username,
                        password=password,
                        telegram_bot=telegram_bot,
                        chat_id=chat_id
                    )
                    
                    if browser_result.get("success"):
                        logger.info("Регистрация успешна через браузер с обходом капчи!")
                        return browser_result
                    else:
                        logger.warning("Не удалось зарегистрироваться через браузер")
                        return {
                            "success": False,
                            "error": f"❌ Обнаружена защита PerimeterX (капча). HTTP регистрация заблокирована. Обход капчи не удался: {browser_result.get('error', 'Неизвестная ошибка')}",
                            "method": "http_blocked_captcha_bypass_failed",
                            "screenshot_sent": screenshot_data is not None
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
    use_proxy: bool = True,
    telegram_bot = None,
    chat_id: int = None,
    selected_domain: str = 'gmx.com'
) -> list:
    """Пакетная регистрация аккаунтов"""
    results = []
    
    async with FiverrWorkingRegistrator(proxy, use_proxy) as registrator:
        for i in range(count):
            try:
                logger.info(f"Регистрация аккаунта {i+1}/{count}")
                
                # Получаем доступные домены и выбираем первый доступный
                # Используем выбранный пользователем домен
                logger.info(f"Используем выбранный домен: {selected_domain}")
                
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
                result = await registrator.register_account(
                    email=email, 
                    email_service=email_service, 
                    email_id=email_result.get("id"),
                    telegram_bot=telegram_bot,
                    chat_id=chat_id
                )
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
