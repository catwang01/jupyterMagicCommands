import atexit
from abc import ABCMeta, abstractmethod

from jupyterMagicCommands.utils.general import removeprefix


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


class NonInteractiveOutputter(AbstractOutputter):
    def write(self, s):
        print(removeprefix(s, "\x1b[?1h\x1b="), end="")


class FileOutputter(AbstractOutputter):
    def __init__(self, file_path: str, **kwargs) -> None:
        self.file_path = file_path
        self.file = open(file_path, "w", **kwargs)
        atexit.register(self.file.close)

    def write(self, s: str):
        self.file.write(s)
