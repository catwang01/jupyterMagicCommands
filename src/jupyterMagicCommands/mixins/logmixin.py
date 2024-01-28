import logging

# This class could be imported from a utility module
class LogMixin(object):

    @property
    def logger(self):
        name = '.'.join([__name__, self.__class__.__name__])
        return logging.getLogger(name)
