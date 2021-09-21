import logging
import os
import time
from http import HTTPStatus
from typing import Dict

import requests
import telegram
from dotenv import load_dotenv

import app_logger


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


bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework: Dict) -> str:
    homework_name = homework['homework_name']
    status = homework['status']

    if status == 'rejected':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    elif status == 'approved':
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    elif status == 'reviewing':
        return (
            f'Работу "{homework["lesson_name"]} - {homework_name}"'
            f' взяли на проверку! ({homework["date_updated"]})'
        )
    else:
        message = 'Нам пришел json, со странным значением статуса : '
        message += f'{homework["status"]} в дз : {homework["homework_name"]}'
        logger.warning(message)
        raise ValueError(message)
    return (
        f'У вас проверили работу "{homework_name}" - {homework["lesson_name"]}'
        f'\nВремя: {homework["date_updated"]}!\n{verdict}'
    )


def get_homeworks(current_timestamp):
    try:
        homework_statuses = requests.get(
            YA_PRACTICUM_HW_URL,
            headers={'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'},
            params={'from_date': current_timestamp}
        )
    # На случай, если нет подключения к интернету / неверная ссылка /
    # Что то поломалось на серверах API и меня редиректит часто / таймаут
    except requests.exceptions.RequestException as eror:
        message = f'API недоступно - {eror}'
        logger.critical(message)
        raise Exception(message)

    # Соит ли оставить эту проверку? или трай выше это выполняет итак?
    # Как я понял RequestException учитывает и то, что может вернуться не 200
    # код. Тогда это бесполезная проверка... Но! Вроде бы 302 не попадает
    # в RequestException - тогда стоит оставить...
    if homework_statuses.status_code != HTTPStatus.OK:
        message = 'Сервер отвалился (код ответа страницы) - '
        message += f'{homework_statuses.status_code}, при переходе по'
        message += f'{YA_PRACTICUM_HW_URL}'
        logger.critical(message)
        raise ValueError(message)
    else:
        return homework_statuses.json()


def send_message(message):
    try:
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
    except Exception as error:
        message = f'Какие то проблемы с оптравкой msg - {error}'
        logger.critical(message)
        raise Exception(message)


def check_json_values(input_json: Dict):
    out = True
    if not input_json.get('current_date', False):
        out = False
        raise ValueError('"current_date" - None')
    if input_json['homeworks']:
        if not input_json.get('homeworks', False):
            out = False
            raise ValueError('"homeworks" - None')
        expected_hw = [
            'homework_name', 'status', 'lesson_name',
            'reviewer_comment', 'date_updated'
        ]
        for i in expected_hw:
            if not input_json['homeworks'][0].get(i, False):
                out = False
                raise ValueError(f'["homeworks"][0]["{i}"] - None')
    return out


def check_json(input_json: Dict):
    '''Проверяем JSON от API'''
    try:
        input_json['current_date']
        input_json['homeworks']
        if input_json['homeworks']:
            input_json['homeworks'][0]['homework_name'],
            input_json['homeworks'][0]['status'],
            input_json['homeworks'][0]['lesson_name'],
            input_json['homeworks'][0]['reviewer_comment'],
            input_json['homeworks'][0]['date_updated']
        return check_json_values(input_json)
    except Exception as error:
        message = f'В JSON ответе некорректный ключ/неверное значение: {error}'
        logger.error(message)
        raise KeyError(message)


def main():
    current_timestamp = int(time.time())
    logger.debug('Бот запущен!')
    send_message('Бот запущен!')

    while True:
        try:
            hw_statuses_json = get_homeworks(current_timestamp)
            if check_json(hw_statuses_json):
                if hw_statuses_json['homeworks']:
                    logger.info(
                        f'Пришли проверенные ДЗ: '
                        f'{len(hw_statuses_json["homeworks"])} шт.'
                    )
                    for homework in reversed(hw_statuses_json['homeworks']):
                        verdict = parse_homework_status(homework)
                        send_message(verdict)
                current_timestamp = hw_statuses_json['current_date']

            time.sleep(13 * 60)

        except Exception as error:
            # Если отправка сообщений работает - получим сообщение с ошибкой
            message = (
                'Бот упал (ну вообще - не упал, а просто ошибка) '
                f'с ошибкой: {error}'
            )
            send_message(message)
            time.sleep(5 * 60)


if __name__ == '__main__':
    logger = app_logger.get_logger(__name__)

    # Костыль) я сделал логер отдельным файлом, а пайтесты ругались,
    # пока логера не было тут
    logging

    main()
