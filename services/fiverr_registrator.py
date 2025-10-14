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
    
    def _generate_password(self, length: int = 11) -> str:
        """
        Генерация случайного пароля (9-12 символов, заглавные буквы, цифры)
        
        Args:
            length: Длина пароля (по умолчанию 11)
            
        Returns:
            Сгенерированный пароль
        """
        # Гарантируем минимум 1 заглавную букву, 1 строчную и 1 цифру
        password = [
            random.choice(string.ascii_uppercase),  # Заглавная буква
            random.choice(string.ascii_lowercase),  # Строчная буква
            random.choice(string.digits),           # Цифра
        ]
        
        # Заполняем остальные символы
        remaining = length - 3
        characters = string.ascii_letters + string.digits
        password.extend(random.choices(characters, k=remaining))
        
        # Перемешиваем
        random.shuffle(password)
        password_str = ''.join(password)
        
        logger.debug(f"Сгенерирован пароль длиной {length}")
        return password_str
    
    def _generate_username(self, base_name: str = None) -> str:
        """
        Генерация username в формате text_text (например, Loreisa_browns)
        
        Args:
            base_name: Базовое имя из email (опционально)
            
        Returns:
            Сгенерированный username
        """
        if base_name:
            # Используем имя из email если есть
            parts = base_name.lower().split('_')
            if len(parts) >= 2:
                return base_name.lower()
        
        # Генерируем случайное имя
        first_names = ['loreisa', 'maria', 'john', 'anna', 'david', 'sarah', 'michael', 'emma']
        last_names = ['browns', 'smith', 'johnson', 'wilson', 'taylor', 'anderson', 'thomas']
        
        username = f"{random.choice(first_names)}_{random.choice(last_names)}"
        logger.debug(f"Сгенерирован username: {username}")
        return username
    
    def _extract_code_from_html(self, html_content: str) -> Optional[str]:
        """
        Извлечение 6-значного кода из HTML письма
        
        Args:
            html_content: HTML содержимое письма
            
        Returns:
            6-значный код или None
        """
        import re
        
        # Ищем код в bold тегах или после "Il tuo codice:"
        patterns = [
            r'<b[^>]*>(\d{6})</b>',
            r'<strong[^>]*>(\d{6})</strong>',
            r'\*\*(\d{6})\*\*',
            r'Il tuo codice:\s*\*\*(\d{6})\*\*',
            r'codice:\s*(\d{6})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                code = match.group(1)
                logger.info(f"Извлечен код подтверждения: {code}")
                return code
        
        logger.error("Не удалось извлечь код из письма")
        return None
    
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
        Регистрация нового аккаунта на Fiverr (итальянская версия)
        
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
                domain="gmx.com"
            )
            
            if not email_data:
                logger.error("Не удалось заказать email")
                return None
            
            email = email_data['email']
            activation_id = email_data['id']
            logger.info(f"Получен email: {email}")
            
            # Генерируем данные для регистрации
            password = self._generate_password(11)  # 9-12 символов
            
            # Извлекаем базовое имя из email для username
            email_base = email.split('@')[0]
            username = self._generate_username(email_base)
            
            # ШАГ 1: Переходим на главную страницу Fiverr
            logger.info("Переход на fiverr.com...")
            await self.page.goto("https://it.fiverr.com", wait_until="networkidle")
            await self._wait_random(2, 3)
            
            # ШАГ 2: Нажимаем на кнопку "Accedi" (Войти)
            logger.info("Клик на кнопку Accedi...")
            try:
                await self.page.click('a[href*="/login"]', timeout=10000)
                await self._wait_random(2, 3)
            except:
                logger.warning("Кнопка Accedi не найдена, переходим напрямую")
                await self.page.goto("https://it.fiverr.com/login", wait_until="networkidle")
                await self._wait_random(2, 3)
            
            # ШАГ 3: Клик на "Continua con email/username"
            logger.info("Клик на 'Continua con email/username'...")
            try:
                # Ищем кнопку по тексту
                await self.page.click('text="Continua con email/username"', timeout=10000)
                await self._wait_random(2, 3)
            except:
                logger.warning("Кнопка не найдена по тексту, пробуем альтернативный селектор")
                try:
                    await self.page.click('button:has-text("email")', timeout=5000)
                    await self._wait_random(2, 3)
                except:
                    logger.error("Не удалось найти кнопку для продолжения с email")
            
            # ШАГ 4: Заполняем email и пароль
            logger.info("Заполнение email и пароля...")
            
            # Вводим email
            email_input_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="Email"]',
                'input[placeholder*="email"]'
            ]
            
            email_filled = False
            for selector in email_input_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.fill(selector, email)
                    email_filled = True
                    logger.info(f"Email введен через селектор: {selector}")
                    await self._wait_random(1, 2)
                    break
                except:
                    continue
            
            if not email_filled:
                logger.error("Не удалось найти поле email")
                await self.email_service.cancel_email(activation_id)
                return None
            
            # Вводим пароль
            password_input_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="Password"]',
                'input[placeholder*="password"]'
            ]
            
            password_filled = False
            for selector in password_input_selectors:
                try:
                    await self.page.fill(selector, password)
                    password_filled = True
                    logger.info(f"Пароль введен через селектор: {selector}")
                    await self._wait_random(1, 2)
                    break
                except:
                    continue
            
            if not password_filled:
                logger.error("Не удалось найти поле пароля")
                await self.email_service.cancel_email(activation_id)
                return None
            
            # ШАГ 5: Нажимаем "Continua"
            logger.info("Клик на кнопку Continua...")
            try:
                await self.page.click('button:has-text("Continua")', timeout=10000)
                await self._wait_random(3, 5)
            except:
                # Альтернативный способ - через type=submit
                try:
                    await self.page.click('button[type="submit"]', timeout=5000)
                    await self._wait_random(3, 5)
                except Exception as e:
                    logger.error(f"Не удалось нажать кнопку Continua: {e}")
                    await self.email_service.cancel_email(activation_id)
                    return None
            
            # ШАГ 6: Вводим username
            logger.info(f"Ввод username: {username}...")
            
            username_input_selectors = [
                'input[name="username"]',
                'input[placeholder*="username"]',
                'input[placeholder*="nome"]',
                'input[type="text"]'
            ]
            
            username_filled = False
            for selector in username_input_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.fill(selector, username)
                    username_filled = True
                    logger.info(f"Username введен через селектор: {selector}")
                    await self._wait_random(1, 2)
                    break
                except:
                    continue
            
            if not username_filled:
                logger.warning("Поле username не найдено, возможно не требуется")
            
            # ШАГ 7: Нажимаем "Crea il mio account"
            logger.info("Клик на 'Crea il mio account'...")
            try:
                await self.page.click('button:has-text("Crea il mio account")', timeout=10000)
                await self._wait_random(3, 5)
            except:
                try:
                    await self.page.click('button:has-text("Crea")', timeout=5000)
                    await self._wait_random(3, 5)
                except Exception as e:
                    logger.error(f"Не удалось нажать кнопку создания аккаунта: {e}")
                    await self.email_service.cancel_email(activation_id)
                    return None
            
            # ШАГ 8: Ожидаем письмо с кодом подтверждения (1-3 минуты)
            logger.info("Ожидание письма с кодом подтверждения (до 3 минут)...")
            message_data = await self.email_service.get_message(
                activation_id=activation_id,
                preview=True,  # Получаем HTML версию
                max_retries=36,  # 36 * 5 сек = 3 минуты
                retry_interval=5
            )
            
            if not message_data:
                logger.error("Не удалось получить письмо с кодом")
                return None
            
            # Извлекаем код из HTML письма
            html_content = message_data.get('message', '')
            confirmation_code = self._extract_code_from_html(html_content)
            
            if not confirmation_code:
                # Пробуем value напрямую
                confirmation_code = message_data.get('value', '')
                if not confirmation_code or len(confirmation_code) != 6:
                    logger.error("Не удалось извлечь 6-значный код")
                    return None
            
            logger.info(f"Получен код подтверждения: {confirmation_code}")
            
            # ШАГ 9: Вводим код подтверждения (6 цифр)
            logger.info("Ввод кода подтверждения...")
            
            # Ищем поля для ввода кода (может быть 6 отдельных полей или одно поле)
            try:
                # Пробуем найти отдельные поля для каждой цифры
                code_inputs = await self.page.query_selector_all('input[type="text"]')
                
                if len(code_inputs) == 6:
                    # 6 отдельных полей - вводим по одной цифре
                    for i, digit in enumerate(confirmation_code):
                        await code_inputs[i].fill(digit)
                        await self._wait_random(0.2, 0.5)
                else:
                    # Одно поле - вводим весь код
                    code_selectors = [
                        'input[name="code"]',
                        'input[placeholder*="codice"]',
                        'input[placeholder*="code"]',
                        'input[type="text"]'
                    ]
                    
                    for selector in code_selectors:
                        try:
                            await self.page.fill(selector, confirmation_code)
                            logger.info(f"Код введен через селектор: {selector}")
                            await self._wait_random(1, 2)
                            break
                        except:
                            continue
                
                # ШАГ 10: Нажимаем "Invia"
                logger.info("Клик на кнопку Invia...")
                await self.page.click('button:has-text("Invia")', timeout=10000)
                await self._wait_random(3, 5)
                
            except Exception as e:
                logger.error(f"Ошибка при вводе кода: {e}")
                return None
            
            # ШАГ 11: Проходим онбординг (3 вопроса)
            logger.info("Прохождение онбординга...")
            for i in range(3):
                try:
                    # Выбираем левый чекбокс (первый вариант)
                    checkboxes = await self.page.query_selector_all('input[type="checkbox"], input[type="radio"]')
                    if checkboxes:
                        await checkboxes[0].click()
                        await self._wait_random(0.5, 1)
                    
                    # Нажимаем "Avanti"
                    await self.page.click('button:has-text("Avanti")', timeout=10000)
                    logger.info(f"Вопрос {i+1}/3 пройден")
                    await self._wait_random(2, 3)
                except Exception as e:
                    logger.warning(f"Ошибка на шаге онбординга {i+1}: {e}")
                    # Продолжаем, возможно онбординг уже завершен
                    break
            
            # Проверяем успешность регистрации
            await self._wait_random(2, 3)
            current_url = self.page.url
            
            logger.info(f"Текущий URL после регистрации: {current_url}")
            
            # Получаем cookies
            cookies = await self.context.cookies()
            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            # Сохраняем cookies в файл
            import json
            cookies_file = COOKIES_DIR / f"{email.replace('@', '_at_')}.json"
            with open(cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            logger.info(f"Cookies сохранены в {cookies_file}")
            logger.info("✅ Регистрация завершена успешно!")
            
            # Формируем результат
            result = {
                "email": email,
                "password": password,
                "username": username,
                "cookies": cookies,
                "cookies_file": str(cookies_file),
                "proxy": str(self.proxy) if self.proxy else None,
                "success": True,
                "final_url": current_url
            }
            
            return result
                
        except Exception as e:
            logger.error(f"Критическая ошибка при регистрации: {e}")
            import traceback
            logger.error(traceback.format_exc())
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

