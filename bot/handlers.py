"""
Обработчики команд Telegram бота
"""
import asyncio
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from utils.logger import logger
from services.database import db
from services.email_api import EmailAPIService
from services.proxy_manager import ProxyConfig, ProxyManager
from services.fiverr_registrator_selenium import FiverrRegistrator, register_accounts_batch
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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📖 <b>Подробная справка</b>

<b>1. Регистрация аккаунтов (/register)</b>
Команда запустит интерактивный процесс регистрации:
- Укажите количество аккаунтов
- Отправьте прокси (по одному на строку)
- Бот начнет регистрацию

<b>2. Формат прокси:</b>
<code>username:password@ip:port</code>

Пример:
<code>user123:pass456@192.168.1.1:8080</code>

<b>3. Проверка баланса (/balance)</b>
Показывает текущий баланс API для покупки почт

<b>4. Просмотр задач (/tasks)</b>
Список всех ваших задач на регистрацию с их статусами

<b>5. Просмотр аккаунтов (/accounts)</b>
Список всех успешно зарегистрированных аккаунтов

<b>❗ Важно:</b>
- Один прокси = один аккаунт
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
    
    text = """
🚀 <b>Начинаем регистрацию аккаунтов</b>

<b>Шаг 1:</b> Укажите количество аккаунтов для регистрации
Введите число от 1 до 50
"""
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    context.user_data['state'] = 'waiting_count'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')
    
    if state == 'waiting_count':
        try:
            count = int(text)
            if 1 <= count <= 50:
                context.user_data['account_count'] = count
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
        
        for proxy_str in proxies_text:
            proxy_str = proxy_str.strip()
            if not proxy_str:
                continue
            
            proxy = ProxyConfig.from_string(proxy_str)
            if proxy:
                proxies.append(proxy)
            else:
                invalid_proxies.append(proxy_str)
        
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
    asyncio.create_task(
        run_registration_task(update, task_id, account_count, proxies)
    )


async def run_registration_task(
    update: Update,
    task_id: str,
    account_count: int,
    proxies: list
):
    """Выполнение задачи регистрации"""
    user_id = update.effective_user.id
    
    try:
        async with EmailAPIService() as email_service:
            # Запускаем регистрацию
            results = await register_accounts_batch(
                email_service=email_service,
                proxies=proxies,
                accounts_per_proxy=1
            )
            
            # Обрабатываем результаты
            successful = 0
            failed = 0
            
            for i, result in enumerate(results):
                if isinstance(result, dict) and result.get('success'):
                    successful += 1
                    
                    # Сохраняем аккаунт в БД
                    await db.save_account(
                        email=result['email'],
                        password=result['password'],
                        user_id=user_id,
                        task_id=task_id,
                        cookies=result['cookies'],
                        proxy=result.get('proxy')
                    )
                    
                    # Отправляем cookies пользователю
                    cookies_file = result['cookies_file']
                    await update.effective_chat.send_document(
                        document=open(cookies_file, 'rb'),
                        caption=f"""
✅ <b>Аккаунт #{successful}</b>

Email: <code>{result['email']}</code>
Пароль: <code>{result['password']}</code>
""",
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
            
            # Обновляем статус задачи
            await db.update_task_status(task_id, "completed")
            
            # Отправляем итоговый отчет
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
        logger.error(f"Ошибка в run_registration_task: {e}")
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

