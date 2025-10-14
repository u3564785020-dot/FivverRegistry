# 📚 Примеры использования

Практические примеры работы с ботом.

## 🎯 Базовые сценарии

### 1. Регистрация одного аккаунта

```
Пользователь → /register
Бот → Укажите количество аккаунтов

Пользователь → 1
Бот → Отправьте 1 прокси

Пользователь → user123:pass456@192.168.1.1:8080
Бот → ✅ Задача создана! Начинаю регистрацию...

[Через 2-3 минуты]
Бот → ✅ Аккаунт #1
      Email: example@gmx.com
      Пароль: AbCd1234!@#$
      [Отправляет cookies файл]

Бот → 📊 Регистрация завершена!
      ✅ Успешно: 1
      ❌ Ошибок: 0
```

### 2. Массовая регистрация (5 аккаунтов)

```
Пользователь → /register
Бот → Укажите количество аккаунтов

Пользователь → 5
Бот → Отправьте 5 прокси

Пользователь → 
user1:pass1@192.168.1.1:8080
user2:pass2@192.168.1.2:8080
user3:pass3@192.168.1.3:8080
user4:pass4@192.168.1.4:8080
user5:pass5@192.168.1.5:8080

Бот → ✅ Задача создана! Начинаю регистрацию...

[Регистрация идет параллельно, через 5-10 минут]

Бот → ✅ Аккаунт #1 [+ cookies]
Бот → ✅ Аккаунт #2 [+ cookies]
Бот → ✅ Аккаунт #3 [+ cookies]
Бот → ✅ Аккаунт #4 [+ cookies]
Бот → ✅ Аккаунт #5 [+ cookies]

Бот → 📊 Регистрация завершена!
      ✅ Успешно: 5
```

### 3. Проверка баланса

```
Пользователь → /balance
Бот → 🔍 Проверяю баланс...

Бот → 💰 Баланс: $10.5000

      📧 Доступные почты для Fiverr:
      • gmx.com: 128539 шт. ($0.0015)
      • mail.com: 12651 шт. ($0.0015)
      • email.com: 10571 шт. ($0.0015)
```

### 4. Просмотр задач

```
Пользователь → /tasks
Бот → 📋 Ваши задачи:

      ✅ a1b2c3d4
      Статус: completed
      Прогресс: 5/5
      Успешно: 5 | Ошибок: 0

      🔄 e5f6g7h8
      Статус: running
      Прогресс: 2/10
      Успешно: 2 | Ошибок: 0
```

### 5. Просмотр аккаунтов

```
Пользователь → /accounts
Бот → 📧 Ваши аккаунты (15):

      1. example1@gmx.com
         Создан: 2025-10-14 10:30

      2. example2@mail.com
         Создан: 2025-10-14 10:35

      3. example3@email.com
         Создан: 2025-10-14 10:40
      ...
```

## 🔧 Программные примеры

### Использование Email API

```python
import asyncio
from services.email_api import EmailAPIService

async def example_email_usage():
    async with EmailAPIService() as email_service:
        # Проверка баланса
        balance = await email_service.get_balance()
        print(f"Баланс: ${balance}")
        
        # Получение доступных почт
        domains = await email_service.get_available_emails("fiverr.com")
        print(f"Доступно доменов: {len(domains)}")
        
        # Заказ почты
        email_data = await email_service.order_email(
            site="fiverr.com",
            domain="gmx.com"
        )
        print(f"Email: {email_data['email']}")
        print(f"ID: {email_data['id']}")
        
        # Получение сообщения
        message = await email_service.get_message(
            activation_id=email_data['id'],
            max_retries=30
        )
        print(f"Код: {message['value']}")

asyncio.run(example_email_usage())
```

### Использование Proxy Manager

```python
import asyncio
from services.proxy_manager import ProxyConfig, ProxyManager

async def example_proxy_usage():
    # Парсинг прокси
    proxy_string = "user:pass@192.168.1.1:8080"
    proxy = ProxyConfig.from_string(proxy_string)
    
    print(f"Host: {proxy.host}")
    print(f"Port: {proxy.port}")
    
    # Проверка прокси
    is_working = await ProxyManager.check_proxy(proxy)
    if is_working:
        print("✅ Прокси работает")
        
        # Получение IP
        ip = await ProxyManager.get_proxy_ip(proxy)
        print(f"IP: {ip}")
    else:
        print("❌ Прокси не работает")

asyncio.run(example_proxy_usage())
```

### Использование Database

```python
import asyncio
from services.database import db

async def example_database_usage():
    # Подключение
    await db.connect()
    
    # Добавление пользователя
    await db.add_user(user_id=123456789, username="john_doe")
    
    # Создание задачи
    await db.create_task(
        task_id="task-123",
        user_id=123456789,
        total_accounts=5,
        proxies=["proxy1", "proxy2"]
    )
    
    # Сохранение аккаунта
    await db.save_account(
        email="test@gmx.com",
        password="password123",
        user_id=123456789,
        task_id="task-123",
        cookies={"cookie1": "value1"},
        proxy="user:pass@ip:port"
    )
    
    # Получение аккаунтов пользователя
    accounts = await db.get_user_accounts(user_id=123456789)
    for account in accounts:
        print(f"Email: {account['email']}")
    
    # Отключение
    await db.disconnect()

asyncio.run(example_database_usage())
```

### Регистрация с кастомными настройками

