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


    async def on_read(self) -> None:
        pass


class NonInteractiveOutputter(AbstractOutputter):

    def register_read_callback(self, cb) -> None:
        pass

    def write(self, s):
        print(s)

    def handle_read(self):
        pass