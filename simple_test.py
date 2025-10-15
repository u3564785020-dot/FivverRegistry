#!/usr/bin/env python3
"""
ПРОСТОЙ ТЕСТ РЕГИСТРАТОРА БЕЗ ЗАВИСИМОСТЕЙ
"""

import asyncio
import aiohttp
import random
import string
import re

class SimpleFiverrRegistrator:
    def __init__(self):
        self.session = None
        self.csrf_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_username(self):
        """Генерация случайного имени пользователя в формате text_text"""
        word1 = ''.join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
        word2 = ''.join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
        return f"{word1}_{word2}"
    
    def _generate_password(self):
        """Генерация надежного пароля"""
        length = random.randint(8, 12)
        uppercase = random.choice(string.ascii_uppercase)
        lowercase = random.choice(string.ascii_lowercase)
        digit = random.choice(string.digits)
        remaining = ''.join(random.choices(string.ascii_letters + string.digits, k=length - 3))
        password = list(uppercase + lowercase + digit + remaining)
        random.shuffle(password)
        return ''.join(password)
    
    async def register_account(self, email: str):
        """Регистрация аккаунта"""
        try:
            print(f"Начинаем регистрацию с email: {email}")
            
            # Получаем главную страницу для CSRF токена
            url = "https://it.fiverr.com/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'it,it-IT;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Not:A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    print("Главная страница загружена")
                    
                    # Ищем CSRF токен
                    csrf_patterns = [
                        r'name="csrf_token"\s+value="([^"]+)"',
                        r'name="_token"\s+value="([^"]+)"',
                        r'"csrf_token":"([^"]+)"',
                        r'window\.csrf_token\s*=\s*["\']([^"\']+)["\']',
                        r'<meta name="csrf-token" content="([^"]+)"'
                    ]
                    
                    for pattern in csrf_patterns:
                        match = re.search(pattern, html)
                        if match:
                            self.csrf_token = match.group(1)
                            print(f"CSRF токен найден: {self.csrf_token[:20]}...")
                            break
                    
                    if not self.csrf_token:
                        print("CSRF токен не найден, продолжаем без него")
                else:
                    print(f"Ошибка загрузки главной страницы: {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}
            
            # Генерируем данные
            username = self._generate_username()
            password = self._generate_password()
            
            print(f"Username: {username}")
            print(f"Password: {password}")
            
            # Подготавливаем данные для регистрации
            registration_data = {
                'user[email]': email,
                'user[password]': password,
                'user[username]': username,
                'funnel': 'standard'
            }
            
            # Подготавливаем заголовки
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'it,it-IT;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Content-Type': 'multipart/form-data',
                'Origin': 'https://it.fiverr.com',
                'Referer': 'https://it.fiverr.com/login?source=top_nav',
                'X-Requested-With': 'XMLHttpRequest',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Priority': 'u=1, i'
            }
            
            # Добавляем CSRF токен если есть
            if self.csrf_token:
                headers['X-Csrf-Token'] = self.csrf_token
            
            # URL для регистрации
            url = "https://it.fiverr.com/users"
            
            # Создаем FormData для multipart/form-data
            form_data = aiohttp.FormData()
            for key, value in registration_data.items():
                form_data.add_field(key, str(value))
            
            print("Отправляем запрос регистрации...")
            
            # Выполняем запрос регистрации
            async with self.session.post(url, data=form_data, headers=headers) as response:
                response_text = await response.text()
                print(f"Ответ сервера: {response.status}")
                print(f"Тело ответа: {response_text[:200]}...")
                
                if response.status == 200:
                    try:
                        response_data = await response.json()
                        print("Регистрация успешна!")
                        return {
                            "success": True,
                            "email": email,
                            "username": username,
                            "password": password,
                            "response": response_data
                        }
                    except:
                        print("Регистрация успешна (не JSON ответ)")
                        return {
                            "success": True,
                            "email": email,
                            "username": username,
                            "password": password,
                            "response": response_text
                        }
                else:
                    print(f"Ошибка регистрации: {response.status}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "response": response_text
                    }
                    
        except Exception as e:
            print(f"Критическая ошибка: {e}")
            return {"success": False, "error": str(e)}

async def test_simple_registration():
    """Простой тест регистрации"""
    print("="*80)
    print("ПРОСТОЙ ТЕСТ РЕГИСТРАТОРА FIVERR")
    print("="*80)
    
    # Тестовый email
    test_email = "test@example.com"
    
    async with SimpleFiverrRegistrator() as registrator:
        result = await registrator.register_account(test_email)
        
        print(f"\nРезультат регистрации:")
        if result["success"]:
            print(f"✅ Успешно!")
            print(f"Email: {result['email']}")
            print(f"Username: {result['username']}")
            print(f"Password: {result['password']}")
        else:
            print(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
            if 'response' in result:
                print(f"Response: {result['response'][:200]}...")

if __name__ == "__main__":
    asyncio.run(test_simple_registration())
