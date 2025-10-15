"""
Обработчики команд Telegram бота
"""
import asyncio
import uuid
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from utils.logger import logger
from services.database import db
from services.email_api import EmailAPIService
from services.proxy_manager import ProxyConfig, ProxyManager
from services.fiverr_registrator_playwright import FiverrRegistrator
from config import ADMIN_IDS, MAX_CONCURRENT_REGISTRATIONS


# === Вспомогательные функции ===

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


async def send_long_message(update: Update, text: str):
    """Отправка длинного сообщения с разбивкой на части"""
    max_length = 4096
    for i in range(0, len(text), max_length):
        await update.message.reply_text(
            text[i:i + max_length],
            parse_mode=ParseMode.HTML
        )


# === Обработчики команд ===

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Добавляем пользователя в базу
    await db.add_user(user.id, user.username)
    
    welcome_text = f"""
👋 <b>Привет, {user.first_name}!</b>

Я бот для автоматической регистрации аккаунтов на Fiverr.

<b>Доступные команды:</b>
/start - Показать это сообщение
/proxy_toggle - Переключить использование прокси
/help - Подробная справка
/balance - Проверить баланс API почт
/register - Начать регистрацию аккаунтов
/tasks - Просмотр ваших задач
/accounts - Список ваших аккаунтов

<b>Возможности:</b>
✅ Автоматическая регистрация
✅ Поддержка прокси
✅ Многопоточность
✅ Автоматическое получение cookies
✅ История всех операций

Для начала работы используйте /register
"""
    
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)
    logger.info(f"Пользователь {user.id} ({user.username}) запустил бота")