```python
import asyncio
from services.email_api import EmailAPIService
from services.proxy_manager import ProxyConfig
from services.fiverr_registrator import FiverrRegistrator

async def custom_registration():
    # Настройка прокси
    proxy = ProxyConfig.from_string("user:pass@192.168.1.1:8080")
    
    async with EmailAPIService() as email_service:
        # Создание регистратора
        registrator = FiverrRegistrator(
            email_service=email_service,
            proxy=proxy
        )
        
        # Регистрация аккаунта
        result = await registrator.register_account()
        
        if result and result['success']:
            print(f"✅ Успех!")
            print(f"Email: {result['email']}")
            print(f"Пароль: {result['password']}")
            print(f"Cookies: {result['cookies_file']}")
        else:
            print("❌ Ошибка регистрации")

asyncio.run(custom_registration())
```

## 🎨 Кастомизация

### Изменение максимального количества параллельных регистраций

```python
# config.py
MAX_CONCURRENT_REGISTRATIONS = 10  # Увеличено с 5 до 10
```

### Изменение таймаутов

```python
# config.py
BROWSER_TIMEOUT = 120000  # 2 минуты вместо 1
REGISTRATION_TIMEOUT = 600  # 10 минут вместо 5
```

### Добавление кастомного домена email

```python
# В handlers.py, функция start_registration
email_data = await email_service.order_email(
    site="fiverr.com",
    domain="outlook.com"  # Используем Outlook вместо GMX
)
```

### Настройка user agent

```python
# В fiverr_registrator.py
from fake_useragent import UserAgent

ua = UserAgent(browsers=['chrome', 'firefox'])
custom_ua = ua.random

context_options = {
    "user_agent": custom_ua,
    # ... остальные настройки
}
```

## 🧪 Тестирование

### Тест Email API

```bash
cd tests
python test_email_api.py
```

**Пример вывода:**
```
==================================================
🧪 Тестирование Email API
==================================================

1️⃣ Проверка баланса...
✅ Баланс: $10.5000

2️⃣ Получение доступных почт для Fiverr...
✅ Найдено доменов: 9
   • gmx.com: 128539 шт. по $0.0015
   • mail.com: 12651 шт. по $0.0015
   ...

3️⃣ Заказать тестовую почту? (y/n): y
Заказ почты...
✅ Почта заказана:
   Email: test@gmx.com
   ID: 123456

Отмена активации...
✅ Активация отменена

==================================================
✅ Тестирование завершено!
==================================================
```

### Тест Proxy

```bash
cd tests
python test_proxy.py
```

**Пример вывода:**
```
==================================================
🧪 Тестирование прокси
==================================================

Введите прокси в формате username:password@ip:port:
> user:pass@192.168.1.1:8080

1️⃣ Парсинг прокси...
✅ Прокси распознан:
   Host: 192.168.1.1
   Port: 8080
   Username: user
   Password: ****

2️⃣ Проверка работоспособности прокси...
Это может занять несколько секунд...
✅ Прокси работает!

3️⃣ Получение IP адреса...
✅ IP адрес прокси: 192.168.1.1

==================================================
✅ Тестирование завершено!
==================================================
```

## 📊 Мониторинг

### Просмотр логов в реальном времени

**Linux/Mac:**
```bash
tail -f logs/bot_2025-10-14.log
```

**Windows:**
```powershell
Get-Content logs\bot_2025-10-14.log -Wait
```

### Просмотр только ошибок

```bash
grep ERROR logs/bot_2025-10-14.log
```

### Подсчет успешных регистраций

```bash
grep "Регистрация успешна" logs/bot_2025-10-14.log | wc -l
```

## 🔄 CI/CD

### Автоматический деплой при пуше

```bash
# Внесите изменения
git add .
git commit -m "feat: Add new feature"
git push origin main

# Railway автоматически:
# 1. Обнаружит изменения
# 2. Соберет Docker образ
# 3. Задеплоит новую версию
# 4. Перезапустит бота
```

### Откат к предыдущей версии

```bash
# В Railway Dashboard
Deployments → [Выберите предыдущий деплой] → Redeploy
```

## 💡 Полезные команды

### Экспорт аккаунтов в CSV

```python
import asyncio
import csv
from services.database import db

async def export_accounts_to_csv():
    await db.connect()
    
    accounts = await db.get_user_accounts(user_id=123456789, limit=1000)
    
    with open('accounts.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['email', 'password', 'created_at'])
        writer.writeheader()
        
        for account in accounts:
            writer.writerow({
                'email': account['email'],
                'password': account['password'],
                'created_at': account['created_at']
            })
    
    print(f"Экспортировано {len(accounts)} аккаунтов")
    await db.disconnect()

asyncio.run(export_accounts_to_csv())
```

### Массовая проверка прокси

```python
import asyncio
from services.proxy_manager import ProxyConfig, ProxyManager

async def check_multiple_proxies(proxy_list):
    results = []
    
    for proxy_string in proxy_list:
        proxy = ProxyConfig.from_string(proxy_string)
        if proxy:
            is_working = await ProxyManager.check_proxy(proxy)
            results.append({
                'proxy': str(proxy),
                'working': is_working
            })
    
    return results

# Использование
proxies = [
    "user1:pass1@192.168.1.1:8080",
    "user2:pass2@192.168.1.2:8080",
    "user3:pass3@192.168.1.3:8080"
]

results = asyncio.run(check_multiple_proxies(proxies))
for r in results:
    status = "✅" if r['working'] else "❌"
    print(f"{status} {r['proxy']}")
```

---

**Больше примеров в коде!**

Изучите файлы в директории `services/` для понимания внутренней работы.

