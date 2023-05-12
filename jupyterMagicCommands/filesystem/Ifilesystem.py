from typing import IO
from abc import abstractmethod

class IFileSystem:

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
    def removedirs(self, path: str) -> None:
        pass
     
    @abstractmethod
    def system(self, path: str) -> None:
        pass
        