"""
Тестовый скрипт для проверки работы Email API
"""
import asyncio
import sys
sys.path.append('..')

from services.email_api import EmailAPIService
from utils.logger import logger


async def test_email_api():
    """Тестирование функций Email API"""
    
    print("=" * 50)
    print("🧪 Тестирование Email API")
    print("=" * 50)
    
    async with EmailAPIService() as email_service:
        # 1. Проверка баланса
        print("\n1️⃣ Проверка баланса...")
        balance = await email_service.get_balance()
        if balance is not None:
            print(f"✅ Баланс: ${balance:.4f}")
        else:
            print("❌ Ошибка получения баланса")
            return
        
        # 2. Получение доступных почт
        print("\n2️⃣ Получение доступных почт для Fiverr...")
        domains = await email_service.get_available_emails("fiverr.com")
        if domains:
            print(f"✅ Найдено доменов: {len(domains)}")
            for domain, info in list(domains.items())[:5]:
                count = info.get('count', 0)
                price = info.get('price', 0)
                print(f"   • {domain}: {count} шт. по ${price}")
        else:
            print("❌ Ошибка получения списка почт")
            return
        
        # 3. Тест заказа почты (опционально)
        response = input("\n3️⃣ Заказать тестовую почту? (y/n): ")
        if response.lower() == 'y':
            print("Заказ почты...")
            email_data = await email_service.order_email(
                site="fiverr.com",
                domain="gmx.com"
            )
            
            if email_data:
                print(f"✅ Почта заказана:")
                print(f"   Email: {email_data['email']}")
                print(f"   ID: {email_data['id']}")
                
                # Отменяем активацию
                print("\nОтмена активации...")
                if await email_service.cancel_email(email_data['id']):
                    print("✅ Активация отменена")
                else:
                    print("❌ Ошибка отмены активации")
            else:
                print("❌ Ошибка заказа почты")
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_email_api())

