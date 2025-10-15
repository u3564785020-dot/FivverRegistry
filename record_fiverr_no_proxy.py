"""
Скрипт БЕЗ прокси - чтобы увидеть селекторы
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("🚀 Запуск браузера БЕЗ прокси...")
        
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        
        page = await context.new_page()
        
        print("📄 Переход на https://fiverr.com/join...")
        await page.goto("https://fiverr.com/join", wait_until="load", timeout=60000)
        
        print("\n" + "="*80)
        print("✅ БРАУЗЕР ОТКРЫТ! (БЕЗ ПРОКСИ)")
        print("📋 Пройди регистрацию, я запишу все селекторы")
        print("="*80 + "\n")
        
        # Держим браузер открытым
        await page.wait_for_timeout(600000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())


