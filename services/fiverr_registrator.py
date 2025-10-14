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
        Генерация СЛУЧАЙНОГО НАБОРА СИМВОЛОВ в формате: xxxxx_yyyyy
        МАКСИМУМ 15 символов (лимит Fiverr)!
        
        Args:
            base_name: Не используется
            
        Returns:
            Случайный username типа psodx_iusyds (text_text), max 15 chars
        """
        # Генерируем случайные строки из букв
        letters = 'abcdefghijklmnopqrstuvwxyz'
        
        # Первая часть: 5-6 букв (чтобы влезло в 15 с подчеркиванием)
        first_part_length = random.randint(5, 6)
        first_part = ''.join(random.choice(letters) for _ in range(first_part_length))
        
        # Вторая часть: точно вычисляем чтобы НЕ ПРЕВЫСИТЬ 15 символов
        # 15 - len(first_part) - 1 (подчеркивание) = длина второй части
        second_part_length = 15 - first_part_length - 1  # Ровно 15!
        second_part = ''.join(random.choice(letters) for _ in range(second_part_length))
        
        username = f"{first_part}_{second_part}"
        
        # Проверка что не больше 15
        if len(username) > 15:
            username = username[:15]
        
        logger.debug(f"Сгенерирован случайный username: {username} (длина: {len(username)})")
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
    
    async def _js_click(self, selector: str, timeout: int = 10000) -> bool:
        """
        Клик на элемент через JavaScript (более надежный чем page.click)
        
        Args:
            selector: CSS селектор элемента
            timeout: Таймаут ожидания элемента в миллисекундах
            
        Returns:
            True если клик успешен, False иначе
        """
        try:
            # Ждем появления элемента
            await self.page.wait_for_selector(selector, timeout=timeout, state='visible')
            
            # Кликаем через JavaScript
            clicked = await self.page.evaluate(f'''
                () => {{
                    const element = document.querySelector('{selector}');
                    if (element) {{
                        element.click();
                        return true;
                    }}
                    return false;
                }}
            ''')
            
            if clicked:
                logger.debug(f"✅ JS клик успешен: {selector}")
                return True
            else:
                logger.warning(f"⚠️ Элемент не найден для JS клика: {selector}")
                return False
                
        except Exception as e:
            logger.debug(f"❌ Ошибка JS клика на {selector}: {e}")
            return False
    
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
            # Проверяем прокси перед началом (если указан) - НЕ блокирующая проверка
            if self.proxy:
                logger.info(f"Проверка прокси {self.proxy}...")
                from services.proxy_manager import ProxyManager
                # Даем прокси шанс - проверка не критична
                await ProxyManager.check_proxy(self.proxy, timeout=20)
                # Продолжаем даже если проверка не прошла - прокси может работать с Fiverr
            
            # Инициализируем браузер
            await self._init_browser()
            
            # Проверяем доступные почтовые домены для fiverr.com
            logger.info("Проверка доступных почтовых доменов для fiverr.com...")
            available_domains = await self.email_service.get_available_emails(site="fiverr.com")
            
            if not available_domains:
                logger.error("Не удалось получить список доступных доменов")
                return None
            
            # Выбираем первый домен с count > 0
            selected_domain = None
            for domain, info in available_domains.items():
                if info.get("count", 0) > 0:
                    selected_domain = domain
                    logger.info(f"Выбран домен: {domain} (доступно: {info['count']} шт., цена: ${info['price']})")
                    break
            
            if not selected_domain:
                logger.error("Нет доступных почтовых доменов для fiverr.com")
                return None
            
            # Заказываем почту с выбранным доменом
            logger.info(f"Заказ email на домене {selected_domain}...")
            email_data = await self.email_service.order_email(
                site="fiverr.com",
                domain=selected_domain,
                regex=r"\d{6}"  # Ищем 6-значный код в письме
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
            try:
                # Используем менее строгое условие загрузки для медленных прокси
                await self.page.goto("https://it.fiverr.com", wait_until="domcontentloaded", timeout=90000)
                logger.info("Страница загружена, ожидание готовности...")
                await self._wait_random(3, 5)
            except Exception as e:
                logger.error(f"Ошибка загрузки страницы: {e}")
                logger.info("Пробуем альтернативный метод загрузки...")
                try:
                    # Пробуем без wait_until
                    await self.page.goto("https://it.fiverr.com", timeout=90000)
                    await self._wait_random(5, 7)
                except Exception as e2:
                    logger.error(f"Не удалось загрузить страницу: {e2}")
                    await self.email_service.cancel_email(activation_id)
                    return None
            
            # ШАГ 2: Нажимаем на кнопку "Sign in" (Accedi/Войти)
            logger.info("Клик на кнопку Sign in...")
            try:
                # Селектор: a[href="/login?source=top_nav"]
                clicked = await self._js_click('a.nav-link[href*="/login"]', timeout=15000)
                if not clicked:
                    raise Exception("Sign in button not clicked")
                logger.info("✅ Кликнули на Sign in")
                
                # ВАЖНО: Ждем появления модального окна с опциями логина/регистрации
                logger.info("Ожидание появления модального окна с опциями...")
                await self._wait_random(2, 4)
                
            except:
                logger.warning("Кнопка Sign in не найдена, переходим напрямую на /login")
                try:
                    await self.page.goto("https://it.fiverr.com/login", wait_until="domcontentloaded", timeout=90000)
                    await self._wait_random(3, 5)
                except Exception as e:
                    logger.error(f"Не удалось открыть страницу логина: {e}")
                    await self.email_service.cancel_email(activation_id)
                    return None
            
            # ШАГ 3: Ждем и кликаем на кнопку "Continue with email/username"
            logger.info("Поиск кнопки 'Continue with email/username'...")
            try:
                # Сначала ждем появления текста внутри кнопки
                logger.info("Ожидание появления текста 'Continue with email/username'...")
                text_selector = 'p[data-track-tag="text"]._ifhvih'
                
                try:
                    await self.page.wait_for_selector(text_selector, timeout=15000, state='visible')
                    logger.info(f"✅ Текст кнопки найден: {text_selector}")
                except Exception as e:
                    logger.error(f"❌ Текст кнопки не появился за 15 секунд: {e}")
                    await self.email_service.cancel_email(activation_id)
                    return None
                
                # Теперь находим родительский элемент (кнопку/div) и кликаем на него
                logger.info("Поиск родительской кнопки для клика...")
                
                # ИЩЕМ КЛИКАБЕЛЬНЫЙ ЭЛЕМЕНТ (с cursor: pointer)
                logger.info("Поиск КЛИКАБЕЛЬНОГО элемента с текстом кнопки...")
                clickable_info = await self.page.evaluate('''
                    () => {
                        // Ищем ВСЕ <p> с data-track-tag="text"
                        const allP = document.querySelectorAll('p[data-track-tag="text"]._ifhvih');
                        
                        const results = [];
                        allP.forEach((p, index) => {
                            // Ищем родителя с cursor: pointer
                            let parent = p.parentElement;
                            let depth = 0;
                            let clickableParent = null;
                            
                            while (parent && depth < 10) {
                                const style = window.getComputedStyle(parent);
                                if (style.cursor === 'pointer' || parent.getAttribute('role') === 'button') {
                                    clickableParent = {
                                        tag: parent.tagName,
                                        role: parent.getAttribute('role'),
                                        cursor: style.cursor,
                                        class: parent.className
                                    };
                                    break;
                                }
                                parent = parent.parentElement;
                                depth++;
                            }
                            
                            results.push({
                                index: index,
                                text: p.textContent.substring(0, 50),
                                clickableParent: clickableParent
                            });
                        });
                        
                        return results;
                    }
                ''')
                
                logger.info(f"Найдено элементов: {clickable_info}")
                
                # Кликаем на родителя с cursor: pointer И текстом "email" или "username"
                logger.info("Клик на кнопку 'Continue with email/username'...")
                clicked = await self.page.evaluate('''
                    () => {
                        // Ищем ВСЕ <p> с data-track-tag="text"
                        const allP = document.querySelectorAll('p[data-track-tag="text"]._ifhvih');
                        
                        for (const p of allP) {
                            const text = p.textContent.toLowerCase();
                            
                            // Проверяем что текст содержит "email" или "username"
                            if (!text.includes('email') && !text.includes('username')) {
                                continue;
                            }
                            
                            console.log('Найден нужный текст:', p.textContent);
                            
                            // Ищем родителя с cursor: pointer
                            let parent = p.parentElement;
                            let depth = 0;
                            
                            while (parent && depth < 10) {
                                const style = window.getComputedStyle(parent);
                                if (style.cursor === 'pointer' || parent.getAttribute('role') === 'button') {
                                    console.log('Найден кликабельный элемент:', parent.tagName);
                                    parent.click();
                                    return true;
                                }
                                parent = parent.parentElement;
                                depth++;
                            }
                        }
                        
                        console.log('Кнопка с email/username не найдена');
                        return false;
                    }
                ''')
                
                if not clicked:
                    logger.error("❌ Не найден кликабельный элемент с cursor: pointer")
                    await self.email_service.cancel_email(activation_id)
                    return None
                
                logger.info("✅ Кликнули на кликабельный элемент")
                
                # ВАЖНО: Форма открывается в модальном окне (URL НЕ меняется!)
                # Даем время на анимацию открытия модального окна
                logger.info("Ожидание открытия модального окна с формой...")
                await self._wait_random(2, 3)
                
                # СКРИНШОТ для debug
                try:
                    screenshot_path = f"/tmp/fiverr_modal_{email}.png"
                    await self.page.screenshot(path=screenshot_path, full_page=True)
                    logger.info(f"Скриншот сохранен: {screenshot_path}")
                except:
                    pass
                
                try:
                    await self.page.wait_for_selector(
                        'input#identification-usernameOrEmail, input[name="usernameOrEmail"]',
                        timeout=15000,
                        state='visible'
                    )
                    logger.info("✅ Форма email/password загрузилась!")
                except Exception as e:
                    logger.error(f"❌ Форма не появилась за 15 секунд: {e}")
                    
                    # Debug: ПОЛНАЯ ДИАГНОСТИКА
                    logger.error("=== ДИАГНОСТИКА МОДАЛЬНОГО ОКНА ===")
                    
                    # 1. Все input на странице
                    modal_check = await self.page.evaluate('''
                        () => {
                            const allInputs = document.querySelectorAll('input');
                            const inputs = [];
                            allInputs.forEach(input => {
                                const rect = input.getBoundingClientRect();
                                inputs.push({
                                    type: input.type,
                                    name: input.name,
                                    id: input.id,
                                    placeholder: input.placeholder,
                                    visible: input.offsetParent !== null,
                                    inViewport: rect.top >= 0 && rect.left >= 0
                                });
                            });
                            return inputs;
                        }
                    ''')
                    logger.error(f"ВСЕ INPUT: {modal_check}")
                    
                    # 2. HTML модального окна (если есть)
                    modal_html = await self.page.evaluate('''
                        () => {
                            const modal = document.querySelector('[role="dialog"], .modal, [data-modal]');
                            if (modal) return modal.innerHTML.substring(0, 500);
                            return "Модальное окно не найдено";
                        }
                    ''')
                    logger.error(f"HTML МОДАЛЬНОГО ОКНА: {modal_html}")
                    
                    await self.email_service.cancel_email(activation_id)
                    return None
                    
            except Exception as e:
                logger.error(f"Ошибка клика на кнопку email: {e}")
                await self.email_service.cancel_email(activation_id)
                return None
            
            # ШАГ 4: Заполняем email и пароль
            logger.info("Заполнение email и пароля...")
            
            # Вводим email - точные селекторы из HTML
            email_input_selectors = [
                'input#identification-usernameOrEmail',  # ID из HTML
                'input[name="usernameOrEmail"]',  # name из HTML
                'input[autocomplete="email"]',  # autocomplete атрибут
                'input[type="text"][data-track-tag="input"]',  # Универсальный
            ]
            
            email_filled = False
            for selector in email_input_selectors:
                try:
                    # Проверяем что элемент видим и доступен
                    await self.page.wait_for_selector(selector, timeout=5000, state='visible')
                    await self.page.fill(selector, email)
                    email_filled = True
                    logger.info(f"✅ Email '{email}' введен через селектор: {selector}")
                    await self._wait_random(1, 2)
                    break
                except Exception as e:
                    logger.debug(f"Селектор {selector} не сработал: {e}")
                    continue
            
            if not email_filled:
                logger.error("❌ Не удалось найти поле email")
                logger.error(f"Текущий URL: {self.page.url}")
                # Попытка получить список всех input на странице для отладки
                try:
                    inputs = await self.page.query_selector_all('input')
                    logger.error(f"Всего найдено input элементов: {len(inputs)}")
                    for i, inp in enumerate(inputs[:5]):  # Первые 5
                        inp_type = await inp.get_attribute('type')
                        inp_name = await inp.get_attribute('name')
                        inp_id = await inp.get_attribute('id')
                        logger.error(f"Input {i}: type={inp_type}, name={inp_name}, id={inp_id}")
                except:
                    pass
                await self.email_service.cancel_email(activation_id)
                return None
            
            # Вводим пароль - точные селекторы из HTML
            password_input_selectors = [
                'input#identification-password',  # ID из HTML
                'input[name="password"][autocomplete="current-password"]',  # name + autocomplete
                'input[type="password"][data-track-tag="input"]',  # type + data-track
                'input[type="password"]',  # Универсальный fallback
            ]
            
            password_filled = False
            for selector in password_input_selectors:
                try:
                    await self.page.fill(selector, password)
                    password_filled = True
                    logger.info(f"✅ Пароль введен через селектор: {selector}")
                    await self._wait_random(1, 2)
                    break
                except Exception as e:
                    logger.debug(f"Селектор {selector} не сработал: {e}")
                    continue
            
            if not password_filled:
                logger.error("❌ Не удалось найти поле пароля")
                await self.email_service.cancel_email(activation_id)
                return None
            
            # ШАГ 5: Нажимаем "Continua" (submit button)
            logger.info("Отправка формы через клик на кнопку Submit...")
            try:
                # НАХОДИМ и КЛИКАЕМ на кнопку Submit (form.submit() не работает - JS блокирует!)
                submit_clicked = await self.page.evaluate('''
                    () => {
                        // Ищем кнопку submit по разным критериям
                        const submitButton = 
                            document.querySelector('button[type="submit"]') ||
                            document.querySelector('button[data-track-tag="button"][type="submit"]') ||
                            document.querySelector('form button[type="submit"]');
                        
                        if (submitButton) {
                            // Кликаем через JavaScript
                            submitButton.click();
                            return true;
                        }
                        return false;
                    }
                ''')
                
                if submit_clicked:
                    logger.info("✅ Кликнули на кнопку Submit!")
                    
                    # URL НЕ МЕНЯЕТСЯ - это модальное окно! Просто ждем обновления контента
                    await self._wait_random(3, 4)
                    
                    # Ждем пока ИСЧЕЗНУТ старые поля email/password (модальное окно обновится)
                    try:
                        logger.info("Ожидание обновления модального окна...")
                        await self.page.wait_for_selector('input#identification-password', state='hidden', timeout=10000)
                        logger.info("✅ Старая форма исчезла, модальное окно обновилось")
                    except:
                        logger.warning("⚠️ Старая форма не исчезла, возможно ошибка валидации")
                        # Проверяем наличие ошибок
                        try:
                            page_text = await self.page.evaluate('() => document.body.innerText')
                            if any(keyword in page_text.lower() for keyword in ['invalid', 'error', 'errore', 'incorrect']):
                                logger.error(f"❌ Обнаружена ошибка валидации! Текст: {page_text[:500]}")
                                await self.email_service.cancel_email(activation_id)
                                return None
                        except:
                            pass
                    
                    await self._wait_random(2, 3)
                else:
                    logger.error("❌ Форма не валидна или не найдена!")
                    # Логируем текст страницы для диагностики
                    try:
                        page_text = await self.page.evaluate('() => document.body.innerText')
                        logger.error(f"Текст страницы: {page_text[:500]}")
                    except:
                        pass
                    await self.email_service.cancel_email(activation_id)
                    return None
                    
            except Exception as e:
                logger.error(f"Ошибка отправки формы: {e}")
                await self.email_service.cancel_email(activation_id)
                return None
            
            # ШАГ 6: Вводим username (ОБЯЗАТЕЛЬНОЕ ПОЛЕ!) с проверкой на занятость
            logger.info(f"Ввод username: {username}...")
            
            # ЯВНО ЖДЕМ появления поля username
            logger.info("Ожидание появления поля username...")
            try:
                await self.page.wait_for_selector('input#username', state='visible', timeout=30000)
                logger.info("✅ Поле username появилось!")
            except Exception as e:
                logger.error(f"❌ Поле username не появилось за 30 секунд: {e}")
                # DEBUG: показываем что есть на странице
                try:
                    page_html = await self.page.content()
                    logger.error(f"HTML страницы (первые 1000 символов): {page_html[:1000]}")
                except:
                    pass
            
            # Точные селекторы из HTML (БЕЗ placeholder - это просто текст для примера!)
            username_input_selectors = [
                'input#username',  # ID из HTML - САМЫЙ НАДЕЖНЫЙ
                'input[name="username"][maxlength="15"]',  # name + maxlength
                'input[name="username"][type="text"]',  # name + type
                'input[data-track-tag="input"][name="username"]',  # data-track-tag + name
                'input[name="username"]',  # Универсальный fallback
            ]
            
            # Попытки ввода username с проверкой на занятость
            max_username_attempts = 5
            username_accepted = False
            
            for attempt in range(max_username_attempts):
                # Если это не первая попытка - генерируем новый username
                if attempt > 0:
                    username = self._generate_username()
                    logger.info(f"Попытка {attempt + 1}/{max_username_attempts}: Генерируем новый username: {username}")
                
                # Заполняем поле username
                username_filled = False
                for selector in username_input_selectors:
                    try:
                        logger.debug(f"Поиск username поля через селектор: {selector}")
                        username_field = await self.page.wait_for_selector(selector, timeout=20000, state='visible')
                        
                        # Очищаем поле перед вводом (если это повторная попытка)
                        if attempt > 0:
                            await username_field.fill('')
                            await self._wait_random(0.3, 0.5)
                        
                        await username_field.fill(username)
                        username_filled = True
                        logger.info(f"✅ Username '{username}' введен через селектор: {selector}")
                        await self._wait_random(1, 2)
                        break
                    except Exception as e:
                        logger.debug(f"Селектор {selector} не сработал: {e}")
                        continue
                
                if not username_filled:
                    # DEBUG: Показываем все input на странице
                    try:
                        all_inputs = await self.page.evaluate('''
                            () => {
                                const inputs = document.querySelectorAll('input');
                                return Array.from(inputs).map(inp => ({
                                    id: inp.id,
                                    name: inp.name,
                                    type: inp.type,
                                    placeholder: inp.placeholder,
                                    visible: inp.offsetParent !== null
                                }));
                            }
                        ''')
                        logger.error(f"❌ Все input элементы на странице: {all_inputs}")
                    except:
                        pass
                    
                    logger.error("❌ ОБЯЗАТЕЛЬНОЕ поле username не найдено!")
                    await self.email_service.cancel_email(activation_id)
                    return None
                
                # Проверяем, есть ли ошибка "username занят"
                # Текст ошибки: "Sembra che questo nome utente sia già in uso. Scegline un altro."
                await self._wait_random(1, 2)  # Даем время на появление ошибки
                
                try:
                    # Ищем сообщение об ошибке (может быть на разных языках)
                    error_texts = [
                        'già in uso',  # Итальянский: "уже используется"
                        'already in use',  # Английский
                        'already taken',  # Английский альтернативный
                        'username is taken',  # Английский
                        'Scegline un altro',  # Итальянский: "Выберите другое"
                    ]
                    
                    page_content = await self.page.content()
                    username_taken = any(error_text.lower() in page_content.lower() for error_text in error_texts)
                    
                    if username_taken:
                        logger.warning(f"⚠️ Username '{username}' уже занят! Попытка {attempt + 1}/{max_username_attempts}")
                        continue  # Переходим к следующей попытке с новым username
                    else:
                        # Username не занят, можно продолжать
                        logger.info(f"✅ Username '{username}' свободен!")
                        username_accepted = True
                        break
                        
                except Exception as e:
                    logger.debug(f"Ошибка при проверке занятости username: {e}")
                    # Если не можем проверить - считаем что username свободен
                    username_accepted = True
                    break
            
            if not username_accepted:
                logger.error(f"❌ Не удалось подобрать свободный username за {max_username_attempts} попыток")
                await self.email_service.cancel_email(activation_id)
                return None
            
            # ШАГ 7: Нажимаем "Crea il mio account" (submit button)
            logger.info("Клик на кнопку создания аккаунта (submit)...")
            try:
                # Пробуем разные селекторы через JS
                selectors = [
                    'button[type="submit"][data-track-tag="button"]',
                    'button[type="submit"]',
                ]
                
                clicked = False
                for selector in selectors:
                    # Проверяем сколько кнопок с таким селектором
                    button_count = await self.page.evaluate(f'''
                        () => document.querySelectorAll('{selector}').length
                    ''')
                    
                    if button_count >= 2:
                        # Кликаем на вторую кнопку через JS
                        clicked = await self.page.evaluate(f'''
                            () => {{
                                const buttons = document.querySelectorAll('{selector}');
                                if (buttons.length >= 2) {{
                                    buttons[1].click();
                                    return true;
                                }}
                                return false;
                            }}
                        ''')
                        if clicked:
                            logger.info(f"✅ Кликнули на вторую submit кнопку: {selector}")
                            break
                    elif button_count == 1:
                        # Кликаем на единственную через JS
                        if await self._js_click(selector, timeout=5000):
                            clicked = True
                            logger.info(f"✅ Кликнули на единственную submit кнопку: {selector}")
                            break
                
                if not clicked:
                    logger.error("❌ Не удалось нажать кнопку создания аккаунта")
                    await self.email_service.cancel_email(activation_id)
                    return None
                
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
            
            # Ищем поля для ввода кода - точные селекторы из HTML
            try:
                # Пробуем найти поля для одноразового кода
                code_inputs = await self.page.query_selector_all('input[autocomplete="one-time-code"]')
                
                # Если не нашли по autocomplete, пробуем другие селекторы
                if not code_inputs:
                    code_inputs = await self.page.query_selector_all('input[inputmode="numeric"][pattern="[0-9]*"]')
                
                if not code_inputs:
                    code_inputs = await self.page.query_selector_all('input[maxlength="6"][type="text"]')
                
                if len(code_inputs) >= 6:
                    # 6 отдельных полей - вводим целый код в первое поле
                    # Fiverr автоматически распределит цифры по полям
                    logger.info("Найдено 6 полей для кода, вводим весь код в первое поле...")
                    await code_inputs[0].fill(confirmation_code)
                    logger.info(f"✅ Код {confirmation_code} введен")
                    await self._wait_random(1, 2)
                elif len(code_inputs) == 1:
                    # Одно поле - вводим весь код
                    logger.info("Найдено одно поле для кода...")
                    await code_inputs[0].fill(confirmation_code)
                    logger.info(f"✅ Код {confirmation_code} введен")
                    await self._wait_random(1, 2)
                else:
                    # Fallback - пробуем общие селекторы
                    logger.warning(f"Найдено {len(code_inputs)} полей для кода, пробуем fallback селекторы...")
                    code_selectors = [
                        'input[name="code"]',
                        'input[placeholder*="codice"]',
                        'input[placeholder*="code"]',
                        'input[type="text"][data-track-tag="input"]'
                    ]
                    
                    filled = False
                    for selector in code_selectors:
                        try:
                            await self.page.fill(selector, confirmation_code)
                            logger.info(f"✅ Код введен через селектор: {selector}")
                            await self._wait_random(1, 2)
                            filled = True
                            break
                        except:
                            continue
                    
                    if not filled:
                        logger.error("❌ Не удалось найти поле для кода")
                        return None
                
                # ШАГ 10: Нажимаем "Invia" (submit/role button)
                logger.info("Клик на кнопку Invia...")
                # Селектор: button[role="button"] или button[data-track-tag="button"]
                selectors = [
                    'button[role="button"][data-track-tag="button"]',
                    'button[role="button"]._arosdn',
                    'button[role="button"]',
                    'button[data-track-tag="button"]',
                ]
                
                clicked = False
                for selector in selectors:
                    if await self._js_click(selector, timeout=5000):
                        clicked = True
                        logger.info(f"✅ Кликнули Invia через: {selector}")
                        await self._wait_random(3, 5)
                        break
                
                if not clicked:
                    logger.error("❌ Не удалось нажать кнопку Invia")
                    return None
                
            except Exception as e:
                logger.error(f"Ошибка при вводе кода: {e}")
                return None
            
            # ШАГ 11: Проходим онбординг (3 вопроса)
            logger.info("Прохождение онбординга...")
            for i in range(3):
                try:
                    # Выбираем левый чекбокс (первый вариант) через JS
                    checkbox_clicked = await self.page.evaluate('''
                        () => {
                            const checkboxes = document.querySelectorAll('input[type="checkbox"], input[type="radio"]');
                            if (checkboxes.length > 0) {
                                checkboxes[0].click();
                                return true;
                            }
                            return false;
                        }
                    ''')
                    
                    if checkbox_clicked:
                        logger.debug(f"✅ Чекбокс выбран для вопроса {i+1}")
                        await self._wait_random(0.5, 1)
                    
                    # Нажимаем "Avanti" (role="button")
                    # Селектор: button[role="button"][data-track-tag="button"]
                    selectors = [
                        'button[role="button"][data-track-tag="button"]',
                        'button[role="button"]._arosdn',
                        'button[role="button"]',
                    ]
                    
                    clicked = False
                    for selector in selectors:
                        if await self._js_click(selector, timeout=5000):
                            clicked = True
                            logger.info(f"✅ Вопрос {i+1}/3 пройден")
                            await self._wait_random(2, 3)
                            break
                    
                    if not clicked:
                        logger.warning(f"⚠️ Не удалось нажать кнопку на вопросе {i+1}, возможно онбординг завершен")
                        break
                        
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

