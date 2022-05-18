class GetApiError(Exception):
    """Ошибка доступа к сервису API ENDPOINT."""
    pass


class IncorrectApiAnswer(Exception):
    """Получен некорректный ответ сервиса API ENDPOINT."""
    pass


class SendMessageFailure(Exception):
    """Сбой при отправке сообщения в Telegram чат."""
    pass


class NoHomeworkInfo(Exception):
    """Не найдено информации о домашней работе."""
    pass


class WrongGetApiStatus(Exception):
    """Статус код ответа не равен 200"""
    pass


class EmptyResponse(Exception):
    """Отсутствуют данные в ответе от сервера."""
    pass
