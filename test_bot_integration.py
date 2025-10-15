#!/usr/bin/env python3
"""
ТЕСТ ИНТЕГРАЦИИ БОТА С НОВЫМ РЕГИСТРАТОРОМ
"""

import asyncio
import os
import sys

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fiverr_registrator_working import register_accounts_batch
from services.email_api import EmailAPIService

async def test_bot_integration():
    """Тест интеграции с ботом"""
    print("="*80)
    print("ТЕСТ ИНТЕГРАЦИИ БОТА С НОВЫМ РЕГИСТРАТОРОМ")
    print("="*80)
    
    try:
        async with EmailAPIService() as email_service:
            # Тестируем регистрацию одного аккаунта
            print("Запускаем регистрацию 1 аккаунта...")
            
            results = await register_accounts_batch(
                email_service=email_service,
                count=1,
                proxy=None
            )
            
            print(f"\nРезультаты регистрации:")
            for i, result in enumerate(results, 1):
                print(f"\n--- Аккаунт {i} ---")
                if result["success"]:
                    print(f"✅ Успешно!")
                    print(f"📧 Email: {result['email']}")
                    print(f"👤 Username: {result['username']}")
                    print(f"🔑 Password: {result['password']}")
                    print(f"🍪 Cookies: {len(result.get('cookies', {}))} cookies")
                    
                    if result.get('confirmation_code'):
                        print(f"🔐 Код подтверждения: {result['confirmation_code']}")
                    else:
                        print("🔐 Код подтверждения: не получен")
                    
                    # Показываем пример сообщения бота
                    print(f"\n📱 Пример сообщения бота:")
                    print(f"✅ Аккаунт #{i}")
                    print(f"📧 Email: {result['email']}")
                    print(f"👤 Username: {result['username']}")
                    print(f"🔑 Password: {result['password']}")
                    if result.get('confirmation_code'):
                        print(f"🔐 Код подтверждения: {result['confirmation_code']}")
                    print(f"📁 Cookies файл прикреплен ниже.")
                    
                else:
                    print(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
                    if 'response' in result:
                        print(f"📄 Response: {result['response'][:200]}...")
    
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bot_integration())
