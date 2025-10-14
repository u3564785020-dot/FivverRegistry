"""
Модуль для работы с MongoDB
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from utils.logger import logger
from config import MONGODB_URI, MONGODB_DATABASE


class Database:
    """Класс для работы с MongoDB"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """Подключение к MongoDB"""
        try:
            self.client = AsyncIOMotorClient(MONGODB_URI)
            self.db = self.client[MONGODB_DATABASE]
            
            # Проверяем соединение
            await self.client.admin.command('ping')
            logger.info(f"Успешное подключение к MongoDB: {MONGODB_DATABASE}")
            
            # Создаем индексы
            await self._create_indexes()
        except Exception as e:
            logger.error(f"Ошибка подключения к MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Отключение от MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Отключение от MongoDB")
    
    async def _create_indexes(self):
        """Создание индексов для коллекций"""
        try:
            # Индексы для коллекции users
            await self.db.users.create_index("user_id", unique=True)
            await self.db.users.create_index("created_at")
            
            # Индексы для коллекции tasks
            await self.db.tasks.create_index("task_id", unique=True)
            await self.db.tasks.create_index("user_id")
            await self.db.tasks.create_index("status")
            await self.db.tasks.create_index("created_at")
            
            # Индексы для коллекции accounts
            await self.db.accounts.create_index("email", unique=True)
            await self.db.accounts.create_index("user_id")
            await self.db.accounts.create_index("created_at")
            
            logger.info("Индексы созданы успешно")
        except Exception as e:
            logger.error(f"Ошибка создания индексов: {e}")
    
    # === Работа с пользователями ===
    
    async def add_user(self, user_id: int, username: str = None) -> bool:
        """
        Добавление пользователя
        
        Args:
            user_id: ID пользователя Telegram
            username: Username пользователя
            
        Returns:
            True если успешно, False иначе
        """
        try:
            await self.db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "username": username,
                        "updated_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow(),
                        "total_accounts": 0,
                        "is_active": True
                    }
                },
                upsert=True
            )
            logger.info(f"Пользователь {user_id} добавлен/обновлен")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных пользователя"""
        try:
            return await self.db.users.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None
    
    async def is_user_active(self, user_id: int) -> bool:
        """Проверка активности пользователя"""
        user = await self.get_user(user_id)
        return user.get("is_active", False) if user else False
    
    # === Работа с задачами ===
    
    async def create_task(
        self,
        task_id: str,
        user_id: int,
        total_accounts: int,
        proxies: List[str]
    ) -> bool:
        """
        Создание задачи на регистрацию аккаунтов
        
        Args:
            task_id: Уникальный ID задачи
            user_id: ID пользователя
            total_accounts: Количество аккаунтов для регистрации
            proxies: Список прокси
            
        Returns:
            True если успешно, False иначе
        """
        try:
            task = {
                "task_id": task_id,
                "user_id": user_id,
                "total_accounts": total_accounts,
                "completed_accounts": 0,
                "failed_accounts": 0,
                "proxies": proxies,
                "status": "pending",  # pending, running, completed, failed
                "created_at": datetime.utcnow(),
                "started_at": None,
                "completed_at": None,
                "results": []
            }
            
            await self.db.tasks.insert_one(task)
            logger.info(f"Задача {task_id} создана для пользователя {user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания задачи: {e}")
            return False
    
    async def update_task_status(self, task_id: str, status: str) -> bool:
        """Обновление статуса задачи"""
        try:
            update_data = {"status": status}
            
            if status == "running":
                update_data["started_at"] = datetime.utcnow()
            elif status in ["completed", "failed"]:
                update_data["completed_at"] = datetime.utcnow()
            
            await self.db.tasks.update_one(
                {"task_id": task_id},
                {"$set": update_data}
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления статуса задачи: {e}")
            return False
    
    async def add_task_result(
        self,
        task_id: str,
        email: str,
        success: bool,
        error: Optional[str] = None
    ) -> bool:
        """Добавление результата регистрации к задаче"""
        try:
            result = {
                "email": email,
                "success": success,
                "error": error,
                "timestamp": datetime.utcnow()
            }
            
            update_field = "completed_accounts" if success else "failed_accounts"
            
            await self.db.tasks.update_one(
                {"task_id": task_id},
                {
                    "$push": {"results": result},
                    "$inc": {update_field: 1}
                }
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления результата: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Получение данных задачи"""
        try:
            return await self.db.tasks.find_one({"task_id": task_id})
        except Exception as e:
            logger.error(f"Ошибка получения задачи: {e}")
            return None
    
    async def get_user_tasks(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение задач пользователя"""
        try:
            cursor = self.db.tasks.find(
                {"user_id": user_id}
            ).sort("created_at", DESCENDING).limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Ошибка получения задач пользователя: {e}")
            return []
    
    # === Работа с аккаунтами ===
    
    async def save_account(
        self,
        email: str,
        password: str,
        user_id: int,
        task_id: str,
        cookies: Dict[str, Any],
        proxy: Optional[str] = None
    ) -> bool:
        """
        Сохранение данных зарегистрированного аккаунта
        
        Args:
            email: Email аккаунта
            password: Пароль аккаунта
            user_id: ID пользователя
            task_id: ID задачи
            cookies: Cookies браузера
            proxy: Использованный прокси
            
        Returns:
            True если успешно, False иначе
        """
        try:
            account = {
                "email": email,
                "password": password,
                "user_id": user_id,
                "task_id": task_id,
                "cookies": cookies,
                "proxy": proxy,
                "created_at": datetime.utcnow(),
                "is_active": True
            }
            
            await self.db.accounts.insert_one(account)
            
            # Обновляем счетчик аккаунтов пользователя
            await self.db.users.update_one(
                {"user_id": user_id},
                {"$inc": {"total_accounts": 1}}
            )
            
            logger.info(f"Аккаунт {email} сохранен для пользователя {user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения аккаунта: {e}")
            return False
    
    async def get_user_accounts(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Получение аккаунтов пользователя"""
        try:
            cursor = self.db.accounts.find(
                {"user_id": user_id}
            ).sort("created_at", DESCENDING).limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Ошибка получения аккаунтов: {e}")
            return []
    
    async def get_account_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Получение аккаунта по email"""
        try:
            return await self.db.accounts.find_one({"email": email})
        except Exception as e:
            logger.error(f"Ошибка получения аккаунта: {e}")
            return None


# Глобальный экземпляр базы данных
db = Database()

