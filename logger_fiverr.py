"""
ЛОГИРОВАНИЕ ВСЕХ ДЕЙСТВИЙ при регистрации
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print(">>> Запуск браузера с логированием...")
        
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=300
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        
        page = await context.new_page()
        
        # ПЕРЕХВАТ ВСЕХ КЛИКОВ
        await page.expose_function("logClick", lambda target: 
            print(f"\n>>> КЛИК НА ЭЛЕМЕНТ:\n{target}\n")
        )
        
        # ПЕРЕХВАТ ВСЕХ ВВОДОВ
        await page.expose_function("logInput", lambda selector, value: 
            print(f"\n>>> ВВОД В ПОЛЕ:\n  Селектор: {selector}\n  Значение: {value}\n")
        )
        
        # Внедряем JavaScript для отслеживания
        await page.add_init_script("""
            document.addEventListener('click', (e) => {
                const el = e.target;
                const info = {
                    tag: el.tagName,
                    id: el.id || 'нет',
                    class: el.className || 'нет',
                    text: el.innerText ? el.innerText.substring(0, 100) : 'нет',
                    html: el.outerHTML.substring(0, 500),
                    selector: generateSelector(el)
                };
                window.logClick(JSON.stringify(info, null, 2));
            }, true);
            
            document.addEventListener('input', (e) => {
                const el = e.target;
                window.logInput(generateSelector(el), e.target.value);
            }, true);
            
            function generateSelector(el) {
                if (el.id) return '#' + el.id;
                if (el.name) return `[name="${el.name}"]`;
                let path = [];
                while (el.parentElement) {
                    let selector = el.tagName.toLowerCase();
                    if (el.className) {
                        selector += '.' + el.className.split(' ').join('.');
                    }
                    path.unshift(selector);
                    el = el.parentElement;
                    if (path.length > 3) break;
                }
                return path.join(' > ');
            }
        """)
        
        print(">>> Переход на https://fiverr.com/join...")
        await page.goto("https://fiverr.com/join", wait_until="load", timeout=60000)
        
        print("\n" + "="*80)
        print(">>> БРАУЗЕР ОТКРЫТ!")
        print(">>> ПРОЙДИ РЕГИСТРАЦИЮ - Я ЛОГИРУЮ КАЖДОЕ ДЕЙСТВИЕ!")
        print("="*80 + "\n")
        
        # Держим браузер открытым 10 минут
        await page.wait_for_timeout(600000)
        
        await browser.close()
        print("\n>>> Логирование завершено")

if __name__ == "__main__":
    asyncio.run(main())

