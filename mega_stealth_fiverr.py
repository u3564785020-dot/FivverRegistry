"""
МЕГА-STEALTH браузер для обхода Fiverr антибота
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print(">>> Запуск МЕГА-STEALTH браузера...")
        
        # Запуск с МАКСИМАЛЬНЫМ stealth
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
                "--ignore-certificate-errors-spki-list",
                "--ignore-certificate-errors-spki-list",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ]
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York"
        )
        
        page = await context.new_page()
        
        # ДОПОЛНИТЕЛЬНЫЙ STEALTH
        await page.add_init_script("""
            // Убираем ВСЕ следы автоматизации
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})});
            
            // Удаляем chrome.runtime
            if (window.chrome) {
                delete window.chrome.runtime;
                delete window.chrome.loadTimes;
                delete window.chrome.csi;
            }
            
            // Фейковые WebGL данные
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel(R) UHD Graphics 620';
                return getParameter.apply(this, arguments);
            };
            
            // Фейковые screen данные
            Object.defineProperty(screen, 'availHeight', {get: () => 1040});
            Object.defineProperty(screen, 'availWidth', {get: () => 1920});
            Object.defineProperty(screen, 'colorDepth', {get: () => 24});
            Object.defineProperty(screen, 'pixelDepth', {get: () => 24});
        """)
        
        print(">>> Переход на https://fiverr.com/join...")
        await page.goto("https://fiverr.com/join", wait_until="load", timeout=60000)
        
        print("\n" + "="*80)
        print(">>> МЕГА-STEALTH БРАУЗЕР ОТКРЫТ!")
        print(">>> ПРОВЕРЯЕМ ОБОШЛИ ЛИ АНТИБОТ!")
        print("="*80 + "\n")
        
        # Ждем 30 секунд для проверки
        await page.wait_for_timeout(30000)
        
        await browser.close()
        print("\n>>> Тест завершен")

if __name__ == "__main__":
    asyncio.run(main())
