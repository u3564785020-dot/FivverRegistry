"""
Тестовый скрипт для проверки работы прокси
"""
import asyncio
import sys
sys.path.append('..')

from services.proxy_manager import ProxyConfig, ProxyManager
from utils.logger import logger


async def test_proxy():
    """Тестирование прокси"""
    
    print("=" * 50)
    print("🧪 Тестирование прокси")
    print("=" * 50)
    
    # Запрашиваем прокси у пользователя
    proxy_string = input("\nВведите прокси в формате username:password@ip:port:\n> ")
    
    # Парсим прокси
    print("\n1️⃣ Парсинг прокси...")
    proxy = ProxyConfig.from_string(proxy_string)
    
    if not proxy:
        print("❌ Неверный формат прокси")
        return
    
    print(f"✅ Прокси распознан:")
    print(f"   Host: {proxy.host}")
    print(f"   Port: {proxy.port}")
    print(f"   Username: {proxy.username}")
    print(f"   Password: {'*' * len(proxy.password)}")
    
    # Проверяем работоспособность
    print("\n2️⃣ Проверка работоспособности прокси...")
    print("Это может занять несколько секунд...")
    
    is_working = await ProxyManager.check_proxy(proxy, timeout=15)
    
    if is_working:
        print("✅ Прокси работает!")
        
        # Получаем IP
        print("\n3️⃣ Получение IP адреса...")
        ip = await ProxyManager.get_proxy_ip(proxy)
        if ip:
            print(f"✅ IP адрес прокси: {ip}")
        else:
            print("⚠️ Не удалось получить IP адрес")
    else:
        print("❌ Прокси не работает или недоступен")
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_proxy())