async def proxy_toggle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /proxy_toggle"""
    user_id = update.effective_user.id
    
    # Получаем текущее состояние прокси из контекста
    current_proxy_state = context.user_data.get('use_proxy', True)
    new_proxy_state = not current_proxy_state
    
    # Сохраняем новое состояние
    context.user_data['use_proxy'] = new_proxy_state
    
    status_text = "включены" if new_proxy_state else "отключены"
    emoji = "✅" if new_proxy_state else "❌"
    
    await update.message.reply_text(
        f"{emoji} <b>Прокси {status_text}</b>\n\n"
        f"Следующая регистрация будет использовать {'прокси' if new_proxy_state else 'прямое подключение'}.",
        parse_mode=ParseMode.HTML
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📖 <b>Подробная справка</b>

<b>1. Регистрация аккаунтов (/register)</b>
Команда запустит интерактивный процесс регистрации:
- Укажите количество аккаунтов
- Отправьте прокси (по одному на строку) или отключите прокси
- Бот начнет регистрацию

<b>2. Управление прокси (/proxy_toggle)</b>
Переключает использование прокси:
- ✅ Прокси включены - использует указанные прокси
- ❌ Прокси отключены - прямое подключение без прокси

<b>3. Формат прокси:</b>
<code>username:password@ip:port</code>

Пример:
<code>user123:pass456@192.168.1.1:8080</code>

<b>4. Проверка баланса (/balance)</b>
Показывает текущий баланс API для покупки почт

<b>5. Просмотр задач (/tasks)</b>
Список всех ваших задач на регистрацию с их статусами

<b>6. Просмотр аккаунтов (/accounts)</b>
Список всех успешно зарегистрированных аккаунтов

<b>❗ Важно:</b>
- Один прокси = один аккаунт (если прокси включены)
- Регистрация может занять 2-5 минут на аккаунт
- Cookies сохраняются автоматически
- Поддерживается до {MAX_CONCURRENT_REGISTRATIONS} параллельных регистраций
"""
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /balance"""
    user_id = update.effective_user.id
    
    await update.message.reply_text("🔍 Проверяю баланс...")
    
    try:
        async with EmailAPIService() as email_service:
            balance = await email_service.get_balance()
            
            if balance is not None:
                # Получаем доступные домены
                domains = await email_service.get_available_emails()
                
                response = f"💰 <b>Баланс:</b> ${balance:.4f}\n\n"
                
                if domains:
                    response += "<b>📧 Доступные почты для Fiverr:</b>\n"
                    for domain, info in domains.items():
                        count = info.get('count', 0)
                        price = info.get('price', 0)
                        if count > 0:
                            response += f"• {domain}: {count} шт. (${price})\n"
                else:
                    response += "⚠️ Нет доступных почт"
                
                await update.message.reply_text(response, parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(
                    "❌ Ошибка при получении баланса. Проверьте API токен.",
                    parse_mode=ParseMode.HTML
                )
    except Exception as e:
        logger.error(f"Ошибка в balance_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при проверке баланса",
            parse_mode=ParseMode.HTML
        )


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /register"""
    user_id = update.effective_user.id
    
    # Проверяем активность пользователя
    if not await db.is_user_active(user_id):
        await update.message.reply_text(
            "❌ Ваш аккаунт неактивен. Обратитесь к администратору."
        )
        return
    
    # Проверяем, включены ли прокси
    use_proxy = context.user_data.get('use_proxy', True)
    
    if use_proxy:
        text = """
📝 <b>Регистрация аккаунтов Fiverr</b>

<b>Шаг 1:</b> Выберите домен для покупки почты

<b>Доступные домены:</b>
• gmx.com (рекомендуется)
• mail.com
• email.com
• yandex.ru
• rambler.ru

<b>Формат:</b> Просто название домена
<b>Пример:</b> gmx.com

<b>Прокси:</b> ✅ Включены
"""
    else:
        text = """
📝 <b>Регистрация аккаунтов Fiverr</b>

<b>Шаг 1:</b> Выберите домен для покупки почты

<b>Доступные домены:</b>
• gmx.com (рекомендуется)
• mail.com
• email.com
• yandex.ru
• rambler.ru

<b>Формат:</b> Просто название домена
<b>Пример:</b> gmx.com

<b>Прокси:</b> ❌ Отключены - прямое подключение
"""
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    context.user_data['state'] = 'waiting_domain'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')
    
    if state == 'waiting_domain':
        # Проверяем, что домен валидный
        domain = text.strip().lower()
        valid_domains = ['gmx.com', 'mail.com', 'email.com', 'yandex.ru', 'rambler.ru', 'mail.ru', 'gmail.com', 'outlook.com', 'hotmail.com']
        
        if domain in valid_domains:
            context.user_data['selected_domain'] = domain
            context.user_data['state'] = 'waiting_count'
            await update.message.reply_text(
                f"""
✅ Выбран домен: <b>{domain}</b>

<b>Шаг 2:</b> Введите количество аккаунтов для регистрации (1-50)

<b>Формат:</b> Просто число
<b>Пример:</b> 5
""",
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                f"""
❌ Неверный домен: <b>{domain}</b>

<b>Доступные домены:</b>
• gmx.com (рекомендуется)
• mail.com
• email.com
• yandex.ru
• rambler.ru

<b>Формат:</b> Просто название домена
<b>Пример:</b> gmx.com
""",
                parse_mode=ParseMode.HTML
            )
    
    elif state == 'waiting_count':
        try:
            count = int(text)
            if 1 <= count <= 50:
                context.user_data['account_count'] = count
                
                # Проверяем настройку прокси
                use_proxy = context.user_data.get('use_proxy', True)
                
                if use_proxy:
                    context.user_data['state'] = 'waiting_proxies'
                    await update.message.reply_text(
                        f"""
✅ Будет зарегистрировано: <b>{count}</b> аккаунт(ов)

<b>Шаг 2:</b> Отправьте прокси (по одному на строку)

<b>Формат:</b>
<code>username:password@ip:port</code>

<b>Пример:</b>
<code>user123:pass456@192.168.1.1:8080</code>

Количество прокси: <b>{count}</b>
""",
                        parse_mode=ParseMode.HTML
                    )
                else:
                    # Прокси отключены, сразу запускаем регистрацию
                    context.user_data['state'] = None
                    await update.message.reply_text(
                        f"""
✅ Будет зарегистрировано: <b>{count}</b> аккаунт(ов)
❌ Прокси отключены - используем прямое подключение

🚀 Начинаем регистрацию...
""",
                        parse_mode=ParseMode.HTML
                    )
                    
                    # Запускаем регистрацию без прокси
                    task_id = str(uuid.uuid4())
                    selected_domain = context.user_data.get('selected_domain', 'gmx.com')
                    await db.create_task(
                        user_id=update.effective_user.id,
                        task_id=task_id,
                        total_accounts=count,
                        proxies=[]
                    )
                    
                    # Запускаем задачу в фоне
                    # Передаем только необходимые данные, а не весь context
                    asyncio.create_task(
                        run_registration_task_simple(update, task_id, count, [], use_proxy=False, selected_domain=selected_domain)
                    )
            else:
                await update.message.reply_text(
                    "❌ Количество должно быть от 1 до 50. Попробуйте снова:"
                )
        except ValueError:
            await update.message.reply_text(
                "❌ Пожалуйста, введите число. Попробуйте снова:"
            )
    
    elif state == 'waiting_proxies':
        proxies_text = text.strip().split('\n')
        account_count = context.user_data.get('account_count', 0)
        
        # Парсим прокси
        proxies = []
        invalid_proxies = []
        
        # Проверяем каждый прокси
        await update.message.reply_text("🔍 Проверяю прокси...")
        
        for i, proxy_str in enumerate(proxies_text):
            proxy_str = proxy_str.strip()
            if not proxy_str:
                continue
            
            proxy = ProxyConfig.from_string(proxy_str)
            if proxy:
                # Проверяем работоспособность прокси
                await update.message.reply_text(f"⏳ Проверяю прокси {i+1}/{len(proxies_text)}...")
                
                is_working = await ProxyManager.check_proxy(proxy)
                if is_working:
                    proxies.append(proxy)
                    await update.message.reply_text(f"✅ Прокси {i+1} рабочий!")
                else:
                    invalid_proxies.append(proxy_str)
                    await update.message.reply_text(f"❌ Прокси {i+1} не работает!")
            else:
                invalid_proxies.append(proxy_str)
                await update.message.reply_text(f"❌ Прокси {i+1} неверный формат!")
        
        if invalid_proxies:
            await update.message.reply_text(
                f"❌ Неверный формат прокси:\n" + "\n".join(invalid_proxies) +
                f"\n\nПопробуйте снова в формате: username:password@ip:port"
            )
            return
        
        if len(proxies) != account_count:
            await update.message.reply_text(
                f"❌ Количество прокси ({len(proxies)}) не совпадает с количеством аккаунтов ({account_count})\n\n"
                f"Отправьте {account_count} прокси."
            )
            return
        
        # Сохраняем прокси и запускаем регистрацию
        context.user_data['proxies'] = proxies
        context.user_data['state'] = None
        
        await start_registration(update, context)


