"""
Fiverr Account Registration - ТОЛЬКО БРАУЗЕРНАЯ ЭМУЛЯЦИЯ
Регистрация аккаунтов на Fiverr исключительно через Selenium
"""

import asyncio
import random
import string
import time
import uuid
import subprocess
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List
from io import BytesIO

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from utils.logger import logger
from services.proxy_manager import ProxyConfig
from services.email_api import EmailAPIService


class FiverrRegistrator:
    """Регистратор аккаунтов Fiverr ТОЛЬКО через браузер"""
    
    def __init__(self, proxy: Optional[ProxyConfig] = None, use_proxy: bool = True):
        self.proxy = proxy
        self.use_proxy = use_proxy
        self.driver = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def _generate_username(self) -> str:
        """Генерация случайного username в формате text_text"""
        first_part = ''.join(random.choices(string.ascii_lowercase, k=random.randint(6, 10)))
        second_part = ''.join(random.choices(string.ascii_lowercase, k=random.randint(6, 10)))
        return f"{first_part}_{second_part}"
    
    def _generate_password(self) -> str:
        """Генерация надежного пароля"""
        length = random.randint(8, 12)
        password = []
        
        # Обязательно добавляем символы разных типов
        password.append(random.choice(string.ascii_uppercase))  # Заглавная буква
        password.append(random.choice(string.ascii_lowercase))  # Строчная буква
        password.append(random.choice(string.digits))           # Цифра
        
        # Заполняем остальные символы
        for _ in range(length - 3):
            password.append(random.choice(string.ascii_letters + string.digits))
        
        # Перемешиваем
        random.shuffle(password)
        return ''.join(password)
    
    def _get_random_user_agent(self) -> str:
        """Получение случайного User-Agent"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        ]
        return random.choice(user_agents)
    
    def _setup_chrome_options(self) -> Options:
        """Настройка Chrome для максимальной скрытности"""
        options = Options()
        
        # Базовые настройки скрытности
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-translate")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-client-side-phishing-detection")
        options.add_argument("--disable-sync")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--no-report-upload")
        options.add_argument("--safebrowsing-disable-auto-update")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-prompt-on-repost")
        options.add_argument("--disable-domain-reliability")
        options.add_argument("--disable-component-update")
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-client-side-phishing-detection")
        options.add_argument("--disable-sync")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--no-report-upload")
        options.add_argument("--safebrowsing-disable-auto-update")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-prompt-on-repost")
        options.add_argument("--disable-domain-reliability")
        options.add_argument("--disable-component-update")
        options.add_argument("--disable-features=TranslateUI")
        
        # Режим инкогнито для изоляции
        options.add_argument("--incognito")
        options.add_argument("--no-user-data-dir")
        
        # User-Agent
        options.add_argument(f"--user-agent={self._get_random_user_agent()}")
        
        # Размер окна
        options.add_argument("--window-size=1920,1080")
        
        # Отключаем логи
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        
        # Отключаем уведомления
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.media_stream": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        return options
    
    async def _kill_chrome_processes(self):
        """Принудительное завершение всех процессов Chrome"""
        try:
            subprocess.run(["pkill", "-9", "-f", "chrome"], check=False)
            subprocess.run(["pkill", "-9", "-f", "chromedriver"], check=False)
            subprocess.run(["pkill", "-9", "-f", "chromium"], check=False)
            subprocess.run(["rm", "-rf", "/tmp/.com.google.Chrome*"], shell=True, check=False)
            subprocess.run(["rm", "-rf", "/tmp/chrome*"], shell=True, check=False)
            logger.info("Все процессы Chrome принудительно завершены")
        except Exception as e:
            logger.warning(f"Ошибка при завершении процессов Chrome: {e}")
    
    async def _take_step_screenshot(self, driver, step_name: str, telegram_bot = None, chat_id: int = None, email: str = None) -> None:
        """Отправка скриншота текущего этапа в Telegram"""
        if not telegram_bot or not chat_id:
            return
            
        try:
            screenshot = driver.get_screenshot_as_png()
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
    
    async def _bypass_press_hold_captcha(self, driver) -> bool:
        """Обход капчи PRESS & HOLD"""
        try:
            logger.info("Ищем кнопку PRESS & HOLD...")
            
            # Различные селекторы для кнопки капчи
            captcha_selectors = [
                "button[data-testid*='captcha']",
                "button[class*='captcha']",
                "button[class*='press']",
                "button[class*='hold']",
                "div[class*='captcha'] button",
                "div[class*='press'] button",
                "div[class*='hold'] button",
                "//button[contains(text(), 'PRESS')]",
                "//button[contains(text(), 'HOLD')]",
                "//button[contains(text(), 'Press')]",
                "//button[contains(text(), 'Hold')]",
                "//button[contains(text(), 'press')]",
                "//button[contains(text(), 'hold')]",
                "//div[contains(text(), 'PRESS')]//button",
                "//div[contains(text(), 'HOLD')]//button"
            ]
            
            captcha_button = None
            for selector in captcha_selectors:
                try:
                    if selector.startswith("//"):
                        captcha_button = driver.find_element(By.XPATH, selector)
                    else:
                        captcha_button = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if captcha_button and captcha_button.is_displayed():
                        logger.info(f"Кнопка капчи найдена с селектором: {selector}")
                        break
                except:
                    continue
            
            if not captcha_button:
                logger.warning("Кнопка капчи не найдена")
                return False
            
            logger.info("Начинаем обход капчи PRESS & HOLD...")
            
            # Используем ActionChains для click_and_hold
            actions = ActionChains(driver)
            
            # Нажимаем и удерживаем кнопку
            hold_time = random.uniform(7, 9)  # 7-9 секунд как просил пользователь
            logger.info(f"Удерживаем кнопку {hold_time:.1f} секунд...")
            
            actions.click_and_hold(captcha_button).perform()
            await asyncio.sleep(hold_time)
            actions.release(captcha_button).perform()
            
            logger.info("Кнопка отпущена, ждем результат...")
            await asyncio.sleep(3)
            
            # Проверяем, исчезла ли капча
            page_source = driver.page_source
            if "PRESS" not in page_source and "HOLD" not in page_source:
                logger.info("Капча успешно обойдена!")
                return True
            else:
                logger.warning("Капча не исчезла, возможно нужна повторная попытка")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при обходе капчи: {e}")
            return False
    
    async def _register_with_captcha_bypass(self, email: str, username: str, password: str, telegram_bot = None, chat_id: int = None) -> Dict[str, Any]:
        """Регистрация с обходом капчи через браузер"""
        try:
            # Убиваем все процессы Chrome
            await self._kill_chrome_processes()
            await asyncio.sleep(2)
            
            # Настраиваем Chrome
            options = self._setup_chrome_options()
            
            # Запускаем браузер
            logger.info("Запускаем браузер для регистрации...")
            self.driver = webdriver.Chrome(options=options)
            
            # Устанавливаем размер окна
            self.driver.set_window_size(1920, 1080)
            
            # Скрываем признаки автоматизации
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array")
            self.driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise")
            self.driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol")
            
            # Переходим на главную страницу (где происходит регистрация)
            logger.info("Переходим на главную страницу Fiverr...")
            self.driver.get("https://it.fiverr.com/")
            
            # Ждем загрузки
            await asyncio.sleep(3)
            
            # Скриншот главной страницы
            await self._take_step_screenshot(self.driver, "Главная страница Fiverr", telegram_bot, chat_id, email)
            
            # Проверяем, есть ли капча
            page_source = self.driver.page_source
            if "PRESS" in page_source and "HOLD" in page_source:
                logger.info("Обнаружена капча PRESS & HOLD, пытаемся обойти...")
                
                # Скриншот перед обходом капчи
                await self._take_step_screenshot(self.driver, "Обнаружена капча", telegram_bot, chat_id, email)
                
                # Обходим капчу
                captcha_bypassed = await self._bypass_press_hold_captcha(self.driver)
                
                if not captcha_bypassed:
                    logger.error("Не удалось обойти капчу")
                    return {
                        "success": False,
                        "error": "Не удалось обойти капчу PRESS & HOLD"
                    }
                
                logger.info("Капча успешно обойдена, продолжаем регистрацию...")
                
                # Скриншот после обхода капчи
                await self._take_step_screenshot(self.driver, "Капча обойдена", telegram_bot, chat_id, email)
            
            # Теперь заполняем форму регистрации на главной странице
            try:
                # Ищем поля формы регистрации
                email_selectors = [
                    "input[name='user[email]']",
                    "input[type='email']",
                    "input[placeholder*='email' i]",
                    "input[placeholder*='Email' i]",
                    "input[id*='email']",
                    "input[class*='email']"
                ]
                
                password_selectors = [
                    "input[name='user[password]']",
                    "input[type='password']",
                    "input[placeholder*='password' i]",
                    "input[placeholder*='Password' i]",
                    "input[id*='password']",
                    "input[class*='password']"
                ]
                
                username_selectors = [
                    "input[name='user[username]']",
                    "input[placeholder*='username' i]",
                    "input[placeholder*='Username' i]",
                    "input[id*='username']",
                    "input[class*='username']"
                ]
                
                # Находим поля
                email_field = None
                password_field = None
                username_field = None
                
                for selector in email_selectors:
                    try:
                        email_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if email_field and email_field.is_displayed():
                            break
                    except:
                        continue
                
                for selector in password_selectors:
                    try:
                        password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if password_field and password_field.is_displayed():
                            break
                    except:
                        continue
                
                for selector in username_selectors:
                    try:
                        username_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if username_field and username_field.is_displayed():
                            break
                    except:
                        continue
                
                if not email_field or not password_field:
                    logger.error("Не найдены обязательные поля формы")
                    return {
                        "success": False,
                        "error": "Не найдены поля email или password"
                    }
                
                # Заполняем поля
                email_field.clear()
                email_field.send_keys(email)
                logger.info("Поле email заполнено")
                
                # Скриншот после заполнения email
                await self._take_step_screenshot(self.driver, "Email заполнен", telegram_bot, chat_id, email)
                
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
                await self._take_step_screenshot(self.driver, "Все поля заполнены", telegram_bot, chat_id, email)
                
                # Ищем кнопку регистрации
                submit_selectors = [
                    "button[type='submit']",
                    "input[type='submit']",
                    "button[class*='submit']",
                    "button[class*='register']",
                    "button[class*='signup']",
                    "button[class*='create']",
                    "//button[contains(text(), 'Register')]",
                    "//button[contains(text(), 'Sign up')]",
                    "//button[contains(text(), 'Create')]",
                    "//button[contains(text(), 'Join')]",
                    "//button[contains(text(), 'register')]",
                    "//button[contains(text(), 'sign up')]",
                    "//button[contains(text(), 'create')]",
                    "//button[contains(text(), 'join')]"
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    try:
                        if selector.startswith("//"):
                            submit_button = self.driver.find_element(By.XPATH, selector)
                        else:
                            submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        if submit_button and submit_button.is_displayed():
                            logger.info(f"Кнопка регистрации найдена с селектором: {selector}")
                            break
                    except:
                        continue
                
                if not submit_button:
                    logger.error("Кнопка регистрации не найдена")
                    return {
                        "success": False,
                        "error": "Кнопка регистрации не найдена"
                    }
                
                # Нажимаем кнопку
                submit_button.click()
                logger.info("Кнопка регистрации нажата")
                
                # Скриншот после нажатия кнопки регистрации
                await self._take_step_screenshot(self.driver, "Кнопка регистрации нажата", telegram_bot, chat_id, email)
                
                # Ждем результата
                await asyncio.sleep(5)
                
                # Проверяем успешность регистрации
                current_url = self.driver.current_url
                page_source = self.driver.page_source
                
                if "success" in page_source.lower() or "welcome" in page_source.lower() or "dashboard" in current_url:
                    logger.info("Регистрация успешна!")
                    
                    # Скриншот успешной регистрации
                    await self._take_step_screenshot(self.driver, "Регистрация успешна!", telegram_bot, chat_id, email)
                    
                    # Получаем cookies
                    cookies = {}
                    for cookie in self.driver.get_cookies():
                        cookies[cookie['name']] = cookie['value']
                    
                    return {
                        "success": True,
                        "email": email,
                        "username": username,
                        "password": password,
                        "cookies": cookies,
                        "confirmation_code": None
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
            logger.error(f"Критическая ошибка при регистрации: {e}")
            return {
                "success": False,
                "error": f"Критическая ошибка: {str(e)}"
            }
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
    
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
                domains_result = await email_service.get_available_domains()
                if domains_result and domains_result.get("status") == "success":
                    available_domains = domains_result.get("data", [])
                    if available_domains:
                        selected_domain = available_domains[0]
                        logger.info(f"Используем выбранный домен: {selected_domain}")
                    else:
                        logger.warning("Нет доступных доменов, используем gmx.com")
                        selected_domain = "gmx.com"
                else:
                    logger.warning("Не удалось получить домены, используем gmx.com")
                    selected_domain = "gmx.com"
                
                # Заказываем email
                email_result = await email_service.order_email(selected_domain)
                if not email_result.get("email"):
                    logger.error(f"Не удалось заказать email для аккаунта {i+1}")
                    results.append({
                        "success": False,
                        "error": "Не удалось заказать email",
                        "account_number": i+1
                    })
                    continue
                
                email = email_result["email"]
                email_id = email_result.get("id")
                logger.info(f"Получен email: {email}")
                
                # Регистрируем аккаунт
                result = await registrator.register_account(
                    email=email,
                    email_service=email_service,
                    email_id=email_id,
                    telegram_bot=telegram_bot,
                    chat_id=chat_id
                )
                
                result["account_number"] = i+1
                results.append(result)
                
                if result.get("success"):
                    logger.info(f"✅ Аккаунт {i+1} успешно зарегистрирован!")
                else:
                    logger.error(f"❌ Ошибка регистрации аккаунта {i+1}: {result.get('error', 'Неизвестная ошибка')}")
                
                # Задержка между регистрациями
                if i < count - 1:
                    delay = random.uniform(10, 30)
                    logger.info(f"Ждем {delay:.1f} секунд перед следующей регистрацией...")
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"❌ Критическая ошибка при регистрации аккаунта {i+1}: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "account_number": i+1
                })
    
    return results
