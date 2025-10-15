#!/usr/bin/env python3
"""
ПРОСТОЙ БРАУЗЕР ДЛЯ РУЧНОЙ РЕГИСТРАЦИИ FIVERR
"""

import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os

def log_action(action_type, description, driver):
    """Логирование действия"""
    timestamp = datetime.now().isoformat()
    url = driver.current_url
    title = driver.title
    
    print(f"[{timestamp}] {action_type}: {description}")
    print(f"URL: {url}")
    print(f"Title: {title}")
    print("-" * 50)
    
    # Делаем скриншот
    try:
        os.makedirs("screenshots", exist_ok=True)
        screenshot_path = f"screenshots/action_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")
    except Exception as e:
        print(f"Screenshot error: {e}")

def log_forms(driver):
    """Логирование форм"""
    try:
        forms = driver.find_elements(By.TAG_NAME, "form")
        print(f"Found {len(forms)} forms on page")
        
        for i, form in enumerate(forms):
            action = form.get_attribute('action')
            method = form.get_attribute('method')
            print(f"Form {i+1}: {method} -> {action}")
            
            # Логируем input поля
            inputs = form.find_elements(By.TAG_NAME, "input")
            for j, input_elem in enumerate(inputs):
                name = input_elem.get_attribute('name')
                input_type = input_elem.get_attribute('type')
                placeholder = input_elem.get_attribute('placeholder')
                print(f"  Input {j+1}: name='{name}' type='{input_type}' placeholder='{placeholder}'")
                
    except Exception as e:
        print(f"Form logging error: {e}")

def log_cookies(driver):
    """Логирование cookies"""
    try:
        cookies = driver.get_cookies()
        print(f"Found {len(cookies)} cookies")
        
        for cookie in cookies:
            print(f"Cookie: {cookie['name']} = {cookie['value'][:50]}...")
            
    except Exception as e:
        print(f"Cookie logging error: {e}")

def main():
    """Основная функция"""
    print("="*80)
    print("SIMPLE MANUAL FIVERR REGISTRATION BROWSER")
    print("="*80)
    
    # Настройка браузера
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    
    driver = None
    
    try:
        # Запуск браузера
        print("Starting browser...")
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("Browser started! Opening Fiverr...")
        
        # Открываем Fiverr
        driver.get("https://www.fiverr.com")
        log_action("page_load", "Opened Fiverr main page", driver)
        
        # Логируем начальные данные
        log_forms(driver)
        log_cookies(driver)
        
        print("\n" + "="*80)
        print("MANUAL REGISTRATION STARTED!")
        print("="*80)
        print("Now do the following:")
        print("1. Go to registration page")
        print("2. Fill in all fields")
        print("3. Complete registration")
        print("4. I'll log everything!")
        print("="*80)
        print("Browser is ready! Start registering manually!")
        print("Press Ctrl+C to stop and save data")
        print("="*80)
        
        # Мониторим изменения
        previous_url = driver.current_url
        action_count = 1
        
        while True:
            try:
                current_url = driver.current_url
                
                # Проверяем изменение URL
                if current_url != previous_url:
                    log_action("navigation", f"Navigated to {current_url}", driver)
                    previous_url = current_url
                    
                    # Логируем данные новой страницы
                    log_forms(driver)
                    log_cookies(driver)
                
                # Проверяем каждую секунду
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
                break
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(1)
        
        # Финальное логирование
        print("\n" + "="*80)
        print("FINAL LOGGING")
        print("="*80)
        
        log_forms(driver)
        log_cookies(driver)
        
        print("\nLogging completed!")
        print("="*80)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if driver:
            print("Closing browser...")
            driver.quit()
            print("Browser closed")

if __name__ == "__main__":
    main()
