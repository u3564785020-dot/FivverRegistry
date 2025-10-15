"""
Fiverr Account Registration - PLAYWRIGHT С ПРОФЕССИОНАЛЬНЫМ СТЕЛСОМ
Регистрация аккаунтов на Fiverr через Playwright с максимальной защитой от детектирования
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

from playwright.async_api import async_playwright
from utils.logger import logger

# ПРОФЕССИОНАЛЬНЫЕ СТЕЛС НАСТРОЙКИ
ITALIAN_USER_AGENTS = [
    # Chrome на Windows (самый популярный)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    
    # Firefox на Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    
    # Edge на Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    
    # Chrome на Mac (популярный в Италии)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    
    # Safari на Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    
    # Chrome на Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

SCREEN_RESOLUTIONS = [
    {"width": 1920, "height": 1080},  # Full HD - самый популярный
    {"width": 1366, "height": 768},   # Ноутбуки
    {"width": 1536, "height": 864},   # Ноутбуки высокого разрешения
    {"width": 2560, "height": 1440},  # 2K мониторы
    {"width": 1440, "height": 900},   # MacBook
    {"width": 1280, "height": 720},   # HD
]

from services.proxy_manager import ProxyConfig
from services.email_api import EmailAPIService
from services.brightdata_api import BrightDataAPIService


class FiverrRegistrator:
    """Регистратор аккаунтов Fiverr через PLAYWRIGHT с ПРОФЕССИОНАЛЬНЫМ СТЕЛСОМ"""
    
    def __init__(self, proxy: Optional[ProxyConfig] = None, use_proxy: bool = True, use_brightdata: bool = True):
        self.proxy = proxy
        self.use_proxy = use_proxy
        self.use_brightdata = use_brightdata
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.brightdata_service = BrightDataAPIService() if use_brightdata else None

    async def _kill_chrome_processes(self):
        """Убиваем все процессы Chrome/Chromium"""
        try:
            subprocess.run(["pkill", "-9", "chrome"], check=False)
            subprocess.run(["pkill", "-9", "chromium"], check=False)
            subprocess.run(["pkill", "-9", "playwright"], check=False)
            subprocess.run(["rm", "-rf", "/tmp/.com.google.Chrome*"], check=False)
            subprocess.run(["rm", "-rf", "/tmp/chrome*"], check=False)
            logger.info("Все процессы Chrome принудительно завершены")
        except Exception as e:
            logger.warning(f"Ошибка при завершении процессов: {e}")

    async def _create_stealth_browser(self):
        """Создание браузера с МАКСИМАЛЬНЫМ СТЕЛСОМ"""
        try:
            logger.info("🚀 Создаем браузер с ПРОФЕССИОНАЛЬНЫМ СТЕЛСОМ...")
            
            # Убиваем процессы
            await self._kill_chrome_processes()
            await asyncio.sleep(2)
            
            # Случайные настройки
            user_agent = random.choice(ITALIAN_USER_AGENTS)
            viewport = random.choice(SCREEN_RESOLUTIONS)
            
            logger.info(f"🎭 User-Agent: {user_agent[:50]}...")
            logger.info(f"📱 Разрешение: {viewport['width']}x{viewport['height']}")
            
            # Запуск Playwright
            self.playwright = await async_playwright().start()
            
            # Настройки прокси
            proxy_config = None
            if self.use_proxy and self.proxy:
                proxy_config = {
                    "server": f"http://{self.proxy.host}:{self.proxy.port}",
                    "username": self.proxy.username,
                    "password": self.proxy.password
                }
                logger.info(f"🌐 Используем прокси: {self.proxy.host}:{self.proxy.port}")
            
            # Запуск браузера с МАКСИМАЛЬНЫМИ СТЕЛС НАСТРОЙКАМИ
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # HEADLESS для Railway
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--ignore-certifcate-errors",
                    "--ignore-certifcate-errors-spki-list",
                    "--disable-gpu",
                    # КРИТИЧЕСКИЕ ФИКСЫ для ограниченных ресурсов
                    "--max_old_space_size=512",
                    "--no-zygote",
                    "--single-process",
                    "--disable-software-rasterizer",
                    "--disable-accelerated-2d-canvas",
                    "--disable-accelerated-video-decode",
                    # Имитация реального браузера
                    "--disable-extensions",
                    "--disable-background-networking",
                    "--disable-default-apps",
                    "--disable-sync",
                    "--metrics-recording-only",
                    "--mute-audio",
                    "--no-first-run",
                    "--safebrowsing-disable-auto-update",
                    "--disable-client-side-phishing-detection",
                    "--disable-component-update",
                ]
            )
            
            # Создание контекста с ПРОФЕССИОНАЛЬНЫМИ настройками
            self.context = await self.browser.new_context(
                viewport=viewport,
                user_agent=user_agent,
                locale="it-IT",
                timezone_id="Europe/Rome",
                geolocation={"latitude": 41.9028, "longitude": 12.4964},  # Рим
                permissions=["geolocation"],
                color_scheme="light",
                has_touch=False,
                is_mobile=False,
                device_scale_factor=1,
                screen={
                    "width": viewport["width"],
                    "height": viewport["height"]
                },
                extra_http_headers={
                    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                },
                proxy=proxy_config
            )
            
            # Создание страницы
            self.page = await self.context.new_page()
            
            # Применяем МАКСИМАЛЬНУЮ защиту от детектирования
            await self._apply_stealth_protection()
            
            # Блокируем рекламу и трекеры
            await self._block_ads_and_trackers()
            
            logger.info("✅ Браузер с ПРОФЕССИОНАЛЬНЫМ СТЕЛСОМ создан!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания браузера: {e}")
            return False

    async def _apply_stealth_protection(self):
        """Применение МАКСИМАЛЬНОЙ защиты от детектирования"""
        try:
            await self.page.add_init_script("""
                // Скрываем webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Скрываем автоматизацию
                delete navigator.__proto__.webdriver;
                
                // Подменяем permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Подменяем plugins для реалистичности
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/pdf", suffixes: "pdf", description: ""},
                            description: "",
                            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        }
                    ]
                });
                
                // Подменяем languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['it-IT', 'it', 'en-US', 'en']
                });
                
                // Добавляем реалистичный chrome object
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Скрываем automation
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8
                });
                
                // Добавляем реалистичные параметры устройства
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8
                });
                
                // Подменяем canvas fingerprint (базовая защита)
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(type) {
                    if (type === 'image/png' && this.width === 0 && this.height === 0) {
                        return 'data:image/png;base64,iVBORw0KGg';
                    }
                    return originalToDataURL.apply(this, arguments);
                };
                
                // Эмуляция battery API
                Object.defineProperty(navigator, 'getBattery', {
                    get: () => () => Promise.resolve({
                        charging: true,
                        chargingTime: 0,
                        dischargingTime: Infinity,
                        level: 1
                    })
                });
            """)
            logger.info("🛡️ Применена МАКСИМАЛЬНАЯ защита от детектирования")
        except Exception as e:
            logger.error(f"❌ Ошибка применения защиты: {e}")

    async def _block_ads_and_trackers(self):
        """Блокировка рекламы и трекеров для ускорения"""
        try:
            async def block_route(route):
                url = route.request.url
                
                # Список заблокированных доменов/паттернов
                blocked_patterns = [
                    # Реклама
                    'doubleclick.net', 'googlesyndication.com', 'adservice.google',
                    'googleadservices.com', 'advertising.com', 'ads.', '/ads/',
                    'adserver', 'adtech', 'advertising', 'adsystem',
                    # Аналитика
                    'google-analytics.com', 'googletagmanager.com', 'analytics.google',
                    'facebook.com/tr', 'facebook.net', 'connect.facebook',
                    'pixel.', 'tracking.', 'track.', 'metrics.',
                    # Социальные сети (виджеты)
                    'twitter.com/widgets', 'instagram.com/embed', 'platform.twitter',
                    # CDN с трекерами
                    'criteo.com', 'outbrain.com', 'taboola.com', 'addthis.com',
                    # Видео-реклама
                    'youtube.com/ads', 'vimeo.com/stats',
                ]
                
                # Проверяем, нужно ли блокировать
                if any(blocked in url for blocked in blocked_patterns):
                    await route.abort()
                else:
                    await route.continue_()
            
            # Применяем блокировку
            await self.page.route("**/*", block_route)
            logger.info("🚫 Блокировка рекламы и трекеров активирована")
        except Exception as e:
            logger.error(f"❌ Ошибка блокировки: {e}")

    async def _take_step_screenshot(self, step_name: str, telegram_bot=None, chat_id: int = None, email: str = ""):
        """Скриншот этапа регистрации"""
        try:
            if not telegram_bot or not chat_id:
                return
            
            # Делаем скриншот
            screenshot = await self.page.screenshot(full_page=True)
            
            # Отправляем в Telegram
            caption = f"📸 {step_name}\n📧 Email: {email}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            await telegram_bot.send_photo(
                chat_id=chat_id,
                photo=BytesIO(screenshot),
                caption=caption
            )
            
            logger.info(f"Скриншот этапа '{step_name}' отправлен в Telegram")
            
        except Exception as e:
            logger.error(f"Ошибка отправки скриншота: {e}")

    async def _bypass_press_hold_captcha(self) -> bool:
        """ПРОДВИНУТЫЙ обход капчи PRESS & HOLD с человеческим поведением"""
        try:
            logger.info("🎯 Обходим капчу PRESS & HOLD...")
            
            # Ищем кнопку с МНОЖЕСТВЕННЫМИ селекторами
            button_selectors = [
                "button[class*='press']",
                "button[class*='hold']", 
                "div[class*='press']",
                "div[class*='hold']",
                "//button[contains(text(), 'PRESS')]",
                "//button[contains(text(), 'HOLD')]",
                "//div[contains(text(), 'PRESS')]",
                "//div[contains(text(), 'HOLD')]",
                "//*[contains(@class, 'press')]",
                "//*[contains(@class, 'hold')]",
                "//*[contains(text(), 'PRESS') and contains(text(), 'HOLD')]"
            ]
            
            button = None
            for selector in button_selectors:
                try:
                    if selector.startswith("//"):
                        button = await self.page.query_selector(f"xpath={selector}")
                    else:
                        button = await self.page.query_selector(selector)
                    
                    if button:
                        logger.info(f"✅ Кнопка найдена с селектором: {selector}")
                        break
                except:
                    continue
            
            if not button:
                logger.error("❌ Кнопка PRESS & HOLD не найдена")
                return False
            
            # ЧЕЛОВЕЧЕСКОЕ ПОВЕДЕНИЕ - ЗАЖИМАЕМ И ДЕРЖИМ!
            logger.info("🤖 Зажимаем кнопку как человек...")
            
            # 1. Наводим курсор на кнопку
            await button.hover()
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # 2. Пауза перед зажатием (как человек думает)
            await asyncio.sleep(random.uniform(0.2, 0.5))
            
            # 3. ЗАЖИМАЕМ И ДЕРЖИМ 7-9 СЕКУНД БЕЗ ДВИЖЕНИЙ!
            hold_time = random.uniform(7.0, 9.0)  # 7-9 секунд
            logger.info(f"⏱️ ЗАЖИМАЕМ кнопку {hold_time:.1f} секунд БЕЗ ДВИЖЕНИЙ...")
            
            # 4. ЗАЖИМАЕМ кнопку
            await button.click(button=button, modifiers=[], force=False, no_wait_after=False, timeout=30000, trial=False)
            
            # 5. ДЕРЖИМ БЕЗ ДВИЖЕНИЙ (как просил пользователь!)
            await asyncio.sleep(hold_time)
            
            logger.info("✅ Кнопка отпущена")
            
            # 6. Ждем обработки (как человек)
            await asyncio.sleep(random.uniform(2, 4))
            
            # 7. Проверяем результат
            page_content = await self.page.content()
            if "PRESS" not in page_content or "HOLD" not in page_content:
                logger.info("🎉 Капча PRESS & HOLD успешно обойдена!")
                return True
            else:
                logger.warning("⚠️ Капча все еще присутствует, пробуем еще раз...")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка в обходе PRESS & HOLD: {e}")
            return False

    async def _bypass_perimeterx_captcha(self) -> bool:
        """ПРОДВИНУТЫЙ обход PerimeterX капчи - ЗАЖАТЬ И ДЕРЖАТЬ!"""
        try:
            logger.info("🛡️ Обходим PerimeterX капчу - ЗАЖИМАЕМ И ДЕРЖИМ...")
            
            # Ждем загрузки PerimeterX
            await asyncio.sleep(3)
            
            # Ищем кнопку для зажатия - МАКСИМАЛЬНОЕ КОЛИЧЕСТВО СЕЛЕКТОРОВ!
            button_selectors = [
                # PerimeterX специфичные селекторы
                "button[class*='px-captcha']",
                "div[class*='px-captcha'] button",
                "button[id*='px-captcha']",
                "div[id*='px-captcha'] button",
                "button[class*='captcha']",
                "div[class*='captcha'] button",
                "button[id*='captcha']",
                "div[id*='captcha'] button",
                
                # PRESS & HOLD селекторы
                "button[class*='press']",
                "button[class*='hold']",
                "div[class*='press']",
                "div[class*='hold']",
                "button:has-text('PRESS')",
                "button:has-text('HOLD')",
                "div:has-text('PRESS')",
                "div:has-text('HOLD')",
                
                # Общие кнопки
                "button[type='button']",
                "button[type='submit']",
                "input[type='button']",
                "input[type='submit']",
                "button",
                "div[role='button']",
                "span[role='button']",
                
                # XPath селекторы
                "//button[contains(@class, 'px-captcha')]",
                "//div[contains(@class, 'px-captcha')]//button",
                "//button[contains(@id, 'px-captcha')]",
                "//div[contains(@id, 'px-captcha')]//button",
                "//button[contains(@class, 'captcha')]",
                "//div[contains(@class, 'captcha')]//button",
                "//button[contains(text(), 'PRESS')]",
                "//button[contains(text(), 'HOLD')]",
                "//div[contains(text(), 'PRESS')]",
                "//div[contains(text(), 'HOLD')]",
                "//*[contains(@class, 'px-captcha')]//*[contains(text(), 'PRESS')]",
                "//*[contains(@class, 'px-captcha')]//*[contains(text(), 'HOLD')]",
                "//button[contains(@class, 'press')]",
                "//button[contains(@class, 'hold')]",
                "//div[contains(@class, 'press')]",
                "//div[contains(@class, 'hold')]",
                "//button[@type='button']",
                "//button[@type='submit']",
                "//input[@type='button']",
                "//input[@type='submit']",
                "//button",
                "//div[@role='button']",
                "//span[@role='button']",
                
                # Дополнительные селекторы для PerimeterX
                "//*[contains(@class, 'px-captcha')]//button",
                "//*[contains(@id, 'px-captcha')]//button",
                "//*[contains(@class, 'captcha')]//button",
                "//*[contains(@id, 'captcha')]//button",
                "//*[contains(text(), 'PRESS') and contains(text(), 'HOLD')]",
                "//*[contains(text(), 'press') and contains(text(), 'hold')]",
                "//*[contains(text(), 'Press') and contains(text(), 'Hold')]"
            ]
            
            button = None
            found_selector = None
            
            # Сначала получаем HTML для анализа
            page_content = await self.page.content()
            logger.info(f"🔍 Анализируем HTML страницы (длина: {len(page_content)})...")
            
            # Ищем все кнопки на странице
            all_buttons = await self.page.query_selector_all("button")
            all_divs = await self.page.query_selector_all("div")
            all_inputs = await self.page.query_selector_all("input")
            
            logger.info(f"📊 Найдено элементов: {len(all_buttons)} кнопок, {len(all_divs)} div, {len(all_inputs)} input")
            
            # Пробуем каждый селектор
            for i, selector in enumerate(button_selectors):
                try:
                    if selector.startswith("//"):
                        button = await self.page.query_selector(f"xpath={selector}")
                    else:
                        button = await self.page.query_selector(selector)
                    
                    if button:
                        # Проверяем, что кнопка видима
                        is_visible = await button.is_visible()
                        is_enabled = await button.is_enabled()
                        button_text = await button.text_content()
                        
                        logger.info(f"✅ Найдена кнопка PerimeterX: {selector}")
                        logger.info(f"   Видима: {is_visible}, Включена: {is_enabled}, Текст: '{button_text}'")
                        
                        if is_visible and is_enabled:
                            found_selector = selector
                            break
                        else:
                            logger.warning(f"   Кнопка найдена, но не видима или не включена")
                            button = None
                except Exception as e:
                    logger.debug(f"   Селектор {i+1}/{len(button_selectors)} не сработал: {selector}")
                    continue
            
            if not button:
                logger.error("❌ Кнопка PerimeterX не найдена")
                
                # Дополнительная отладка - ищем любые элементы с текстом PRESS или HOLD
                try:
                    press_elements = await self.page.query_selector_all("//*[contains(text(), 'PRESS')]")
                    hold_elements = await self.page.query_selector_all("//*[contains(text(), 'HOLD')]")
                    
                    logger.info(f"🔍 Найдено элементов с 'PRESS': {len(press_elements)}")
                    logger.info(f"🔍 Найдено элементов с 'HOLD': {len(hold_elements)}")
                    
                    for i, elem in enumerate(press_elements[:3]):  # Показываем первые 3
                        try:
                            tag_name = await elem.evaluate("el => el.tagName")
                            text_content = await elem.text_content()
                            logger.info(f"   PRESS элемент {i+1}: {tag_name} - '{text_content}'")
                        except:
                            pass
                    
                    for i, elem in enumerate(hold_elements[:3]):  # Показываем первые 3
                        try:
                            tag_name = await elem.evaluate("el => el.tagName")
                            text_content = await elem.text_content()
                            logger.info(f"   HOLD элемент {i+1}: {tag_name} - '{text_content}'")
                        except:
                            pass
                            
                except Exception as e:
                    logger.error(f"Ошибка при дополнительной отладке: {e}")
                
                return False
            
            # ЧЕЛОВЕЧЕСКОЕ ПОВЕДЕНИЕ - ЗАЖИМАЕМ И ДЕРЖИМ!
            logger.info("🤖 Зажимаем кнопку как человек...")
            
            # 1. Наводим курсор на кнопку
            await button.hover()
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # 2. Пауза перед зажатием (как человек думает)
            await asyncio.sleep(random.uniform(0.2, 0.5))
            
            # 3. ЗАЖИМАЕМ И ДЕРЖИМ 7-9 СЕКУНД БЕЗ ДВИЖЕНИЙ!
            hold_time = random.uniform(7.0, 9.0)  # 7-9 секунд
            logger.info(f"⏱️ ЗАЖИМАЕМ кнопку {hold_time:.1f} секунд БЕЗ ДВИЖЕНИЙ...")
            
            # 4. ЗАЖИМАЕМ кнопку
            await button.click(button=button, modifiers=[], force=False, no_wait_after=False, timeout=30000, trial=False)
            
            # 5. ДЕРЖИМ БЕЗ ДВИЖЕНИЙ (как просил пользователь!)
            await asyncio.sleep(hold_time)
            
            logger.info("✅ Кнопка отпущена")
            
            # 6. Ждем обработки
            await asyncio.sleep(random.uniform(2, 4))
            
            # 7. Проверяем результат
            page_content = await self.page.content()
            if "px-captcha" not in page_content.lower() and "PRESS" not in page_content:
                logger.info("🎉 PerimeterX капча обойдена!")
                return True
            else:
                logger.warning("⚠️ PerimeterX капча все еще активна, пробуем еще раз...")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка в обходе PerimeterX: {e}")
            return False

    async def _register_with_captcha_bypass(self, email: str, username: str, password: str, telegram_bot=None, chat_id: int = None) -> Dict[str, Any]:
        """Регистрация с обходом капчи через PLAYWRIGHT + BRIGHTDATA"""
        try:
            # Сначала пробуем обойти капчу через BrightData
            if self.use_brightdata and self.brightdata_service:
                logger.info("🚀 Пробуем обойти капчу через BrightData...")
                
                # Проверяем обход капчи
                captcha_bypassed = await self.brightdata_service.check_captcha_bypass("https://it.fiverr.com/")
                
                if captcha_bypassed:
                    logger.info("✅ Капча обойдена через BrightData! Используем разблокированную страницу...")
                    
                    # Получаем разблокированную страницу
                    unlocked_html = await self.brightdata_service.unlock_fiverr_page("https://it.fiverr.com/")
                    
                    if unlocked_html:
                        # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: убеждаемся что капча действительно обойдена
                        if "px-captcha" not in unlocked_html.lower() and "PRESS" not in unlocked_html.upper():
                            logger.info("✅ Подтверждено: капча полностью обойдена через BrightData!")
                            
                            # Создаем браузер и загружаем разблокированную страницу
                            if not await self._create_stealth_browser():
                                return {
                                    "success": False,
                                    "error": "Не удалось создать браузер с стелс настройками"
                                }
                            
                            # Загружаем разблокированную HTML страницу
                            await self.page.set_content(unlocked_html)
                            logger.info("✅ Разблокированная страница загружена в браузер")
                            
                            # Скриншот разблокированной страницы
                            await self._take_step_screenshot("Страница разблокирована через BrightData", telegram_bot, chat_id, email)
                            
                            # Пропускаем обход капчи и переходим к регистрации
                            return await self._fill_registration_form(email, username, password, telegram_bot, chat_id)
                        else:
                            logger.warning("⚠️ BrightData разблокировал страницу, но капча все еще присутствует. Пробуем обычный способ...")
                    else:
                        logger.warning("⚠️ Не удалось получить разблокированную страницу, пробуем обычный способ...")
                else:
                    logger.warning("⚠️ BrightData не смог обойти капчу, пробуем обычный способ...")
            
            # Обычный способ через браузер
            logger.info("🌐 Используем обычный способ обхода капчи через браузер...")
            
            # Создаем браузер с ПРОФЕССИОНАЛЬНЫМ СТЕЛСОМ
            if not await self._create_stealth_browser():
                return {
                    "success": False,
                    "error": "Не удалось создать браузер с стелс настройками"
                }
            
            # Переходим на главную страницу (где происходит регистрация)
            logger.info("Переходим на главную страницу Fiverr...")
            await self.page.goto("https://it.fiverr.com/", wait_until="networkidle", timeout=60000)
            
            # Ждем загрузки
            await asyncio.sleep(3)
            
            # Скриншот главной страницы
            await self._take_step_screenshot("Главная страница Fiverr", telegram_bot, chat_id, email)
            
            # УМНАЯ ПРОВЕРКА КАПЧИ
            page_content = await self.page.content()
            
            # Проверяем разные типы капчи
            captcha_detected = False
            captcha_type = None
            
            if "PRESS" in page_content and "HOLD" in page_content:
                captcha_detected = True
                captcha_type = "PRESS_HOLD"
                logger.info("🎯 Обнаружена капча PRESS & HOLD - используем ПРОДВИНУТЫЙ обход...")
            elif "px-captcha" in page_content.lower():
                captcha_detected = True
                captcha_type = "PERIMETERX"
                logger.info("🛡️ Обнаружена PerimeterX капча - используем СТЕЛС обход...")
            elif "captcha" in page_content.lower():
                captcha_detected = True
                captcha_type = "GENERIC"
                logger.info("🤖 Обнаружена общая капча - используем УНИВЕРСАЛЬНЫЙ обход...")
            
            if captcha_detected:
                await self._take_step_screenshot(f"Обнаружена капча: {captcha_type}", telegram_bot, chat_id, email)
                
                # ПРОДВИНУТЫЙ ОБХОД КАПЧИ
                if captcha_type == "PRESS_HOLD":
                    captcha_bypassed = await self._bypass_press_hold_captcha()
                elif captcha_type == "PERIMETERX":
                    captcha_bypassed = await self._bypass_perimeterx_captcha()
                else:
                    captcha_bypassed = await self._bypass_press_hold_captcha()  # Fallback
                
                if not captcha_bypassed:
                    logger.error(f"❌ Не удалось обойти капчу {captcha_type}")
                    return {
                        "success": False,
                        "error": f"Не удалось обойти капчу {captcha_type}"
                    }
                
                logger.info(f"✅ Капча {captcha_type} успешно обойдена!")
                await self._take_step_screenshot(f"Капча {captcha_type} обойдена", telegram_bot, chat_id, email)
                
                # Ждем после обхода капчи
                await asyncio.sleep(2)
            
            # Заполняем форму регистрации
            return await self._fill_registration_form(email, username, password, telegram_bot, chat_id)
            
        except Exception as e:
            logger.error(f"Критическая ошибка при регистрации: {e}")
            return {
                "success": False,
                "error": f"Критическая ошибка: {str(e)}"
            }
        finally:
            # Закрываем браузер
            if self.browser:
                try:
                    await self.browser.close()
                except:
                    pass
            if self.playwright:
                try:
                    await self.playwright.stop()
                except:
                    pass
            if self.brightdata_service:
                try:
                    await self.brightdata_service.close()
                except:
                    pass

    async def _fill_registration_form(self, email: str, username: str, password: str, telegram_bot=None, chat_id: int = None) -> Dict[str, Any]:
        """Заполнение формы регистрации"""
        try:
            logger.info("📝 Заполняем форму регистрации...")
            
            # Теперь заполняем форму регистрации
            try:
                # Ищем поля формы регистрации
                email_selectors = [
                    "input[name='user[email]']",
                    "input[type='email']",
                    "#user_email",
                    "input[placeholder*='email' i]",
                    "input[placeholder*='Email' i]"
                ]
                
                password_selectors = [
                    "input[name='user[password]']",
                    "input[type='password']",
                    "#user_password",
                    "input[placeholder*='password' i]",
                    "input[placeholder*='Password' i]"
                ]
                
                username_selectors = [
                    "input[name='user[username]']",
                    "#user_username",
                    "input[placeholder*='username' i]",
                    "input[placeholder*='Username' i]"
                ]
                
                # Ищем поля
                email_field = None
                password_field = None
                username_field = None
                
                for selector in email_selectors:
                    try:
                        email_field = await self.page.query_selector(selector)
                        if email_field:
                            break
                    except:
                        continue
                
                for selector in password_selectors:
                    try:
                        password_field = await self.page.query_selector(selector)
                        if password_field:
                            break
                    except:
                        continue
                
                for selector in username_selectors:
                    try:
                        username_field = await self.page.query_selector(selector)
                        if username_field:
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
                await email_field.fill(email)
                logger.info("Поле email заполнено")
                
                # Скриншот после заполнения email
                await self._take_step_screenshot("Email заполнен", telegram_bot, chat_id, email)
                
                await password_field.fill(password)
                logger.info("Поле password заполнено")
                
                # Заполняем username если поле найдено
                if username_field:
                    await username_field.fill(username)
                    logger.info("Поле username заполнено")
                else:
                    logger.info("Поле username не найдено - возможно необязательное")
                
                logger.info("Поля формы заполнены")
                
                # Скриншот после заполнения всех полей
                await self._take_step_screenshot("Все поля заполнены", telegram_bot, chat_id, email)
                
                # Ищем кнопку регистрации
                submit_selectors = [
                    "button[type='submit']",
                    "input[type='submit']",
                    ".fiverr-button",
                    ".register-button",
                    "button:has-text('Sign Up')",
                    "button:has-text('Register')",
                    "button:has-text('Create Account')"
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    try:
                        submit_button = await self.page.query_selector(selector)
                        if submit_button:
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
                await submit_button.click()
                logger.info("Кнопка регистрации нажата")
                
                # Скриншот после нажатия кнопки регистрации
                await self._take_step_screenshot("Кнопка регистрации нажата", telegram_bot, chat_id, email)
                
                # Ждем результата
                await asyncio.sleep(5)
                
                # Проверяем успешность регистрации
                current_url = self.page.url
                page_content = await self.page.content()
                
                if "success" in page_content.lower() or "welcome" in page_content.lower() or "dashboard" in current_url:
                    logger.info("Регистрация успешна!")
                    
                    # Скриншот успешной регистрации
                    await self._take_step_screenshot("Регистрация успешна!", telegram_bot, chat_id, email)
                    
                    # Получаем cookies
                    cookies = await self.context.cookies()
                    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                    
                    return {
                        "success": True,
                        "email": email,
                        "username": username,
                        "password": password,
                        "cookies": cookies_dict,
                        "confirmation_code": None  # Будет получен через Email API
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
                    "error": f"Ошибка при заполнении формы: {str(e)}"
                }
            
        except Exception as e:
            logger.error(f"Критическая ошибка при регистрации: {e}")
            return {
                "success": False,
                "error": f"Критическая ошибка: {str(e)}"
            }
        finally:
            # Закрываем браузер
            if self.browser:
                try:
                    await self.browser.close()
                except:
                    pass
            if self.playwright:
                try:
                    await self.playwright.stop()
                except:
                    pass

    def _generate_username(self) -> str:
        """Генерация случайного username в формате text_text"""
        prefix = ''.join(random.choices(string.ascii_lowercase, k=random.randint(6, 10)))
        suffix = ''.join(random.choices(string.ascii_lowercase, k=random.randint(6, 10)))
        return f"{prefix}_{suffix}"

    def _generate_password(self) -> str:
        """Генерация надежного пароля"""
        length = random.randint(8, 12)
        uppercase = random.choice(string.ascii_uppercase)
        lowercase = ''.join(random.choices(string.ascii_lowercase, k=length-3))
        digit = random.choice(string.digits)
        special = random.choice('!@#$%^&*')
        
        password = uppercase + lowercase + digit + special
        return ''.join(random.sample(password, len(password)))

    async def register_account(self, email: str, username: str = None, password: str = None, email_id: str = None, email_service: EmailAPIService = None, telegram_bot=None, chat_id: int = None) -> Dict[str, Any]:
        """Регистрация одного аккаунта через PLAYWRIGHT"""
        try:
            logger.info(f"Начинаем регистрацию аккаунта с email: {email}")
            
            # Генерируем данные если не переданы
            if not username:
                username = self._generate_username()
                logger.info(f"Сгенерирован username: {username}")
            
            if not password:
                password = self._generate_password()
                logger.info(f"Сгенерирован пароль: {password}")
            
            # Регистрация через браузер
            result = await self._register_with_captcha_bypass(email, username, password, telegram_bot, chat_id)
            
            # Если нужен код подтверждения, получаем его
            if result.get("success") and email_id and email_service:
                logger.info("Получаем код подтверждения...")
                confirmation_result = await email_service.get_message(email_id)
                if confirmation_result and confirmation_result.get("value"):
                    result["confirmation_code"] = confirmation_result.get("value")
                    logger.info(f"Код подтверждения получен: {result['confirmation_code']}")
                else:
                    logger.warning("Не удалось получить код подтверждения")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка регистрации аккаунта: {e}")
            return {
                "success": False,
                "error": f"Ошибка регистрации: {str(e)}"
            }

    async def register_accounts_batch(self, email_service: EmailAPIService, count: int, proxy: Optional[ProxyConfig] = None, selected_domain: str = 'gmx.com', telegram_bot=None, chat_id: int = None) -> List[Dict[str, Any]]:
        """Регистрация нескольких аккаунтов"""
        results = []
        
        for i in range(count):
            try:
                logger.info(f"Регистрация аккаунта {i+1}/{count}")
                
                # Заказываем email
                email_result = await email_service.order_email(selected_domain)
                if not email_result.get("email"):
                    logger.error(f"Не удалось заказать email для аккаунта {i+1}")
                    results.append({
                        "success": False,
                        "error": "Не удалось заказать email"
                    })
                    continue
                
                email = email_result["email"]
                email_id = email_result.get("id")
                logger.info(f"Получен email: {email}")
                
                # Регистрируем аккаунт
                result = await self.register_account(
                    email=email,
                    email_id=email_id,
                    email_service=email_service,
                    telegram_bot=telegram_bot,
                    chat_id=chat_id
                )
                
                results.append(result)
                
                if result.get("success"):
                    logger.info(f"✅ Аккаунт {i+1} успешно зарегистрирован!")
                else:
                    logger.error(f"❌ Ошибка регистрации аккаунта {i+1}: {result.get('error')}")
                
                # Пауза между регистрациями
                if i < count - 1:
                    await asyncio.sleep(random.uniform(3, 7))
                
            except Exception as e:
                logger.error(f"❌ Критическая ошибка при регистрации аккаунта {i+1}: {e}")
                results.append({
                    "success": False,
                    "error": f"Критическая ошибка: {str(e)}"
                })
        
        return results
