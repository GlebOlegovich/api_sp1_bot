import logging
from logging.handlers import RotatingFileHandler

_log_format = (
    "%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s)."
    "%(funcName)s(%(lineno)d) - %(message)s"
)


def get_file_handler():
    file_handler = RotatingFileHandler(
        'my_logger.log',
        maxBytes=10000,
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_log_format))
    return file_handler


# В ТЗ говорится про StreamHandler(), им стримить в терминал можно итп,
# но еще нужно стримить errors в ТГ, как я понял -
# это надо сделать StreamHandler()ом, но я хз как)
# Поэтому я пока что сделал просто
# вызов функции отправки сообщения, мб можешь подсказать,
# как мне сделать это через стрим?
def get_stream_handler():
    stream_handler = logging.StreamHandler()
    # Сделал стриминг с дебага,  потому что на heroku.com нет возможности
    # просматривать файл .log (его там вообще нет, видимо, не дает создавать)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(_log_format))
    return stream_handler


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_file_handler())
    logger.addHandler(get_stream_handler())
    return logger
