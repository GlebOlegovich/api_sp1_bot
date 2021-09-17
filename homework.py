import logging
import os
import time
from http import HTTPStatus
from typing import Dict

import requests
import telegram
from dotenv import load_dotenv

import app_logger

# from pprint import pprint


load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YA_PRACTICUM_HW_URL = (
    'https://praktikum.yandex.ru/api/'
    'user_api/homework_statuses/'
)

STICKERS = {
    'понравилось': 'CAACAgIAAxkBAAEC6zthRGKOmkZuxSASJlwj'
                   's24h7cMh-QACNQADrWW8FPWlcVzFMOXgIAQ',

    'ошибки': 'CAACAgIAAxkBAAEC6lRhQ6i2KM00tMRK-c'
              '_5t3B-nm7xTAACeQgAAgi3GQLo6uffKEXZAAEgBA',

    'проверку': 'CAACAgIAAxkBAAEC60JhRGNgDpeRmgx3SWX-O_'
                'KsDPA_2QACTgADwDZPE5XvE_fE3wn3IAQ',

    'упал': 'CAACAgIAAxkBAAEC60xhRGkcD0O7P_Fu11'
            'UWeXOemidxMQACPgADspiaDv-4iTC3LFg0IAQ',
}

# проинициализируйте бота здесь,
# чтобы он был доступен в каждом нижеобъявленном методе,
# и не нужно было прокидывать его в каждый вызов
bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework: Dict) -> str:
    homework_name = homework['homework_name']
    if homework['status'] == 'rejected':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    elif homework['status'] == 'approved':
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    elif homework['status'] == 'reviewing':
        return (
            f'Работу "{homework["lesson_name"]} - {homework_name}"'
            f' взяли на проверку! ({homework["date_updated"]})'
        )
    else:
        message = 'Нам пришел json, со странным значением статуса : '
        message += f'{homework["status"]} в дз : {homework["homework_name"]} '
        raise ValueError(message)
    return (
        f'У вас проверили работу "{homework_name}" - {homework["lesson_name"]}'
        f'\nВремя: {homework["date_updated"]}!\n{verdict}'
    )


def get_homeworks(current_timestamp):
    homework_statuses = requests.get(
        YA_PRACTICUM_HW_URL,
        headers={'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'},
        params={'from_date': current_timestamp}
    )
    if homework_statuses.status_code != HTTPStatus.OK:
        raise ValueError(
            f'Сервер отвалился - {homework_statuses.status_code}'
            f', при переходе по {YA_PRACTICUM_HW_URL}'
        )
    else:
        return homework_statuses.json()


def send_message(message):
    for key, sticker in STICKERS.items():
        if message.find(key) != -1:
            bot.send_sticker(
                chat_id=CHAT_ID,
                sticker=sticker
            )
            break

    logger.info(f'Бот отпрвил сообщение: {message}')
    return bot.send_message(
        chat_id=CHAT_ID,
        text=message
    )


def main():
    #current_timestamp = int(time.time())  # Начальное значение timestamp
    current_timestamp = 1626455426
    logger.debug('Бот запущен!')

    while True:
        try:
            hw_statuses_json = (get_homeworks(current_timestamp))
            current_timestamp = hw_statuses_json['current_date']

            #  Если что то есть в этом списке...
            if hw_statuses_json['homeworks']:
                logger.info(
                    f'Пришли проверенные ДЗ: '
                    f'{len(hw_statuses_json["homeworks"])} шт.'
                )
                # pprint(hw_statuses_json)
                for homework in hw_statuses_json['homeworks']:
                    verdict = parse_homework_status(homework)
                    send_message(verdict)

            time.sleep(13 * 60)  # Опрашивать раз в пять минут

        except Exception as error:
            message = (
                'Бот упал (ну вообще - не упал, а просто ошибка) '
                f'с ошибкой: {error}'
            )
            logger.error(error)
            send_message(message)
            time.sleep(60)


if __name__ == '__main__':
    logger = app_logger.get_logger(__name__)

    # Костыль) я сделал логер отдельным файлом, а пайтесты ругались,
    # пока логера не было тут
    logging

    main()
