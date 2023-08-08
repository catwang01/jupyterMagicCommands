import asyncio
import logging
import os
import subprocess
import tempfile
from typing import IO, Optional

import pexpect
from IPython import get_ipython

from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.outputters import (AbstractOutputter,
                                             AsyncInteractiveOutputter,
                                             FileOutputter,
                                             NonInteractiveOutputter)
from jupyterMagicCommands.utils.log import NULL_LOGGER

logger = logging.getLogger(__name__)

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

    def system(self, cmd: str, 
               background: bool=False, 
               interactive: bool=False,
               outFile: Optional[str]=None) -> None:

        async def run_command(child, outputter: AbstractOutputter):
            prevMessage = ""
            while True:
                try:
                    i = await child.expect_list(
                        [pexpect.TIMEOUT, pexpect.EOF],
                        timeout=0.02,
                        async_=True
                    ) # fresh terminal per 0.2s
                    message = child.before.decode()
                    outputter.write(message[len(prevMessage):])
                    prevMessage = message
                    if i != 0:
                        break
                except KeyboardInterrupt:
                    child.sendintr()

        encoding = 'utf8'
        with tempfile.NamedTemporaryFile(encoding=encoding, mode='w', delete=False) as fp:
            fp.write(cmd)
            actual_cmd_to_run = f"bash '{fp.name}'"
            logger.debug(actual_cmd_to_run)

        if background:
            if outFile is None: 
                outFile = '/tmp/out.log'
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
            return

        child = pexpect.spawn(actual_cmd_to_run)
        outputter: AbstractOutputter
        if interactive:
            outputter = AsyncInteractiveOutputter()
        else:
            if outFile is not None:
                outputter = FileOutputter(outFile)
            else:
                outputter = NonInteractiveOutputter()
        outputter.register_read_callback(child.sendline)
        gathered = asyncio.gather(outputter.on_read(), run_command(child, outputter))
        asyncio.ensure_future(gathered)