async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запуск процесса регистрации"""
    user_id = update.effective_user.id
    account_count = context.user_data.get('account_count')
    proxies = context.user_data.get('proxies')
    
    # Создаем задачу в БД
    task_id = str(uuid.uuid4())
    proxies_str = [f"{p.username}:{p.password}@{p.host}:{p.port}" for p in proxies]
    
    await db.create_task(
        task_id=task_id,
        user_id=user_id,
        total_accounts=account_count,
        proxies=proxies_str
    )
    
    # Проверяем баланс
    async with EmailAPIService() as email_service:
        balance = await email_service.get_balance()
        
        if balance is None or balance < 0.002 * account_count:
            await update.message.reply_text(
                "❌ Недостаточно средств на балансе API для покупки почт"
            )
            await db.update_task_status(task_id, "failed")
            return
    
    # Отправляем подтверждение
    await update.message.reply_text(
        f"""
✅ <b>Задача создана!</b>

ID задачи: <code>{task_id}</code>
Количество аккаунтов: {account_count}
Прокси: {len(proxies)}

⏳ Начинаю регистрацию...
Это может занять несколько минут.
""",
        parse_mode=ParseMode.HTML
    )
    
    # Обновляем статус
    await db.update_task_status(task_id, "running")
    
    # Запускаем регистрацию в фоне
    # Получаем настройку прокси из контекста пользователя
    use_proxy = context.user_data.get('use_proxy', True)
    
    asyncio.create_task(
        run_registration_task_simple(update, task_id, account_count, proxies, use_proxy, 'gmx.com')
    )


async def run_registration_task_simple(
    update: Update,
    task_id: str,
    account_count: int,
    proxies: list,
    use_proxy: bool = True,
    selected_domain: str = 'gmx.com'
):
    """Упрощенная версия run_registration_task без context"""
    user_id = update.effective_user.id
    
    try:
        async with EmailAPIService() as email_service:
            # Запускаем регистрацию
            proxy_config = None
            if proxies and len(proxies) > 0:
                proxy_config = proxies[0]
            
            results = await register_accounts_batch(
                email_service=email_service,
                count=account_count,
                proxy=proxy_config,
                use_proxy=use_proxy,
                telegram_bot=update.effective_chat.get_bot(),
                chat_id=update.effective_chat.id,
                selected_domain=selected_domain
            )
            
            successful = 0
            failed = 0
            
            for i, result in enumerate(results):
                if isinstance(result, dict) and result.get('success'):
                    successful += 1
                    
                    await db.save_account(
                        email=result['email'],
                        password=result['password'],
                        user_id=user_id,
                        task_id=task_id,
                        cookies=result['cookies'],
                        proxy=result.get('proxy')
                    )
                    
                    cookies_text = ""
                    if 'cookies' in result:
                        for name, value in result['cookies'].items():
                            cookies_text += f"{name}={value}\n"
                    
                    cookies_file = io.BytesIO(cookies_text.encode('utf-8'))
                    cookies_file.name = f"cookies_{result['email']}.txt"
                    
                    account_details = f"""✅ <b>Аккаунт #{successful}</b>
