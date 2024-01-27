from abc import ABCMeta, abstractmethod

from jupyterMagicCommands.outputters.outputter_cb import AbstractOutputterReadCB

class AbstractOutputter(metaclass=ABCMeta):

    @abstractmethod
    def write(self, s: str) -> None:
        pass

    @abstractmethod
    def handle_read(self) -> None:
        pass

    @abstractmethod
    def register_read_callback(self, cb: AbstractOutputterReadCB) -> None:
        pass