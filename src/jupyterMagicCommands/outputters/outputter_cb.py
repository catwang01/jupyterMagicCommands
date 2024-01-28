from abc import ABCMeta, abstractmethod


class AbstractOutputterReadCB(metaclass=ABCMeta):

    @abstractmethod
    def __call__(self, x) -> None:
        pass


class EmptyOutputterReadCB(AbstractOutputterReadCB):

    def __call__(self, x) -> None:
        pass