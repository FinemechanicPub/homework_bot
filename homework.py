"""Телеграм-бот для информирования об изменении статуса домашней работы."""

import os
import requests
import time

from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'http://127.0.0.1'#'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

processed_homeworks = set()


def send_message(bot: Bot, message: str) -> None:
    """Отправка сообщения в Telegram."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp: int) -> dict:
    """Запрос данных у сервера."""
    timestamp = current_timestamp #or int(time.time())
    params = {'from_date': timestamp}
    return requests.get(
        url=ENDPOINT,
        headers=HEADERS,
        params=params
    ).json()


def check_response(response: dict) -> list:
    """Извлечение списка домашних работ из ответа сервера."""
    #  if 'homeworks' not in response - выбросить исключение
    return response['homeworks']


def parse_status(homework: dict) -> str:
    """Составление сообщения о статусе домашней работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка наличия токенов доступа к сервисам."""
    return None not in [
        PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    ]


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        return
    #...

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0

    #...

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                send_message(bot, parse_status(homework))
                break
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            #...
            time.sleep(RETRY_TIME)
        else:
            pass
            #...


if __name__ == '__main__':
    main()
