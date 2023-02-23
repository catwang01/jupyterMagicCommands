import os
from typing import IO
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem

class FileSystem(IFileSystem):

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def makedirs(self, path: str) -> None:
        os.makedirs(path)

    def open(self, filename, mode, encoding) -> IO:
        return open(filename, mode, encoding)

    def getcwd(self) -> str:
        return os.getcwd()

    def chdir(self, path:str) -> None:
        return os.chdir(path)

    def removedirs(self, path: str) -> None:
        return os.removedirs(path)

    def system(self, cmd: str) -> None:
        os.system(cmd)
