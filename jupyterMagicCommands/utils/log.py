import logging
from logging import DEBUG

NULL_LOGGER = logging.getLogger('__null__')
NULL_LOGGER.addHandler(logging.NullHandler())  # read below for reason

def getLogger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(DEBUG)

    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(filename)s - %(name)s - %(levelname)s - %(message)s")
    streamhandler.setFormatter(formatter)
    logger.addHandler(streamhandler)
    return logger