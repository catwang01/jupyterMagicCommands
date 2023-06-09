import logging
import os
import subprocess
import tempfile
from typing import IO, Optional

from IPython import get_ipython

from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.mixins.logmixin import LogMixin
from jupyterMagicCommands.utils.log import NULL_LOGGER


class FileSystem(IFileSystem):

    def __init__(self, logger: logging.Logger=NULL_LOGGER):
        self.logger = logger

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def makedirs(self, path: str) -> None:
        os.makedirs(path)

    def open(self, filename, mode, encoding) -> IO:
        return open(filename, mode, encoding=encoding)

    def getcwd(self) -> str:
        return os.getcwd()

    def chdir(self, path:str) -> None:
        return os.chdir(path)

    def removedirs(self, path: str) -> None:
        return os.removedirs(path)

    def system(self, cmd: str, background: bool=False, outFile: Optional[str]=None) -> None:
        encoding = 'utf8'
        with tempfile.NamedTemporaryFile(encoding=encoding, mode='w', delete=False) as fp:
            fp.write(cmd)
            fp.seek(0)
            actual_cmd_to_run = f"bash '{fp.name}'"
            if background:
                if outFile is None: outFile = 'out.log'
                print(f"WARNING: outFile is not set, the default output file is {outFile}")
                with open(outFile, 'w', encoding='utf8') as logFile:
                    stdout = stderr = logFile
                    process = subprocess.Popen(
                        actual_cmd_to_run,
                        stdout=stdout,
                        stderr=stderr,
                        shell=True
                    )
                print(f"Run subprocess with pid: {process.pid}. Output to '{outFile}'")
            else:
                get_ipython().system(actual_cmd_to_run)