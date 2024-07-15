from typing import IO, Optional
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem

class DummyFileSystem(IFileSystem):
    def exists(self, path: str) -> bool:
        pass

    def makedirs(self, path: str) -> None:
        pass

    def open(self, filename: str, mode: str, encoding: str) -> IO:
        pass

    def getcwd(self) -> str:
        pass

    def chdir(self, path: str) -> None:
        pass

    def remove(self, path: str) -> None:
        pass

    def is_dir(self, path: str) -> bool:
        pass

    def system(
        self,
        cmd: str,
        background: bool = False,
        interactive: bool = False,
        outFile: Optional[str] = None,
        outVar: Optional[str] = None,
        proc: Optional[str] = None,
    ) -> None:
        pass