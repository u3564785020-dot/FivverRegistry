"""
Chrome с автоматическим обходом капчи для Fiverr
"""
import subprocess
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

def create_stealth_browser():
    """Создание максимально скрытного браузера"""
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
    
    # USER AGENT
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    
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
    import random
    time.sleep(random.uniform(min_seconds, max_seconds))

def wait_for_captcha_and_solve(driver):
    """Ждем капчу и пытаемся её решить"""
    print(">>> Ожидание загрузки сайта (5-10 секунд)...")
    time.sleep(8)  # Ждем загрузку
    
    print(">>> Проверяем наличие капчи...")
    
    # Проверяем есть ли капча
    if "human touch" in driver.page_source.lower() or "нужно человеческое прикосновение" in driver.page_source.lower():
        print("КАПЧА ОБНАРУЖЕНА!")
        print(">>> Пробуем обойти...")
        
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
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        # Проверяем что элемент кликабельный и содержит текст капчи
                        if element.is_displayed() and element.is_enabled():
                            text = element.text.lower()
                            if any(word in text for word in ['press', 'hold', 'нажмите', 'удерживайте', 'touch', 'прикосновение']):
                                press_hold_button = element
                                print(f">>> Найдена кнопка капчи: {selector} - текст: '{element.text}'")
                                break
                    if press_hold_button:
                        break
                except Exception as e:
                    print(f"Ошибка с селектором {selector}: {e}")
                    continue
            
            if press_hold_button:
                print(">>> Найдена кнопка капчи")
                print(f">>> HTML кнопки: {press_hold_button.get_attribute('outerHTML')}")
                
                # Пробуем разные способы взаимодействия
                try:
                    # Способ 1: Обычный клик
                    print(">>> Способ 1: Обычный клик...")
                    press_hold_button.click()
                    time.sleep(2)
                    
                    # Проверяем результат
                    if "human touch" not in driver.page_source.lower() and "нужно человеческое прикосновение" not in driver.page_source.lower():
                        print("КАПЧА ПРОЙДЕНА через обычный клик!")
                        return True
                    
                except Exception as e:
                    print(f"Ошибка с обычным кликом: {e}")
                
                try:
                    # Способ 2: JavaScript клик
                    print(">>> Способ 2: JavaScript клик...")
                    driver.execute_script("arguments[0].click();", press_hold_button)
                    time.sleep(2)
                    
                    # Проверяем результат
                    if "human touch" not in driver.page_source.lower() and "нужно человеческое прикосновение" not in driver.page_source.lower():
                        print("КАПЧА ПРОЙДЕНА через JavaScript клик!")
                        return True
                        
                except Exception as e:
                    print(f"Ошибка с JavaScript кликом: {e}")
                
                try:
                    # Способ 3: ActionChains с удержанием
                    print(">>> Способ 3: ActionChains с удержанием...")
                    actions = ActionChains(driver)
                    actions.move_to_element(press_hold_button)
                    actions.click_and_hold(press_hold_button)
                    actions.perform()
                    
                    print(">>> Удерживаем кнопку 3 секунды...")
                    time.sleep(3)
                    
                    actions.release().perform()
                    print(">>> Отпустили кнопку")
                    
                    # Проверяем результат
                    if "human touch" not in driver.page_source.lower() and "нужно человеческое прикосновение" not in driver.page_source.lower():
                        print("КАПЧА ПРОЙДЕНА через удержание!")
                        return True
                        
                except Exception as e:
                    print(f"Ошибка с удержанием: {e}")
                
                try:
                    # Способ 4: JavaScript события
                    print(">>> Способ 4: JavaScript события...")
                    driver.execute_script("""
                        var element = arguments[0];
                        var events = ['mousedown', 'mouseup', 'click', 'touchstart', 'touchend'];
                        events.forEach(function(event) {
                            var evt = new Event(event, {bubbles: true, cancelable: true});
                            element.dispatchEvent(evt);
                        });
                    """, press_hold_button)
                    time.sleep(2)
                    
                    # Проверяем результат
                    if "human touch" not in driver.page_source.lower() and "нужно человеческое прикосновение" not in driver.page_source.lower():
                        print("КАПЧА ПРОЙДЕНА через JavaScript события!")
                        return True
                        
                except Exception as e:
                    print(f"Ошибка с JavaScript событиями: {e}")
                
                human_like_delay(2, 4)
                
                # Проверяем результат
                if "human touch" not in driver.page_source.lower() and "нужно человеческое прикосновение" not in driver.page_source.lower():
                    print("КАПЧА ПРОЙДЕНА!")
                    return True
                else:
                    print("Капча не пройдена, пробуем еще раз...")
                    return False
            else:
                print("Кнопка капчи не найдена")
                return False
                
        except Exception as e:
            print(f"Ошибка с капчей: {e}")
            return False
    else:
        print("Капчи нет, продолжаем...")
        return True

def main():
    print(">>> Запуск Chrome с автоматическим обходом капчи...")
    
    driver = create_stealth_browser()
    
    try:
        print(">>> Переход на Fiverr...")
        driver.get("https://fiverr.com/join")
        
        print(">>> Проверяем что загрузилось...")
        print(f"URL: {driver.current_url}")
        print(f"Title: {driver.title}")
        
        # Ждем и решаем капчу
        captcha_solved = wait_for_captcha_and_solve(driver)
        
        if not captcha_solved:
            print(">>> Капча не решена автоматически, пробуем еще раз...")
            time.sleep(5)
            captcha_solved = wait_for_captcha_and_solve(driver)
        
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
