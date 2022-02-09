"""Телеграм-бот для информирования об изменении статуса домашней работы."""

import logging
import os
import sys
import requests
import time

from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

error_cache = set()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
))
logger.addHandler(handler)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot: Bot, message: str) -> None:
    """Отправка сообщения в Telegram."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info('Отправлено сообщение в Telegram')


def get_api_answer(current_timestamp: int) -> dict:
    """Запрос данных у сервера."""
    response = requests.get(
        url=ENDPOINT,
        headers=HEADERS,
        params={'from_date': current_timestamp or int(time.time())}
    )
    if response.status_code != 200:  # response.ok не поддерживается тестами
        raise ConnectionError(f'Сервер вернул ошибку {response.status_code}')
    return response.json()


def check_response(response: dict) -> list:
    """Извлечение списка домашних работ из ответа сервера."""
    if not isinstance(response, dict):
        raise TypeError('сервер передал некорректный ответ')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('сервер передал некорректное описание домашних работ')
    return homeworks


def parse_status(homework: dict) -> str:
    """Составление сообщения о статусе домашней работы."""
    for field in ('homework_name', 'status'):
        if field not in homework:
            raise KeyError(f'ответ сервера не содержит поля {field}')
    name = homework['homework_name']
    status = homework['status']
    verdict = HOMEWORK_STATUSES.get(status)
    if not verdict:
        raise ValueError(f'неизвестный статус домашней работы - "{status}"')
    return f'Изменился статус проверки работы "{name}". {verdict}'


def check_tokens() -> bool:
    """Проверка наличия токенов доступа к сервисам."""
    return None not in [
        PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    ]


def report_error(error: Exception, bot: Bot):
    """Обработка ошибок."""
    if isinstance(error, TelegramError):
        logger.error(f'Ошибка при отправке сообщения. {error}')
        return
    message = f'Сбой в работе программы: {error}'
    logger.error(message)
    try:
        if message not in error_cache:
            error_cache.add(message)
            bot.send_message(message)
    except Exception as error:
        logger.error(f'Ошибка при отправке сообщения об ошибке. {error}')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical(
            'Не задана одна из переменных среды'
            '(PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)'
        )
        return
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = None
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logger.debug('Обновлений не получено')
            for homework in homeworks:
                send_message(bot, parse_status(homework))
            current_timestamp = response.get('current_date')
        except Exception as error:
            report_error(error, bot)
        else:
            error_cache.clear()
            logger.info('Статус домашних работ проверен')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
