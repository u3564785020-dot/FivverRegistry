"""
РЕАЛЬНЫЙ Chrome через subprocess для обхода Fiverr
"""
import subprocess
import time
import os

def main():
    print(">>> Запуск РЕАЛЬНОГО Chrome...")
    
    # Путь к Chrome (обычно в Program Files)
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME'))
    ]
    
    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break
    
    if not chrome_path:
        print("❌ Chrome не найден!")
        return
    
    # Команда для запуска Chrome с прокси
    cmd = [
        chrome_path,
        "--proxy-server=http://W5H6ceq6XcdpZLEH:W5H6ceq6XcdpZLEH@91.92.66.141:11762",
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-web-security",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "https://fiverr.com/join"
    ]
    
    print(">>> Запуск Chrome с прокси...")
    print(f"Команда: {' '.join(cmd)}")
    
    # Запускаем Chrome
    process = subprocess.Popen(cmd)
    
    print("\n" + "="*80)
    print(">>> CHROME ЗАПУЩЕН!")
    print(">>> ПРОЙДИ РЕГИСТРАЦИЮ ВРУЧНУЮ!")
    print(">>> Chrome будет открыт 10 минут...")
    print("="*80 + "\n")
    
    # Ждем 10 минут
    time.sleep(600)
    
    # Закрываем Chrome
    process.terminate()
    print(">>> Chrome закрыт")

if __name__ == "__main__":
    main()