📧 Email: <code>{result['email']}</code>
👤 Username: <code>{result.get('username', 'N/A')}</code>
🔑 Password: <code>{result['password']}</code>"""

                    if result.get('confirmation_code'):
                        account_details += f"\n🔐 Код подтверждения: <code>{result['confirmation_code']}</code>"
                    
                    account_details += "\n\n📁 Cookies файл прикреплен ниже."
                    
                    await update.effective_chat.send_document(
                        document=cookies_file,
                        caption=account_details,
                        parse_mode=ParseMode.HTML
                    )
                    
                    await db.add_task_result(
                        task_id=task_id,
                        email=result['email'],
                        success=True
                    )
                else:
                    failed += 1
                    error = result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
                    await db.add_task_result(
                        task_id=task_id,
                        email=f"account_{i+1}",
                        success=False,
                        error=error
                    )
            
            await db.update_task_status(task_id, "completed")
            
            summary_text = f"""
📊 <b>Регистрация завершена!</b>
ID задачи: <code>{task_id}</code>
✅ Успешно: {successful}
❌ Ошибок: {failed}
📋 Всего: {account_count}
Все cookies файлы отправлены выше.
"""
            await update.effective_chat.send_message(
                summary_text,
                parse_mode=ParseMode.HTML
            )
            
    except Exception as e:
        logger.error(f"Ошибка в run_registration_task_simple: {e}")
        await db.update_task_status(task_id, "failed")
        
        await update.effective_chat.send_message(
            f"❌ Произошла ошибка при регистрации:\n{str(e)}"
        )


async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /tasks"""
    user_id = update.effective_user.id
    
    tasks = await db.get_user_tasks(user_id, limit=10)
    
    if not tasks:
        await update.message.reply_text("📋 У вас пока нет задач")
        return
    
    response = "<b>📋 Ваши задачи:</b>\n\n"
    
    status_emoji = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌"
    }
    
    for task in tasks:
        task_id = task['task_id'][:8]
        status = task['status']
        total = task['total_accounts']
        completed = task['completed_accounts']
        failed = task['failed_accounts']
        
        response += f"{status_emoji.get(status, '❓')} <code>{task_id}</code>\n"
        response += f"Статус: {status}\n"
        response += f"Прогресс: {completed + failed}/{total}\n"
        response += f"Успешно: {completed} | Ошибок: {failed}\n\n"
    
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)


async def accounts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /accounts"""
    user_id = update.effective_user.id
    
    accounts = await db.get_user_accounts(user_id, limit=20)
    
    if not accounts:
        await update.message.reply_text("📧 У вас пока нет зарегистрированных аккаунтов")
        return
    
    response = f"<b>📧 Ваши аккаунты ({len(accounts)}):</b>\n\n"
    
    for i, account in enumerate(accounts, 1):
        email = account['email']
        created = account['created_at'].strftime('%Y-%m-%d %H:%M')
        
        response += f"{i}. <code>{email}</code>\n"
        response += f"   Создан: {created}\n\n"
        
        if len(response) > 3500:
            await update.message.reply_text(response, parse_mode=ParseMode.HTML)
            response = ""
    
    if response:
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} вызвал ошибку {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )

