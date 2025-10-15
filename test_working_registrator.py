#!/usr/bin/env python3
"""
ТЕСТ РАБОЧЕГО РЕГИСТРАТОРА FIVERR
"""

import asyncio
from services.fiverr_registrator_working import FiverrWorkingRegistrator, register_accounts_batch
from services.email_api import EmailAPIService

async def test_registration():
    """Тест регистрации одного аккаунта"""
    print("="*80)
    print("ТЕСТ РАБОЧЕГО РЕГИСТРАТОРА FIVERR")
    print("="*80)
    
    try:
        async with EmailAPIService() as email_service:
            # Тестируем регистрацию одного аккаунта
            results = await register_accounts_batch(
                email_service=email_service,
                count=1,
                proxy=None
            )
            
            print(f"\nРезультаты регистрации:")
            for i, result in enumerate(results, 1):
                print(f"Аккаунт {i}:")
                if result["success"]:
                    print(f"  ✅ Успешно!")
                    print(f"  Email: {result['email']}")
                    print(f"  Username: {result['username']}")
                    print(f"  Password: {result['password']}")
                    print(f"  Cookies: {len(result.get('cookies', {}))} cookies")
                else:
                    print(f"  ❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
                    if 'response' in result:
                        print(f"  Response: {result['response'][:200]}...")
    
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_registration())
