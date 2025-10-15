"""
UNDETECTED ChromeDriver для обхода Fiverr
"""
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

def create_undetected_browser():
    """Создание максимально скрытного браузера"""
    options = uc.ChromeOptions()
    
    # ОТКЛЮЧАЕМ ВСЕ СЛЕДЫ АВТОМАТИЗАЦИИ
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # ОБЫЧНЫЕ НАСТРОЙКИ
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # USER AGENT
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    
    # ПРОКСИ
    options.add_argument("--proxy-server=http://W5H6ceq6XcdpZLEH:W5H6ceq6XcdpZLEH@91.92.66.141:11762")
    
    # Создаем undetected driver
    driver = uc.Chrome(options=options)
    
    # УБИРАЕМ webdriver
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # УБИРАЕМ chrome.runtime
    driver.execute_script("delete window.chrome.runtime")
    
    # ПОДДЕЛЫВАЕМ plugins
    driver.execute_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
                {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
                {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}
            ]
        });
    """)
    
    return driver

def human_like_delay(min_seconds=1, max_seconds=3):
    """Человеческие задержки"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def main():
    print(">>> Запуск UNDETECTED браузера...")
    
    driver = create_undetected_browser()
    
    try:
        print(">>> Переход на Fiverr...")
        driver.get("https://fiverr.com/join")
        human_like_delay(3, 5)
        
        print(">>> Проверяем что загрузилось...")
        print(f"URL: {driver.current_url}")
        print(f"Title: {driver.title}")
        
        # Проверяем есть ли капча
        if "human touch" in driver.page_source.lower():
            print("КАПЧА ОБНАРУЖЕНА!")
            print(">>> Пробуем обойти...")
            
            # Ищем кнопку PRESS & HOLD
            try:
                press_hold_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'PRESS & HOLD')]"))
                )
                print(">>> Найдена кнопка PRESS & HOLD")
                
                # Человеческое нажатие и удержание
                actions = ActionChains(driver)
                actions.click_and_hold(press_hold_button)
                actions.perform()
                
                print(">>> Удерживаем кнопку 3 секунды...")
                time.sleep(3)
                
                actions.release().perform()
                print(">>> Отпустили кнопку")
                
                human_like_delay(2, 4)
                
                # Проверяем результат
                if "human touch" not in driver.page_source.lower():
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
        time.sleep(600)  # 10 минут
        
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        driver.quit()
        print(">>> Браузер закрыт")

if __name__ == "__main__":
    main()
