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

class FiverrRegistrator:
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
            
            # Удерживаем от 7 до 9 секунд (как требует капча)
            hold_time = random.uniform(7, 9)
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

    async def _take_step_screenshot(self, driver, step_name: str, telegram_bot = None, chat_id: int = None, email: str = None) -> None:
        """Отправка скриншота текущего этапа в Telegram"""
        if not telegram_bot or not chat_id:
            return
            
        try:
            screenshot = driver.get_screenshot_as_png()
            from io import BytesIO
            screenshot_file = BytesIO(screenshot)
            screenshot_file.name = f"{step_name}_{email or 'unknown'}.png"
            
            await telegram_bot.send_photo(
                chat_id=chat_id,
                photo=screenshot_file,
                caption=f"📸 <b>{step_name}</b>\n\n"
                       f"📧 Email: <code>{email or 'N/A'}</code>\n"
                       f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}",
                parse_mode='HTML'
            )
            logger.info(f"Скриншот этапа '{step_name}' отправлен в Telegram")
        except Exception as e:
            logger.warning(f"Ошибка отправки скриншота этапа '{step_name}': {e}")

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
            
            # Агрессивно убиваем все процессы Chrome перед запуском
            import subprocess
            try:
                # Убиваем все процессы Chrome
                subprocess.run(["pkill", "-9", "-f", "chrome"], check=False, capture_output=True)
                subprocess.run(["pkill", "-9", "-f", "chromedriver"], check=False, capture_output=True)
                subprocess.run(["pkill", "-9", "-f", "chromium"], check=False, capture_output=True)
                
                # Очищаем временные файлы Chrome
                subprocess.run(["rm", "-rf", "/tmp/.com.google.Chrome*"], check=False, capture_output=True)
                subprocess.run(["rm", "-rf", "/tmp/chrome*"], check=False, capture_output=True)
                
                await asyncio.sleep(2)
                logger.info("Все процессы Chrome принудительно завершены")
            except Exception as e:
                logger.warning(f"Ошибка при очистке процессов: {e}")
            
            # Настройки Chrome
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Используем только incognito без user-data-dir
            options.add_argument('--incognito')
            options.add_argument('--no-first-run')
            options.add_argument('--disable-default-apps')
            options.add_argument('--no-user-data-dir')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            
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
            
            # Скриншот главной страницы
            await self._take_step_screenshot(driver, "Главная страница Fiverr", telegram_bot, chat_id, email)
            
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
                
                # Скриншот после обхода капчи
                await self._take_step_screenshot(driver, "Капча обойдена", telegram_bot, chat_id, email)
            
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
                
                # Скриншот после заполнения email
                await self._take_step_screenshot(driver, "Email заполнен", telegram_bot, chat_id, email)
                
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
                
                # Скриншот после заполнения всех полей
                await self._take_step_screenshot(driver, "Все поля заполнены", telegram_bot, chat_id, email)
                
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
                
                # Скриншот после нажатия кнопки регистрации
                await self._take_step_screenshot(driver, "Кнопка регистрации нажата", telegram_bot, chat_id, email)
                
                # Ждем результата
                await asyncio.sleep(5)
                
                # Проверяем успешность регистрации
                current_url = driver.current_url
                page_source = driver.page_source
                
                if "success" in page_source.lower() or "welcome" in page_source.lower() or "dashboard" in current_url:
                    logger.info("Регистрация успешна!")
                    
                    # Скриншот успешной регистрации
                    await self._take_step_screenshot(driver, "Регистрация успешна!", telegram_bot, chat_id, email)
                    
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
            
            # Временные файлы больше не используются

    async def _take_captcha_screenshot(self, url: str = "https://it.fiverr.com/") -> Optional[bytes]:
        """Сделать скриншот страницы с капчей"""
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium недоступен - скриншот не может быть сделан")
            return None
        
        driver = None
        try:
            logger.info("Запускаем браузер для скриншота капчи...")
            
            # Убиваем все процессы Chrome перед запуском
            import subprocess
            try:
                subprocess.run(["pkill", "-f", "chrome"], check=False, capture_output=True)
                subprocess.run(["pkill", "-f", "chromedriver"], check=False, capture_output=True)
                await asyncio.sleep(1)
            except:
                pass
            
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
            
            # Используем только incognito без user-data-dir
            options.add_argument('--incognito')
            options.add_argument('--no-first-run')
            options.add_argument('--disable-default-apps')
            options.add_argument('--no-user-data-dir')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            
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
            
            # Временные файлы больше не используются
        
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
        """Регистрация аккаунта ТОЛЬКО через браузер"""
        try:
            logger.info(f"Начинаем регистрацию аккаунта с email: {email}")
            
            # Генерируем данные
            username = self._generate_username()
            password = self._generate_password()
            
            logger.info(f"Сгенерирован username: {username}")
            logger.info(f"Сгенерирован пароль: {password}")
            
            # СРАЗУ используем браузер для регистрации
            return await self._register_with_captcha_bypass(
                email=email,
                username=username,
                password=password,
                telegram_bot=telegram_bot,
                chat_id=chat_id
            )
            
        except Exception as e:
            logger.error(f"Ошибка регистрации аккаунта: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    

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
    
    async with FiverrRegistrator(proxy, use_proxy) as registrator:
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
