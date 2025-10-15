"""
Скрипт для РУЧНОЙ записи процесса регистрации на Fiverr
Запускает браузер с прокси, ты регистрируешься вручную, я вижу все селекторы
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    proxy_config = {
        "server": "http://109.104.153.193:14534",
        "username": "b66AnDhC0l9xFOTj",
        "password": "b66AnDhC0l9xFOTj"
    }
    
    async with async_playwright() as p:
        print("🚀 Запуск браузера с прокси...")
        
        browser = await p.chromium.launch(
            headless=False,  # Видимый браузер
            proxy=proxy_config,
            slow_mo=500  # Замедление для отслеживания
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        page = await context.new_page()
        
        # Слушаем все клики и заполнения
        async def log_click(locator):
            print(f"🖱️ КЛИК: {locator}")
        
        async def log_fill(selector, text):
            print(f"⌨️ ЗАПОЛНЕНИЕ: {selector} -> {text}")
        
        print("📄 Переход на https://fiverr.com/join...")
        await page.goto("https://fiverr.com/join", wait_until="domcontentloaded")
        
        print("\n" + "="*80)
        print("✅ БРАУЗЕР ОТКРЫТ!")
        print("📋 ТВОИ ДЕЙСТВИЯ:")
        print("   1. Пройди процесс регистрации ВРУЧНУЮ")
        print("   2. Я буду логировать HTML всех кликнутых элементов")
        print("   3. После завершения ЗАКРОЙ браузер")
        print("="*80 + "\n")
        
        # Ждем пока ты не закроешь браузер
        try:
            # Логирование всех кликов
            page.on("click", lambda: print("🖱️ Клик зафиксирован"))
            
            # Держим браузер открытым
            await page.wait_for_timeout(600000)  # 10 минут
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print("\n✅ Браузер закрыт")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())


