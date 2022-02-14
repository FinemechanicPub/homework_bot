"""Исключения бота проверки состояния домашних работ."""


class ApiError(Exception):
    """Базовый класс для ошибок связи с сервером домашних работ."""

    MESSAGE = (
        '{msg} Параметры запроса: '
        'url={url}, headers={headers}, params={params}'
    )

    def __init__(self, msg, url, headers, params):
        super().__init__(self.MESSAGE.format(
            msg=msg, url=url, headers=headers, params=params
        ))


class NoResponseError(ApiError):
    """Не удалось получить ответ сервера."""
    pass


class BadResponseError(ApiError):
    """Сервер вернул код ошибки."""
    pass


class ServerError(ApiError):
    """Сервер вернул сведения об ошибке."""
    pass


class MissingDataError(KeyError):
    """Базовый класс для ошибок отсутствия данных в ответе сервера."""

    MESSAGE = 'В ответе сервера не найден необходимый компонент {key}'

    def __init__(self, key):
        super().__init__(self.MESSAGE.format(key=key))


class BadFormatError(TypeError):
    """Базовый класс для ошибок неправильного формата ответа сервера."""

    MESSAGE = 'Ответ сервера имеет неправильную структуру. {description}'

    def __init__(self, description) -> None:
        super().__init__(self.MESSAGE.format(description=description))


class UnknowStatus(Exception):
    """Получен неизвестный статус домашней работы"""

    MESSAGE = 'Неизвестный статус домашней работы - "{status}"'

    def __init__(self, status):
        super().__init__(self.MESSAGE.format(status=status))
