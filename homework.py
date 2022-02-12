"""Телеграм-бот для информирования об изменении статуса домашней работы."""

import logging
import os
import sys
import requests
import time

from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError
from json.decoder import JSONDecodeError

SUCCESS = 'В Telegram отправлено сообщение: "{message}"'
FAILURE = 'Сбой в работе программы. {error_text}'
REQUEST_FAIL = (
    'Не удалось подключиться к серверу. '
    'Параметры запроса: url={url}, headers={headers}, params={params}.'
)
WRONG_STATUS_CODE = (
    'Сервер вернул неожиданный статус ответа: {status_code}. '
    'Параметры запроса: url={url}, headers={headers}, params={params}.'
)
WRONG_JSON = (
    'Ответ сервера не является корректным json-объектом. '
    'Параметры запроса: url={url}, headers={headers}, params={params}. '
    'Текст ответа: {text}'
)
WRONG_RESPONSE_OBJECT = 'Вместо словаря от сервера получен объект {type_name}'
WRONG_HOMEWORKS_OBJECT = (
    'Вместо списка домашних работ получен объект {type_name}'
)
WRONG_HOMEWORK_STATUS = 'Неизвестный статус домашней работы - "{status}"'
STATUS_CHANGED = 'Изменился статус проверки работы "{name}". {verdict}'
MISSING_VARIABLE = 'Не задана переменная среды {name}'
TELEGRAM_ERROR = 'Ошибка при отправке сообщения в Telegram'
ERROR_REPORT_FAIL = 'Ошибка при отправке сообщения об ошибке'
CHECK_COMPLETE = 'Статус домашних работ проверен'
NO_HOMEWORKS = 'Обновлений не получено'

error_cache = set()
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] function "%(funcName)s" '
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

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

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
    try:
        request_data = {
            'url': ENDPOINT,
            'headers': HEADERS,
            'params': {'from_date': current_timestamp}
        }
        response = requests.get(**request_data)
        if response.status_code != 200:
            raise ValueError(WRONG_STATUS_CODE.format(
                status_code=response.status_code, **request_data
            ))
        return response.json()
    except JSONDecodeError:
        raise ValueError(WRONG_JSON.format(text=response.text, **request_data))
    except requests.RequestException:
        raise ConnectionError(REQUEST_FAIL.format(**request_data))


def check_response(response: dict) -> list:
    """Извлечение списка домашних работ из ответа сервера."""
    if not isinstance(response, dict):
        raise TypeError(WRONG_RESPONSE_OBJECT.format(type_name=type(response)))
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(
            WRONG_HOMEWORKS_OBJECT.format(type_name=type(homeworks))
        )
    return homeworks


def parse_status(homework: dict) -> str:
    """Составление сообщения о статусе домашней работы."""
    # Автоматические тесты ожидают проверку имени перед запрсом вердикта
    name = homework['homework_name']
    status = homework['status']
    if status not in VERDICTS:
        raise ValueError(WRONG_HOMEWORK_STATUS.format(status=status))
    return STATUS_CHANGED.format(name=name, verdict=VERDICTS[status])


def check_tokens() -> bool:
    """Проверка наличия токенов доступа к сервисам."""
    result = True
    for var_name in ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']:
        # Проверяется считывание переменных среды в константы
        # Наличие констант в словаре globals() предполагается
        if not globals()[var_name]:
            logger.critical(MISSING_VARIABLE.format(name=var_name))
            result = False
    return result


def log_error(message: str):
    """Запись сообщения об ошибке в лог."""
    logger.exception(message)


def send_error(bot: Bot, message: str):
    """Отправка сообщения об ошибке в Telegram."""
    try:
        if message not in error_cache:
            send_message(bot, message)
            error_cache.add(message)
    except Exception:
        log_error(ERROR_REPORT_FAIL)


def report_error(bot: Bot, error: Exception):
    """Обработка ошибок."""
    message = FAILURE.format(error_text=error)
    log_error(message)
    if not isinstance(error, TelegramError):
        send_error(bot, message)


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(1)
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                send_message(bot, parse_status(homeworks[0]))
            else:
                logger.debug(NO_HOMEWORKS)
            current_timestamp = response.get('current_date', current_timestamp)
        except Exception as error:
            report_error(bot, error)
        else:
            error_cache.clear()
            logger.info(CHECK_COMPLETE)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
