"""
Chrome с прокси расширением для обхода Fiverr
"""
import subprocess
import time
import os
import json

def create_proxy_extension():
    """Создаем расширение для прокси"""
    extension_dir = "proxy_extension"
    os.makedirs(extension_dir, exist_ok=True)
    
    # manifest.json
    manifest = {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Proxy Extension",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        }
    }
    
    with open(f"{extension_dir}/manifest.json", "w") as f:
        json.dump(manifest, f)
    
    # background.js
    background_js = """
    chrome.proxy.settings.set({
        'value': {
            'mode': 'fixed_servers',
            'rules': {
                'singleProxy': {
                    'scheme': 'http',
                    'host': '91.92.66.141',
                    'port': 11762
                }
            }
        },
        'scope': 'regular'
    }, function() {});
    
    chrome.webRequest.onAuthRequired.addListener(
        function(details) {
            return {
                authCredentials: {
                    username: "W5H6ceq6XcdpZLEH",
                    password: "W5H6ceq6XcdpZLEH"
                }
            };
        },
        {urls: ["<all_urls>"]},
        ['blocking']
    );
    """
    
    with open(f"{extension_dir}/background.js", "w") as f:
        f.write(background_js)
    
    return os.path.abspath(extension_dir)

def main():
    print(">>> Запуск Chrome с прокси расширением...")
    
    # Создаем расширение
    extension_path = create_proxy_extension()
    print(f"Расширение создано: {extension_path}")
    
    # Путь к Chrome
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
    
    # Команда для запуска Chrome с расширением
    cmd = [
        chrome_path,
        f"--load-extension={extension_path}",
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-web-security",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "https://fiverr.com/join"
    ]
    
    print(">>> Запуск Chrome с прокси расширением...")
    print(f"Команда: {' '.join(cmd)}")
    
    # Запускаем Chrome
    process = subprocess.Popen(cmd)
    
    print("\n" + "="*80)
    print(">>> CHROME ЗАПУЩЕН С ПРОКСИ РАСШИРЕНИЕМ!")
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
