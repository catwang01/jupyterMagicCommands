import logging
NULL_LOGGER = logging.getLogger('foo')
NULL_LOGGER.addHandler(logging.NullHandler())  # read below for reason