from abc import ABCMeta, abstractmethod



class AbstractOutputterReadCB(metaclass=ABCMeta):
    @abstractmethod
    def __call__(self, x) -> None:
        pass


class EmptyOutputterReadCB(AbstractOutputterReadCB):
    def __call__(self, x) -> None:
        pass


class AbstractOutputter:
    def write(self, s) -> None:
        pass

    def handle_read(self):
        pass

    def register_read_callback(self, cb) -> None:
        pass




