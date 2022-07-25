import logging
import sys
import time
from http import HTTPStatus
try:
    from simplejson.errors import JSONDecodeError
except ImportError:
    from json.decoder import JSONDecodeError


from constants import (
    ENDPOINT, HEADERS, HOMEWORK_STATUSES, PRACTICUM_TOKEN, RETRY_TIME,
    TELEGRAM_CHAT_ID, TELEGRAM_TOKEN,
)

from exceptions import (
    EmptyResponse, GetApiError, IncorrectApiAnswer, NoHomeworkInfo,
    SendMessageFailure, WrongGetApiStatus,
)

import requests

from telegram import Bot
from telegram.error import TelegramError


logger = logging.getLogger(__name__)


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        msg = f'Сообщение "{message}" отправлено в Telegram чат'
        logger.info(msg)
    except TelegramError as error:
        msg = f'Сбой при отправке сообщения: {error}'
        raise SendMessageFailure(msg)


def get_api_answer(current_timestamp):
    """Получение данных сервиса API Яндекс Практикум."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params,
        )
        if homework_statuses.status_code != HTTPStatus.OK:
            message = f'Статус код ответа на запрос к "{ENDPOINT}" равен'
            f'{homework_statuses.status_code}.'
            logger.error(message)
            raise WrongGetApiStatus(message)
    except Exception as error:
        message = f'Сбой в работе API сервиса: {error}'
        raise GetApiError(message)
    try:
        response = homework_statuses.json()
        return response
    except JSONDecodeError:
        jsn_message = 'Ошибка с JSON'
        logger.error(jsn_message)


def check_response(response):
    """Проверка ответа сервиса API на корректность."""
    if response is None:
        message = 'Нет данных в ответе сервиса API.'
        raise EmptyResponse(message)
    if not isinstance(response, dict):
        message = 'Получен некорректный тип данных от сервиса API.'
        raise TypeError(message)
    if 'homeworks' not in response or 'current_date' not in response:
        message = 'Получен некорректный ответ от сервиса API.'
        raise IncorrectApiAnswer(message)
    if not isinstance(response['homeworks'], list):
        message = 'В ответе сервиса API нет списка домашних работ.'
        raise TypeError(message)
    homeworks_list = response['homeworks']
    return homeworks_list


def parse_status(homework):
    """Возвращает информацию об изменении статуса домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if 'homework_name' not in homework:
        message = 'Не найдено имя домашней работы в ответе API.'
        logger.error(message)
        raise KeyError(message)
    if 'status' not in homework:
        message = 'Не найден статус домашней работы в ответе API.'
        logger.error(message)
        raise KeyError(message)
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if verdict is None:
        message = 'Недокументированный статус домашней работы в ответе API.'
        logger.error(message)
        raise KeyError(message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    env_variables_available = all(
        [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, ]
    )
    return env_variables_available


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Недоступна одна или несколько переменных окружения.')
        sys.exit('Работа программы завершена.')
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_message = None
    last_error = None
    while True:
        try:
            response = get_api_answer(current_timestamp=current_timestamp)
            homeworks_list = check_response(response=response)
            if homeworks_list:
                homework = homeworks_list[0]
            else:
                message = 'Не найдено информации о домашней работе.'
                logger.info(message)
                raise NoHomeworkInfo(message)
            status_str = parse_status(homework=homework)
            if status_str != last_message:
                send_message(bot=bot, message=status_str)
                last_message = status_str
            else:
                message = 'Статус домашней работы не изменился.'
                logger.debug(message)
            current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != last_error:
                send_message(bot=bot, message=message)
                last_error = message
        else:
            message = 'Программа отработала без ошибок.'
            logger.info(message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler(stream=sys.stderr)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)

    main()


