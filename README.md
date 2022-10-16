# Телеграм-бот для работы с внешним сервисом

Предназначен для получения отчетов о статусе домашних работ.

## Установка

Создание и активация окружения
```bash
python -m venv venv
source venv/bin/activate
```
Установка зависимостей
```bash
pip install -r requirements.txt
```

## Использование

В файле .env или в переменных окружения необходимо указать данные для подключения к API Практикума и Telegram:
- PRACTICUM_TOKEN - токен доступа к API Практикума
- TELEGRAM_TOKEN - токен бота Telegram
- TELEGRAM_CHAT_ID - ID чата, в который будут присылаться сообщения 

Бот запускается командой
```bash
python homework.py
```

## Технологии

- [Python Telegram Bot](https://github.com/python-telegram-bot/python-telegram-bot)

## Разработчики

- [Александр Рубцов](https://github.com/FinemechanicPub)