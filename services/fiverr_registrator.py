"""
Модуль для автоматизации регистрации аккаунтов на Fiverr
"""
import asyncio
import random
import string
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from fake_useragent import UserAgent
from utils.logger import logger
from config import FIVERR_SIGNUP_URL, BROWSER_HEADLESS, BROWSER_TIMEOUT, COOKIES_DIR
from services.email_api import EmailAPIService
from services.proxy_manager import ProxyConfig


class FiverrRegistrator:
    """Класс для автоматизации регистрации на Fiverr"""
    
    def __init__(
        self,
        email_service: EmailAPIService,
        proxy: Optional[ProxyConfig] = None
    ):
        self.email_service = email_service
        self.proxy = proxy
        self.ua = UserAgent()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    def _generate_password(self, length: int = 16) -> str:
        """
        Генерация случайного пароля
        
        Args:
            length: Длина пароля
            
        Returns:
            Сгенерированный пароль
        """
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(characters) for _ in range(length))
        logger.debug(f"Сгенерирован пароль длиной {length}")
        return password
    
    def _generate_username(self) -> str:
        """
        Генерация случайного username
        
        Returns:
            Сгенерированный username
        """
        prefix = ''.join(random.choices(string.ascii_lowercase, k=3))
        suffix = ''.join(random.choices(string.digits, k=4))
        username = f"{prefix}_{suffix}_user"
        return username
    
    async def _init_browser(self):
        """Инициализация браузера с настройками"""
        playwright = await async_playwright().start()
        
        # Настройки запуска браузера
        launch_options = {
            "headless": BROWSER_HEADLESS,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security"
            ]
        }
        
        # Добавляем прокси если указан
        if self.proxy:
            launch_options["proxy"] = self.proxy.to_playwright_format()
            logger.info(f"Используется прокси: {self.proxy}")
        
        self.browser = await playwright.chromium.launch(**launch_options)
        
        # Создаем контекст с user agent
        context_options = {
            "user_agent": self.ua.random,
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-US",
            "timezone_id": "America/New_York"
        }
        
        self.context = await self.browser.new_context(**context_options)
        
        # Добавляем стелс-скрипт для обхода детекции
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(BROWSER_TIMEOUT)
        
        logger.info("Браузер инициализирован")
    
    async def _close_browser(self):
        """Закрытие браузера"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        logger.info("Браузер закрыт")
    
    async def _wait_random(self, min_seconds: float = 1, max_seconds: float = 3):
        """Случайная задержка для имитации человеческого поведения"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def register_account(self) -> Optional[Dict[str, Any]]:
        """
        Регистрация нового аккаунта на Fiverr
        
        Returns:
            Словарь с данными аккаунта или None в случае ошибки
        """
        try:
            # Инициализируем браузер
            await self._init_browser()
            
            # Заказываем почту
            logger.info("Заказ email для регистрации...")
            email_data = await self.email_service.order_email(
                site="fiverr.com",
                domain="gmx.com"  # Можно использовать другие домены
            )
            
            if not email_data:
                logger.error("Не удалось заказать email")
                return None
            
            email = email_data['email']
            activation_id = email_data['id']
            logger.info(f"Получен email: {email}")
            
            # Генерируем данные для регистрации
            password = self._generate_password()
            username = self._generate_username()
            
            # Переходим на страницу регистрации
            logger.info(f"Переход на {FIVERR_SIGNUP_URL}")
            await self.page.goto(FIVERR_SIGNUP_URL, wait_until="networkidle")
            await self._wait_random(2, 4)
            
            # Заполняем форму регистрации
            # ВНИМАНИЕ: Селекторы могут измениться, нужно актуализировать
            logger.info("Заполнение формы регистрации...")
            
            try:
                # Вводим email
                email_selector = 'input[name="email"], input[type="email"], #email'
                await self.page.wait_for_selector(email_selector, timeout=10000)
                await self.page.fill(email_selector, email)
                await self._wait_random(0.5, 1.5)
                
                # Вводим пароль
                password_selector = 'input[name="password"], input[type="password"], #password'
                await self.page.fill(password_selector, password)
                await self._wait_random(0.5, 1.5)
                
                # Вводим username (если требуется)
                try:
                    username_selector = 'input[name="username"], #username'
                    await self.page.fill(username_selector, username)
                    await self._wait_random(0.5, 1.5)
                except:
                    logger.debug("Поле username не найдено или не требуется")
                
                # Нажимаем кнопку регистрации
                submit_selector = 'button[type="submit"], button.join-button, .sign-up-button'
                await self.page.click(submit_selector)
                
                logger.info("Форма отправлена, ожидание подтверждения...")
                await self._wait_random(3, 5)
                
            except Exception as e:
                logger.error(f"Ошибка заполнения формы: {e}")
                await self.email_service.cancel_email(activation_id)
                return None
            
            # Ожидаем письмо с подтверждением
            logger.info("Ожидание письма с подтверждением...")
            message_data = await self.email_service.get_message(
                activation_id=activation_id,
                max_retries=60,
                retry_interval=5
            )
            
            if not message_data:
                logger.error("Не удалось получить письмо с подтверждением")
                return None
            
            confirmation_code = message_data['value']
            logger.info(f"Получен код подтверждения: {confirmation_code}")
            
            # Вводим код подтверждения (если требуется)
            try:
                code_selector = 'input[name="code"], input[placeholder*="code"], #verification-code'
                await self.page.wait_for_selector(code_selector, timeout=10000)
                await self.page.fill(code_selector, confirmation_code)
                await self._wait_random(0.5, 1.5)
                
                # Подтверждаем код
                confirm_button_selector = 'button[type="submit"], .verify-button, .confirm-button'
                await self.page.click(confirm_button_selector)
                await self._wait_random(3, 5)
                
                logger.info("Код подтверждения введен")
            except Exception as e:
                logger.warning(f"Возможно, подтверждение по email не требуется: {e}")
            
            # Проверяем успешность регистрации
            # Обычно при успешной регистрации происходит редирект на главную или профиль
            current_url = self.page.url
            
            if "fiverr.com" in current_url and "join" not in current_url:
                logger.info("Регистрация успешна!")
                
                # Получаем cookies
                cookies = await self.context.cookies()
                cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                
                # Сохраняем cookies в файл
                import json
                cookies_file = COOKIES_DIR / f"{email.replace('@', '_at_')}.json"
                with open(cookies_file, 'w') as f:
                    json.dump(cookies, f, indent=2)
                
                logger.info(f"Cookies сохранены в {cookies_file}")
                
                # Формируем результат
                result = {
                    "email": email,
                    "password": password,
                    "username": username,
                    "cookies": cookies,
                    "cookies_file": str(cookies_file),
                    "proxy": str(self.proxy) if self.proxy else None,
                    "success": True
                }
                
                return result
            else:
                logger.error(f"Регистрация не удалась. Текущий URL: {current_url}")
                return None
                
        except Exception as e:
            logger.error(f"Критическая ошибка при регистрации: {e}")
            return None
        finally:
            await self._close_browser()
    
    async def register_multiple_accounts(self, count: int) -> list:
        """
        Регистрация нескольких аккаунтов последовательно
        
        Args:
            count: Количество аккаунтов для регистрации
            
        Returns:
            Список результатов регистрации
        """
        results = []
        
        for i in range(count):
            logger.info(f"Регистрация аккаунта {i + 1}/{count}")
            
            result = await self.register_account()
            
            if result:
                results.append(result)
                logger.info(f"Успешно зарегистрирован аккаунт {i + 1}/{count}")
            else:
                logger.error(f"Не удалось зарегистрировать аккаунт {i + 1}/{count}")
                results.append({
                    "success": False,
                    "error": "Registration failed"
                })
            
            # Задержка между регистрациями
            if i < count - 1:
                delay = random.uniform(10, 30)
                logger.info(f"Задержка {delay:.1f} секунд перед следующей регистрацией...")
                await asyncio.sleep(delay)
        
        return results


async def register_accounts_batch(
    email_service: EmailAPIService,
    proxies: list[ProxyConfig],
    accounts_per_proxy: int
) -> list:
    """
    Параллельная регистрация аккаунтов с использованием нескольких прокси
    
    Args:
        email_service: Сервис для работы с email API
        proxies: Список прокси для использования
        accounts_per_proxy: Количество аккаунтов на один прокси
        
    Returns:
        Список результатов регистрации
    """
    tasks = []
    
    for proxy in proxies:
        registrator = FiverrRegistrator(email_service, proxy)
        task = registrator.register_multiple_accounts(accounts_per_proxy)
        tasks.append(task)
    
    # Выполняем регистрацию параллельно
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Объединяем результаты
    all_results = []
    for result in results:
        if isinstance(result, list):
            all_results.extend(result)
        else:
            logger.error(f"Ошибка в одной из задач: {result}")
    
    return all_results

