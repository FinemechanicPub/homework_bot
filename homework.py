"""Телеграм-бот для информирования об изменении статуса домашней работы."""

import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

from exceptions import (
    NoResponseError, BadResponseError, ServerError,
    BadFormatError, MissingDataError, UnknowStatus
)


SUCCESS = 'В Telegram отправлено сообщение: "{message}"'
FAILURE = 'Сбой в работе программы. {error}'
REQUEST_FAIL = (
    'Не удалось подключиться к серверу. '
    'Ошибка: {error}'
)
WRONG_STATUS_CODE = ('Сервер вернул неожиданный статус ответа: {code}.')
SERVER_FAIL = (
    'Сервер вернул сообщение "{name}" следующего содержания: "{text}". '
)
WRONG_RESPONSE_OBJECT = 'Вместо словаря от сервера получен объект {type_name}'
WRONG_HOMEWORKS_OBJECT = (
    'Вместо списка домашних работ получен объект {type_name}'
)
NO_HOMEWORKS_IN_RESPONSE = 'В ответе сервера не обнаружено ключа homeworks.'
WRONG_HOMEWORK_STATUS = 'Неизвестный статус домашней работы - "{status}"'
STATUS_CHANGED = 'Изменился статус проверки работы "{name}". {verdict}'
MISSING_VARIABLE = 'Не задана(ы) переменная(ые) среды: {names}'
ERROR_REPORT_FAIL = 'Ошибка при отправке сообщения об ошибке: {error}'
PROCESSING_COMPLETE = 'Обработка статуса домашних работ завершена успешно.'
NO_HOMEWORK_UPDATE = 'Обновлений не получено.'

formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] Log "%(name)s" function "%(funcName)s" '
    'line %(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
file_handler = logging.FileHandler(__file__ + '.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

load_dotenv()
PRACTICUM_TOKEN = TELEGRAM_TOKEN = TELEGRAM_CHAT_ID = None
VARIABLES = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')
for name in VARIABLES:
    globals()[name] = os.getenv(name)

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot: Bot, message: str) -> None:
    """Отправка сообщения в Telegram."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info(SUCCESS.format(message=message))


def get_api_answer(current_timestamp: int) -> dict:
    """Запрос данных у сервера."""
    request_data = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': current_timestamp}
    }
    try:
        response = requests.get(**request_data)
    except requests.RequestException as error:
        raise NoResponseError(REQUEST_FAIL.format(error=error), **request_data)
    if response.status_code != 200:
        raise BadResponseError(
            WRONG_STATUS_CODE.format(code=response.status_code), **request_data
        )
    json = response.json()
    for key in ('error', 'code'):
        if key in json:
            raise ServerError(
                SERVER_FAIL.format(name=key, text=json[key]), **request_data
            )
    return json


def check_response(response: dict) -> list:
    """Извлечение списка домашних работ из ответа сервера."""
    if not isinstance(response, dict):
        raise BadFormatError(
            WRONG_RESPONSE_OBJECT.format(type_name=type(response))
        )
    if 'homeworks' not in response:
        raise MissingDataError(NO_HOMEWORKS_IN_RESPONSE)
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise BadFormatError(
            WRONG_HOMEWORKS_OBJECT.format(type_name=type(homeworks))
        )
    return homeworks


def parse_status(homework: dict) -> str:
    """Составление сообщения о статусе домашней работы."""
    # Автоматические тесты ожидают проверку имени перед запрсом вердикта
    try:
        name = homework['homework_name']
        status = homework['status']
    except KeyError as error:
        raise MissingDataError(str(error).replace('KeyError: ', ''))
    if status not in VERDICTS:
        raise UnknowStatus(status)
    return STATUS_CHANGED.format(name=name, verdict=VERDICTS[status])


def check_tokens() -> bool:
    """Проверка наличия токенов доступа к сервисам."""
    missing = [name for name in VARIABLES if not globals().get(name)]
    if missing:
        logger.critical(MISSING_VARIABLE.format(names=', '.join(missing)))
    return not missing


def send_error(bot: Bot, message: str, error_cache: set):
    """Отправка сообщения об ошибке в Telegram."""
    try:
        if message not in error_cache:
            send_message(bot, message)
            error_cache.add(message)
    except Exception as error:
        logger.exception(ERROR_REPORT_FAIL.format(error=error))


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise RuntimeError('Запуск невозможен. Подробности в журнале ошибок.')
    error_cache = set()
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                send_message(bot, parse_status(homeworks[0]))
            else:
                logger.debug(NO_HOMEWORK_UPDATE)
            timestamp = response.get('current_date', timestamp)
        except (TelegramError, MissingDataError, BadFormatError) as error:
            logger.exception(FAILURE.format(error=error))
        except Exception as error:
            message = FAILURE.format(error=error)
            logger.exception(message)
            send_error(bot, message, error_cache)
        else:
            error_cache.clear()
            logger.info(PROCESSING_COMPLETE)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
