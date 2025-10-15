"""
Модуль для автоматизации регистрации аккаунтов на Fiverr с Selenium
"""
import asyncio
import random
import string
import time
import json
import os
import traceback
from typing import Optional, Dict, Any, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from utils.logger import logger
from config import FIVERR_SIGNUP_URL, BROWSER_HEADLESS, BROWSER_TIMEOUT, COOKIES_DIR
from services.email_api import EmailAPIService
from services.proxy_manager import ProxyConfig


class FiverrRegistrator:
    """Класс для автоматизации регистрации на Fiverr с Selenium"""
    
    def __init__(
        self,
        email_service: EmailAPIService,
        proxy: Optional[ProxyConfig] = None
    ):
        self.email_service = email_service
        self.proxy = proxy
        self.driver = None
    
    def _generate_password(self, length: int = 12) -> str:
        """
        Генерация случайного пароля с гарантированными требованиями
        
        Args:
            length: Длина пароля (по умолчанию 12)
            
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
        
        for _ in range(remaining):
            password.append(random.choice(characters))
        
        # Перемешиваем символы
        random.shuffle(password)
        
        return ''.join(password)
    
    def _generate_username(self) -> str:
        """
        Генерация случайного username в формате text_text (15 символов)
        
        Returns:
            Сгенерированный username
        """
        # Генерируем случайные строки
        first_part_length = random.randint(5, 7)
        second_part_length = 15 - first_part_length - 1  # -1 для подчеркивания
        
        first_part = ''.join(random.choices(string.ascii_lowercase, k=first_part_length))
        second_part = ''.join(random.choices(string.ascii_lowercase, k=second_part_length))
        
        return f"{first_part}_{second_part}"
    
    async def _init_browser(self):
        """Инициализация браузера с настройками"""
        # Создаем Selenium браузер
        options = Options()
        
        # ОТКЛЮЧАЕМ ВСЕ СЛЕДЫ АВТОМАТИЗАЦИИ
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # ОБЫЧНЫЕ НАСТРОЙКИ
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        
        # Уникальная папка для каждого экземпляра
        import tempfile
        import uuid
        user_data_dir = f"/tmp/chrome_user_data_{uuid.uuid4().hex[:8]}"
        options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # USER AGENT
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
        
        # Добавляем прокси если указан
        if self.proxy:
            options.add_argument(f"--proxy-server={self.proxy.to_url()}")
            logger.info(f"Используется прокси: {self.proxy}")
        
        self.driver = webdriver.Chrome(options=options)
        
        # УБИРАЕМ webdriver
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # УБИРАЕМ chrome.runtime
        self.driver.execute_script("delete window.chrome.runtime")
        
        # ПОДДЕЛЫВАЕМ plugins
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
                    {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
                    {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}
                ]
            });
        """)
        
        logger.info("Браузер инициализирован")
    
    async def _close_browser(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            logger.info("Браузер закрыт")
    
    async def _take_screenshot(self, name: str):
        """Создание скриншота"""
        try:
            screenshot_path = f"logs/screenshot_{name}_{int(time.time())}.png"
            os.makedirs("logs", exist_ok=True)
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Скриншот сохранен: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"Ошибка создания скриншота: {e}")
            return None
    
    async def _js_click(self, selector: str, description: str = "элемент") -> bool:
        """Клик через JavaScript"""
        try:
            # Ждем появления элемента
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            # Выполняем клик через JavaScript
            self.driver.execute_script("arguments[0].click();", element)
            
            logger.info(f"✅ Кликнули через JavaScript на {description}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка JavaScript клика на {description}: {e}")
            return False
    
    async def register_account(self, email: str, password: str, username: str) -> Optional[Dict[str, Any]]:
        """Регистрация одного аккаунта"""
        try:
            # Проверка прокси
            if self.proxy:
                logger.info(f"Проверка прокси {self.proxy}...")
                from services.proxy_manager import ProxyManager
                proxy_ok = await ProxyManager.check_proxy(self.proxy)
                if not proxy_ok:
                    logger.warning("⚠️ Прокси не прошел проверку, но продолжаем...")
            
            # Инициализация браузера
            await self._init_browser()
            
            # Заказ email для регистрации
            logger.info("Заказ email для регистрации...")
            
            # Получаем доступные домены
            available_emails = await self.email_service.get_available_emails()
            if not available_emails:
                logger.error("❌ Не удалось получить список доступных доменов")
                return None
            
            # Выбираем первый доступный домен
            selected_domain = None
            for domain, info in available_emails.items():
                if info.get('count', 0) > 0:
                    selected_domain = domain
                    logger.info(f"Выбран домен: {domain} (доступно: {info['count']} шт., цена: ${info['price']})")
                    break
            
            if not selected_domain:
                logger.error("❌ Нет доступных доменов")
                return None
            
            # Заказываем email
            email_result = await self.email_service.order_email(
                site="fiverr.com",
                domain=selected_domain,
                regex=r"\d{6}"  # Ищем 6-значный код
            )
            
            if not email_result:
                logger.error("❌ Не удалось заказать email")
                return None
            
            email = email_result['email']
            activation_id = email_result['id']
            logger.info(f"Получен email: {email}")
            
            # Переход на fiverr.com
            logger.info("Переход на fiverr.com...")
            self.driver.get("https://fiverr.com/join")
            
            # Ждем загрузки страницы
            time.sleep(8)  # Ждем загрузку
            logger.info("Страница загружена, ожидание готовности...")
            
            # Делаем скриншот после загрузки
            await self._take_screenshot("01_loaded")
            
            # Проверяем есть ли капча
            if "human touch" in self.driver.page_source.lower() or "нужно человеческое прикосновение" in self.driver.page_source.lower():
                logger.info("КАПЧА ОБНАРУЖЕНА!")
                logger.info(">>> Пробуем обойти...")
                
                # Ищем кнопку капчи по ID и классу (не по тексту!)
                try:
                    # Пробуем разные варианты селекторов для кнопки капчи
                    button_selectors = [
                        # По ID (динамический)
                        "//p[@id]",
                        "//button[@id]",
                        "//div[@id]",
                        # По классу (динамический)
                        "//p[contains(@class, 'iUsURgYNFUgzUkD')]",
                        "//button[contains(@class, 'iUsURgYNFUgzUkD')]",
                        "//div[contains(@class, 'iUsURgYNFUgzUkD')]",
                        # По стилю анимации
                        "//p[contains(@style, 'animation')]",
                        "//button[contains(@style, 'animation')]",
                        "//div[contains(@style, 'animation')]",
                        # По тексту (последний вариант)
                        "//button[contains(text(), 'PRESS & HOLD')]",
                        "//button[contains(text(), 'НАЖМИТЕ И УДЕРЖИВАЙТЕ')]",
                        "//button[contains(text(), 'HOLD')]",
                        "//button[contains(text(), 'УДЕРЖИВАЙТЕ')]",
                        "//p[contains(text(), 'PRESS & HOLD')]",
                        "//p[contains(text(), 'НАЖМИТЕ И УДЕРЖИВАЙТЕ')]",
                        "//p[contains(text(), 'HOLD')]",
                        "//p[contains(text(), 'УДЕРЖИВАЙТЕ')]"
                    ]
                    
                    press_hold_button = None
                    for selector in button_selectors:
                        try:
                            # Ищем все элементы по селектору
                            elements = self.driver.find_elements(By.XPATH, selector)
                            for element in elements:
                                # Проверяем что элемент кликабельный и содержит текст капчи
                                if element.is_displayed() and element.is_enabled():
                                    text = element.text.lower()
                                    if any(word in text for word in ['press', 'hold', 'нажмите', 'удерживайте', 'touch', 'прикосновение']):
                                        press_hold_button = element
                                        logger.info(f">>> Найдена кнопка капчи: {selector} - текст: '{element.text}'")
                                        break
                            if press_hold_button:
                                break
                        except Exception as e:
                            logger.debug(f"Ошибка с селектором {selector}: {e}")
                            continue
                    
                    if press_hold_button:
                        logger.info(">>> Найдена кнопка капчи")
                        logger.info(f">>> HTML кнопки: {press_hold_button.get_attribute('outerHTML')}")
                        
                        # Пробуем разные способы взаимодействия
                        try:
                            # Способ 1: Обычный клик
                            logger.info(">>> Способ 1: Обычный клик...")
                            press_hold_button.click()
                            time.sleep(2)
                            
                            # Проверяем результат
                            if "human touch" not in self.driver.page_source.lower() and "нужно человеческое прикосновение" not in self.driver.page_source.lower():
                                logger.info("КАПЧА ПРОЙДЕНА через обычный клик!")
                            else:
                                # Способ 2: JavaScript клик
                                logger.info(">>> Способ 2: JavaScript клик...")
                                self.driver.execute_script("arguments[0].click();", press_hold_button)
                                time.sleep(2)
                                
                                # Проверяем результат
                                if "human touch" not in self.driver.page_source.lower() and "нужно человеческое прикосновение" not in self.driver.page_source.lower():
                                    logger.info("КАПЧА ПРОЙДЕНА через JavaScript клик!")
                                else:
                                    # Способ 3: ActionChains с удержанием
                                    logger.info(">>> Способ 3: ActionChains с удержанием...")
                                    actions = ActionChains(self.driver)
                                    actions.move_to_element(press_hold_button)
                                    actions.click_and_hold(press_hold_button)
                                    actions.perform()
                                    
                                    logger.info(">>> Удерживаем кнопку 3 секунды...")
                                    time.sleep(3)
                                    
                                    actions.release().perform()
                                    logger.info(">>> Отпустили кнопку")
                                    
                                    # Проверяем результат
                                    if "human touch" not in self.driver.page_source.lower() and "нужно человеческое прикосновение" not in self.driver.page_source.lower():
                                        logger.info("КАПЧА ПРОЙДЕНА через удержание!")
                                    
                        except Exception as e:
                            logger.error(f"Ошибка с капчей: {e}")
                    else:
                        logger.warning("Кнопка капчи не найдена")
                        
                except Exception as e:
                    logger.error(f"Ошибка с капчей: {e}")
            else:
                logger.info("Капчи нет, продолжаем...")
            
            # Делаем скриншот после капчи
            await self._take_screenshot("02_after_captcha")
            
            # Клик на кнопку Sign in
            logger.info("Клик на кнопку Sign in...")
            signin_clicked = await self._js_click('a.nav-link[href*="/login"]', "Sign in")
            if not signin_clicked:
                logger.error("❌ Не удалось кликнуть на Sign in")
                return None
            
            logger.info("✅ Кликнули на Sign in")
            
            # Ожидание появления модального окна с опциями
            logger.info("Ожидание появления модального окна с опциями...")
            time.sleep(3)
            
            # Делаем скриншот модального окна
            await self._take_screenshot("03_modal_opened")
            
            # Поиск кнопки 'Continue with email/username'
            logger.info("Поиск кнопки 'Continue with email/username'...")
            
            # Используем JavaScript для поиска и клика по кнопке
            email_button_clicked = self.driver.execute_script("""
                // Ищем все элементы с текстом кнопки
                const textElements = document.querySelectorAll('p[data-track-tag="text"]._ifhvih');
                
                for (let textEl of textElements) {
                    const text = textEl.textContent.toLowerCase();
                    if (text.includes('email') || text.includes('username')) {
                        // Ищем кликабельный родительский элемент
                        let parent = textEl.parentElement;
                        while (parent && parent !== document.body) {
                            if (parent.tagName === 'BUTTON' || 
                                parent.getAttribute('role') === 'button' || 
                                parent.style.cursor === 'pointer' ||
                                parent.classList.contains('_188cbt6')) {
                                parent.click();
                                return true;
                            }
                            parent = parent.parentElement;
                        }
                    }
                }
                return false;
            """)
            
            if not email_button_clicked:
                logger.error("❌ Не удалось кликнуть на кнопку email/username")
                return None
            
            logger.info("✅ Кликнули на кнопку email/username")
            
            # Ожидание загрузки формы email/password
            logger.info("Ожидание загрузки формы email/password...")
            time.sleep(5)
            
            # Делаем скриншот формы
            await self._take_screenshot("04_email_form")
            
            # Заполнение email и пароля
            logger.info("Заполнение email и пароля...")
            
            # Ждем появления полей ввода
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input#identification-usernameOrEmail'))
            )
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input#identification-password'))
            )
            
            # Заполняем поля
            self.driver.find_element(By.CSS_SELECTOR, 'input#identification-usernameOrEmail').send_keys(email)
            self.driver.find_element(By.CSS_SELECTOR, 'input#identification-password').send_keys(password)
            
            # Делаем скриншот после заполнения
            await self._take_screenshot("05_filled_form")
            
            # Отправка формы
            logger.info("Отправка формы...")
            
            # Ищем кнопку отправки
            submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"][data-track-tag="button"]')
            if submit_button:
                # Кликаем через JavaScript
                self.driver.execute_script("arguments[0].click();", submit_button)
                logger.info("✅ Форма отправлена через кнопку")
            else:
                # Пробуем отправить через Enter
                self.driver.find_element(By.CSS_SELECTOR, 'input#identification-password').send_keys('\n')
                logger.info("✅ Форма отправлена через Enter")
            
            # Ждем загрузки после отправки
            time.sleep(5)
            
            # Делаем скриншот после отправки
            await self._take_screenshot("06_form_submitted")
            
            # Ждем появления поля username
            logger.info("Ожидание появления поля username...")
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input#username'))
                )
                logger.info("✅ Поле username появилось")
            except:
                logger.error("❌ Поле username не появилось")
                # Делаем скриншот для отладки
                await self._take_screenshot("07_username_field_missing")
                return None
            
            # Делаем скриншот поля username
            await self._take_screenshot("07_username_field")
            
            # Заполнение username с проверкой доступности
            logger.info("Заполнение username...")
            max_username_attempts = 5
            
            for attempt in range(max_username_attempts):
                current_username = username if attempt == 0 else self._generate_username()
                logger.info(f"Попытка {attempt + 1}/{max_username_attempts}: {current_username}")
                
                # Очищаем поле и вводим username
                username_field = self.driver.find_element(By.CSS_SELECTOR, 'input#username')
                username_field.clear()
                username_field.send_keys(current_username)
                
                # Ждем немного для проверки
                time.sleep(2)
                
                # Проверяем есть ли ошибка валидации
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, '.error, .invalid, [class*="error"]')
                has_error = False
                
                for error_el in error_elements:
                    error_text = error_el.text
                    if error_text and any(word in error_text.lower() for word in ['already', 'taken', 'used', 'уже', 'используется', 'занято']):
                        logger.warning(f"❌ Username {current_username} уже занят: {error_text}")
                        has_error = True
                        break
                
                if not has_error:
                    logger.info(f"✅ Username {current_username} свободен")
                    break
                elif attempt == max_username_attempts - 1:
                    logger.error("❌ Не удалось найти свободный username")
                    return None
            
            # Делаем скриншот после заполнения username
            await self._take_screenshot("08_username_filled")
            
            # Отправка формы username
            logger.info("Отправка формы username...")
            
            # Ищем кнопку отправки для username
            username_submit = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            if username_submit:
                self.driver.execute_script("arguments[0].click();", username_submit)
                logger.info("✅ Форма username отправлена")
            else:
                self.driver.find_element(By.CSS_SELECTOR, 'input#username').send_keys('\n')
                logger.info("✅ Форма username отправлена через Enter")
            
            # Ждем загрузки
            time.sleep(5)
            
            # Делаем скриншот после отправки username
            await self._take_screenshot("09_username_submitted")
            
            # Ждем появления полей для ввода кода подтверждения
            logger.info("Ожидание полей для кода подтверждения...")
            try:
                # Ждем появления полей для кода (может быть 6 отдельных полей или одно)
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"][maxlength="6"], input[type="text"][maxlength="1"]'))
                )
                logger.info("✅ Поля для кода появились")
            except:
                logger.error("❌ Поля для кода не появились")
                await self._take_screenshot("10_code_fields_missing")
                return None
            
            # Делаем скриншот полей кода
            await self._take_screenshot("10_code_fields")
            
            # Получение кода подтверждения из email
            logger.info("Получение кода подтверждения из email...")
            message_result = await self.email_service.get_message(activation_id)
            
            if not message_result:
                logger.error("❌ Не удалось получить код подтверждения")
                await self.email_service.cancel_email(activation_id)
                return None
            
            code = message_result['value']
            logger.info(f"✅ Получен код: {code}")
            
            # Ввод кода подтверждения
            logger.info("Ввод кода подтверждения...")
            
            # Ищем поля для ввода кода
            code_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"][maxlength="6"], input[type="text"][maxlength="1"]')
            
            if len(code_inputs) == 6:
                # 6 отдельных полей - вводим по одной цифре
                for i, digit in enumerate(code[:6]):
                    if i < len(code_inputs):
                        code_inputs[i].send_keys(digit)
                        time.sleep(0.2)  # Небольшая задержка между вводами
            else:
                # Одно поле - вводим весь код
                code_inputs[0].send_keys(code)
            
            # Делаем скриншот после ввода кода
            await self._take_screenshot("11_code_entered")
            
            # Отправка кода
            logger.info("Отправка кода...")
            
            # Ищем кнопку отправки кода
            code_submit = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], button[data-track-tag="button"]')
            if code_submit:
                self.driver.execute_script("arguments[0].click();", code_submit)
                logger.info("✅ Код отправлен")
            else:
                self.driver.find_element(By.CSS_SELECTOR, 'input[type="text"][maxlength="6"]').send_keys('\n')
                logger.info("✅ Код отправлен через Enter")
            
            # Ждем загрузки
            time.sleep(5)
            
            # Делаем скриншот после отправки кода
            await self._take_screenshot("12_code_submitted")
            
            # Ждем появления вопросов онбординга
            logger.info("Ожидание вопросов онбординга...")
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="checkbox"], button[data-track-tag="button"]'))
                )
                logger.info("✅ Вопросы онбординга появились")
            except:
                logger.warning("⚠️ Вопросы онбординга не появились, продолжаем...")
            
            # Делаем скриншот вопросов
            await self._take_screenshot("13_onboarding_questions")
            
            # Выбор первого чекбокса
            logger.info("Выбор первого чекбокса...")
            try:
                first_checkbox = self.driver.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
                if first_checkbox:
                    self.driver.execute_script("arguments[0].click();", first_checkbox)
                    logger.info("✅ Первый чекбокс выбран")
            except:
                logger.warning("⚠️ Не удалось выбрать чекбокс")
            
            # Делаем скриншот после выбора чекбокса
            await self._take_screenshot("14_checkbox_selected")
            
            # Отправка формы онбординга
            logger.info("Отправка формы онбординга...")
            try:
                onboarding_submit = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], button[data-track-tag="button"]')
                if onboarding_submit:
                    self.driver.execute_script("arguments[0].click();", onboarding_submit)
                    logger.info("✅ Форма онбординга отправлена")
            except:
                logger.warning("⚠️ Не удалось отправить форму онбординга")
            
            # Ждем финальной загрузки
            time.sleep(5)
            
            # Делаем финальный скриншот
            await self._take_screenshot("15_registration_complete")
            
            # Получение cookies
            logger.info("Получение cookies...")
            cookies = self.driver.get_cookies()
            
            # Сохранение cookies в файл
            cookie_file = f"cookies/cookies_{username}_{int(time.time())}.json"
            os.makedirs("cookies", exist_ok=True)
            
            with open(cookie_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            logger.info(f"✅ Cookies сохранены: {cookie_file}")
            
            # Отмена email активации
            await self.email_service.cancel_email(activation_id)
            
            result = {
                "email": email,
                "username": current_username,
                "password": password,
                "cookies_file": cookie_file,
                "status": "success"
            }
            
            logger.info(f"✅ Аккаунт {current_username} успешно зарегистрирован!")
            return result
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при регистрации: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
        finally:
            await self._close_browser()
    
    async def register_multiple_accounts(self, count: int) -> List[Dict[str, Any]]:
        """Регистрация нескольких аккаунтов"""
        results = []
        
        for i in range(count):
            logger.info(f"Регистрация аккаунта {i + 1}/{count}")
            
            # Генерируем данные
            password = self._generate_password()
            username = self._generate_username()
            
            # Регистрируем аккаунт
            result = await self.register_account("", password, username)
            
            if result:
                results.append(result)
                logger.info(f"✅ Аккаунт {i + 1} зарегистрирован успешно")
            else:
                logger.error(f"❌ Не удалось зарегистрировать аккаунт {i + 1}")
        
        return results


async def register_accounts_batch(
    email_service: EmailAPIService,
    count: int,
    proxy: Optional[ProxyConfig] = None
) -> List[Dict[str, Any]]:
    """Регистрация нескольких аккаунтов в пакетном режиме"""
    registrator = FiverrRegistrator(email_service, proxy)
    return await registrator.register_multiple_accounts(count)
