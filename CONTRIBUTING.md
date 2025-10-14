# Contributing to Fiverr Bot

Спасибо за интерес к проекту! Мы приветствуем любой вклад.

## 🤝 Как внести вклад

### Reporting Bugs (Сообщение об ошибках)

Если вы нашли ошибку:

1. Убедитесь, что ошибка еще не была сообщена в [Issues](../../issues)
2. Создайте новый Issue с подробным описанием:
   - Шаги для воспроизведения
   - Ожидаемое поведение
   - Фактическое поведение
   - Версия Python, ОС
   - Логи (если есть)

### Suggesting Features (Предложение функций)

Есть идея для улучшения?

1. Создайте Issue с тегом "enhancement"
2. Опишите:
   - Проблему, которую решает функция
   - Предлагаемое решение
   - Альтернативные варианты

### Pull Requests

1. Fork репозитория
2. Создайте ветку для вашей функции:
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. Внесите изменения
4. Убедитесь, что код соответствует стилю проекта
5. Закоммитьте изменения:
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
6. Push в ветку:
   ```bash
   git push origin feature/AmazingFeature
   ```
7. Откройте Pull Request

## 📝 Стандарты кодирования

### Python Style Guide

- Следуйте [PEP 8](https://pep8.org/)
- Используйте docstrings для функций и классов
- Максимальная длина строки: 100 символов
- Используйте type hints где возможно

### Примеры:

```python
async def register_account(
    email: str,
    proxy: Optional[ProxyConfig] = None
) -> Optional[Dict[str, Any]]:
    """
    Регистрация нового аккаунта
    
    Args:
        email: Email адрес для регистрации
        proxy: Прокси для использования
        
    Returns:
        Словарь с данными аккаунта или None
    """
    # Ваш код
    pass
```

### Commit Messages

Используйте понятные сообщения коммитов:

- ✨ `feat: Add new feature`
- 🐛 `fix: Fix bug in registration`
- 📝 `docs: Update README`
- 🎨 `style: Format code`
- ♻️ `refactor: Refactor email service`
- ⚡ `perf: Improve performance`
- ✅ `test: Add tests`

## 🧪 Тестирование

Перед отправкой PR:

1. Убедитесь, что бот запускается
2. Протестируйте основные функции
3. Проверьте логи на ошибки
4. Запустите тестовые скрипты (если есть)

## 📦 Добавление зависимостей

При добавлении новых библиотек:

1. Добавьте в `requirements.txt`
2. Укажите конкретную версию
3. Обновите `Dockerfile` если нужно
4. Документируйте использование в README

## 🐛 Debug режим

Для отладки установите в `.env`:

```env
LOG_LEVEL=DEBUG
BROWSER_HEADLESS=false
```

## 📞 Контакты

Вопросы? Создайте Issue или напишите в обсуждения.

Спасибо за вклад! 🎉

