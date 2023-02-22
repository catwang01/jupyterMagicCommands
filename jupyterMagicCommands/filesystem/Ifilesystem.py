from typing import IO
from abc import abstractmethod
import os

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
     
        