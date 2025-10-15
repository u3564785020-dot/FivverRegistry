"""
Playwright с РАБОЧИМИ прокси для обхода Fiverr
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print(">>> Запуск Playwright с РАБОЧИМИ прокси...")
        
        # ПРАВИЛЬНЫЙ формат прокси для Playwright
        proxy_config = {
            "server": "http://91.92.66.141:11762",
            "username": "W5H6ceq6XcdpZLEH",
            "password": "W5H6ceq6XcdpZLEH"
        }
        
        # Запуск браузера с прокси
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000,  # Медленно как человек
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-ipc-flooding-protection",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
                "--disable-client-side-phishing-detection",
                "--disable-sync",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-translate",
                "--hide-scrollbars",
                "--mute-audio",
                "--no-first-run",
                "--safebrowsing-disable-auto-update",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--ignore-certificate-errors-spki-list"
            ],
            proxy=proxy_config  # ПРАВИЛЬНЫЙ способ передачи прокси
        )
        
        # Создаем контекст с stealth
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation", "notifications"]
        )
        
        # МАКСИМАЛЬНЫЙ stealth скрипт
        await context.add_init_script("""
            // Скрываем webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Скрываем chrome.runtime
            if (window.chrome) {
                delete window.chrome.runtime;
            }
            
            // Переопределяем navigator.plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
                    {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
                    {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}
                ]
            });
            
            // Переопределяем navigator.languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // WebGL vendor (как у реального Chrome)
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel(R) UHD Graphics';
                }
                return getParameter.apply(this, arguments);
            };
            
            // Permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        page = await context.new_page()
        page.set_default_timeout(60000)
        
        print(">>> Переход на Fiverr...")
        await page.goto("https://fiverr.com/join", wait_until="domcontentloaded")
        
        print(">>> Проверяем что загрузилось...")
        print(f"URL: {page.url}")
        print(f"Title: {await page.title()}")
        
        # Проверяем есть ли капча
        content = await page.content()
        if "human touch" in content.lower():
            print("КАПЧА ОБНАРУЖЕНА!")
            print(">>> Пробуем обойти...")
            
            # Ищем кнопку PRESS & HOLD
            try:
                press_hold_button = await page.wait_for_selector("button:has-text('PRESS & HOLD')", timeout=10000)
                print(">>> Найдена кнопка PRESS & HOLD")
                
                # Человеческое нажатие и удержание
                await press_hold_button.hover()
                await page.wait_for_timeout(500)
                await press_hold_button.click()
                
                print(">>> Удерживаем кнопку 3 секунды...")
                await page.wait_for_timeout(3000)
                
                print(">>> Отпустили кнопку")
                await page.wait_for_timeout(2000)
                
                # Проверяем результат
                new_content = await page.content()
                if "human touch" not in new_content.lower():
                    print("КАПЧА ПРОЙДЕНА!")
                else:
                    print("Капча не пройдена")
                    
            except Exception as e:
                print(f"Ошибка с капчей: {e}")
        else:
            print("Капчи нет, продолжаем...")
        
        print("\n" + "="*80)
        print(">>> БРАУЗЕР РАБОТАЕТ!")
        print(">>> ПРОЙДИ РЕГИСТРАЦИЮ ВРУЧНУЮ!")
        print(">>> Браузер будет открыт 10 минут...")
        print("="*80 + "\n")
        
        # Держим браузер открытым 10 минут
        await page.wait_for_timeout(600000)  # 10 минут
        
        await browser.close()
        print(">>> Браузер закрыт")

if __name__ == "__main__":
    asyncio.run(main())
