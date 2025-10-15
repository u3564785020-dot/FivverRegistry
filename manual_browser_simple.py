#!/usr/bin/env python3
"""
ПРОСТОЙ БРАУЗЕР ДЛЯ РУЧНОЙ РЕГИСТРАЦИИ FIVERR
Открывает браузер и сразу начинает логирование
"""

import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os

class SimpleManualBrowser:
    def __init__(self):
        self.driver = None
        self.log_data = {
            'timestamp': datetime.now().isoformat(),
            'actions': [],
            'forms': [],
            'cookies': {},
            'screenshots': []
        }
        self.action_counter = 0
        
    def setup_browser(self):
        """Настройка браузера"""
        print("="*80)
        print("MANUAL FIVERR REGISTRATION BROWSER")
        print("="*80)
        print("Browser will open and log EVERYTHING you do!")
        print("="*80)
        
        options = Options()
        
        # Отключаем автоматизацию
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Обычные настройки
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-web-security")
        
        # Headers
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=options)
        
        # Убираем webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("Browser opened! Go to Fiverr and register manually!")
        print("I'll log everything you do...")
        
    def log_action(self, action_type: str, description: str, element_info: dict = None):
        """Логирование действия"""
        self.action_counter += 1
        
        action_data = {
            'action_number': self.action_counter,
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'description': description,
            'url': self.driver.current_url,
            'title': self.driver.title,
            'element_info': element_info or {}
        }
        
        self.log_data['actions'].append(action_data)
        
        print(f"Action {self.action_counter}: {action_type} - {description}")
        
        # Делаем скриншот
        try:
            os.makedirs("screenshots", exist_ok=True)
            screenshot_path = f"screenshots/action_{self.action_counter}_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            self.log_data['screenshots'].append(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            print(f"Screenshot error: {e}")
    
    def log_forms(self):
        """Логирование форм"""
        try:
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            
            for i, form in enumerate(forms):
                form_info = {
                    'form_number': i + 1,
                    'action': form.get_attribute('action'),
                    'method': form.get_attribute('method'),
                    'enctype': form.get_attribute('enctype'),
                    'inputs': []
                }
                
                # Логируем все input поля
                inputs = form.find_elements(By.TAG_NAME, "input")
                for j, input_elem in enumerate(inputs):
                    input_info = {
                        'input_number': j + 1,
                        'name': input_elem.get_attribute('name'),
                        'type': input_elem.get_attribute('type'),
                        'value': input_elem.get_attribute('value'),
                        'placeholder': input_elem.get_attribute('placeholder'),
                        'required': input_elem.get_attribute('required'),
                        'id': input_elem.get_attribute('id'),
                        'class': input_elem.get_attribute('class')
                    }
                    form_info['inputs'].append(input_info)
                
                self.log_data['forms'].append(form_info)
                print(f"Form {i+1}: {form_info['method']} -> {form_info['action']}")
                print(f"    Inputs: {len(form_info['inputs'])}")
                
        except Exception as e:
            print(f"Form logging error: {e}")
    
    def log_cookies(self):
        """Логирование cookies"""
        try:
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                self.log_data['cookies'][cookie['name']] = cookie['value']
            
            print(f"Cookies logged: {len(cookies)}")
            
        except Exception as e:
            print(f"Cookie logging error: {e}")
    
    def start_logging(self):
        """Запуск логирования"""
        try:
            # Открываем Fiverr
            print("\nOpening Fiverr...")
            self.driver.get("https://www.fiverr.com")
            self.log_action("page_load", "Opened Fiverr main page")
            
            # Логируем начальные данные
            self.log_forms()
            self.log_cookies()
            
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
            print("Press Ctrl+C to stop logging and save data")
            print("="*80)
            
            # Мониторим действия
            self.monitor_actions()
            
        except Exception as e:
            print(f"Error: {e}")
    
    def monitor_actions(self):
        """Мониторинг действий"""
        print("\nMonitoring your actions...")
        print("I'll log everything you do!")
        
        previous_url = self.driver.current_url
        
        try:
            while True:
                # Проверяем изменение URL
                current_url = self.driver.current_url
                if current_url != previous_url:
                    self.log_action("navigation", f"Navigated to {current_url}")
                    previous_url = current_url
                    
                    # Логируем данные новой страницы
                    self.log_forms()
                    self.log_cookies()
                
                time.sleep(1)  # Проверяем каждую секунду
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
            self.finish_logging()
    
    def finish_logging(self):
        """Завершение логирования"""
        print("\n" + "="*80)
        print("GENERATING FINAL REPORT")
        print("="*80)
        
        # Финальные данные
        self.log_forms()
        self.log_cookies()
        
        # Статистика
        print(f"\nSTATISTICS:")
        print(f"Total actions logged: {len(self.log_data['actions'])}")
        print(f"Total forms found: {len(self.log_data['forms'])}")
        print(f"Total cookies: {len(self.log_data['cookies'])}")
        print(f"Total screenshots: {len(self.log_data['screenshots'])}")
        
        # Сохраняем лог
        with open('manual_registration_complete_log.json', 'w', encoding='utf-8') as f:
            json.dump(self.log_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nComplete log saved to: manual_registration_complete_log.json")
        print(f"Screenshots saved in: screenshots/")
        
        print("\nUse this data to create working registration code!")
        print("="*80)
    
    def close_browser(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            print("Browser closed")

def main():
    """Основная функция"""
    browser = SimpleManualBrowser()
    
    try:
        browser.setup_browser()
        browser.start_logging()
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        browser.finish_logging()
        browser.close_browser()

if __name__ == "__main__":
    main()
