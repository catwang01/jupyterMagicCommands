from typing import IO, Optional
from abc import abstractmethod, ABCMeta


class IFileSystem(metaclass=ABCMeta):
    @abstractmethod
    def exists(self, path: str) -> bool:
        pass

    @abstractmethod
    def makedirs(self, path: str) -> None:
        pass

    @abstractmethod
    def open(self, filename: str, mode: str, encoding: str) -> IO:
        pass

    @abstractmethod
    def getcwd(self) -> str:
        pass

    @abstractmethod
    def chdir(self, path: str) -> None:
        pass

    @abstractmethod
    def remove(self, path: str) -> None:
        pass

    @abstractmethod
    def is_dir(self, path: str) -> bool:
        pass

    @abstractmethod
    def system(
        self,
        cmd: str,
        background: bool = False,
        interactive: bool = False,
        outFile: Optional[str] = None,
        outVar: Optional[str] = None,
    ) -> None:
        pass
