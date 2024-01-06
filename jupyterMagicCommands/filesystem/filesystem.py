import logging
import os
import shutil
import tempfile
from typing import IO, Optional

import pexpect

from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.outputters import (AbstractOutputter,
                                             BasicInteractiveOutputter,
                                             FileOutputter,
                                             InteractiveOutputter)
from jupyterMagicCommands.utils.log import NULL_LOGGER

logger = logging.getLogger(__name__)

class FileSystem(IFileSystem):
    def __init__(self, logger: logging.Logger = NULL_LOGGER):
        self.logger = logger

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def makedirs(self, path: str) -> None:
        os.makedirs(path)

    def open(self, filename, mode, encoding) -> IO:
        return open(filename, mode, encoding=encoding)

    def getcwd(self) -> str:
        return os.getcwd()

    def chdir(self, path: str) -> None:
        os.chdir(path)

    def is_dir(self, path: str) -> bool:
        return os.path.isdir(path)

    def remove(self, path: str) -> None:
        if self.exists(path):
            if self.is_dir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        else:
            raise Exception(f"Path '{path}' does not exist")

    def system(
        self,
        cmd: str,
        background: bool = False,
        interactive: bool = False,
        outFile: Optional[str] = None,
    ) -> None:
        encoding = "utf8"
        with tempfile.NamedTemporaryFile(
            encoding=encoding, mode="w", delete=False
        ) as fp:
            fp.write(cmd)
            actual_cmd_to_run = f"bash '{fp.name}'"
            logger.debug(actual_cmd_to_run)

        if background and outFile is None:
            outFile = "/tmp/out.log"
            print(f"WARNING: outFile is not set, the default output file is {outFile}")
        child = pexpect.spawn(actual_cmd_to_run)
        outputter: AbstractOutputter
        if interactive:
            outputter = InteractiveOutputter()
        else:
            if outFile is not None:
                outputter = FileOutputter(outFile)
            else:
                outputter = BasicInteractiveOutputter()

        outputter.register_read_callback(child.send)
        self._run_command(child, outputter)
        if background:
            print(f"Run subprocess with pid: {child.pid}. Output to '{outFile}'")

    def _run_command(self, child, outputter: AbstractOutputter):
        prevMessage = ""
        while True:
            try:
                i = child.expect_list(
                    [pexpect.TIMEOUT, pexpect.EOF],
                    timeout=0.01,
                )  # fresh terminal per 0.2s
                message = child.before.decode()
                outputter.write(message[len(prevMessage) :])
                outputter.handle_read()
                prevMessage = message
                if i != 0:
                    break
            except KeyboardInterrupt:
                child.sendintr()
            except Exception:
                break
