import logging
import os
import shutil
import tempfile
from typing import IO, Optional

import pexpect
import psutil
from IPython import get_ipython

from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.outputters import (AbstractOutputter,
                                             AbstractOutputterFactory)
from jupyterMagicCommands.utils.action_detector import ActionDetector
from jupyterMagicCommands.utils.log import NULL_LOGGER

logger = logging.getLogger(__name__)

class FileSystem(IFileSystem):
    def __init__(
        self,
        outputterFactory: AbstractOutputterFactory,
        logger: logging.Logger = NULL_LOGGER,
        shell = None
    ):
        self.logger = logger
        self.outputterFactory = outputterFactory
        self.shell = shell or get_ipython()
        self._actionDetector = ActionDetector(self.logger, self.shell)

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

    def _find_pid(self, cmd: str) -> Optional[int]:
        # we use the true pid
        processes = psutil.process_iter(attrs=["pid", "name", "cmdline"])
        for p in processes:
            command = " ".join(p.cmdline())
            self.logger.debug(f'The process {p} has the command {command}')
            # the correctness is built on the assumption that the template file saving the cell content is only run by this class
            if command and cmd == command:
                self.logger.info(f"Find a process: {p.info}")
                return p.pid
        return None

    def _system_background(
            self,
            actual_cmd: str,
            outFile: Optional[str] = None,
            outVar: Optional[str] = None,
            proc: Optional[str] = None,
            delay: int = -1,
        ) -> None:
        # for background script, we use the built-in `%%script` magic to help
        if outFile is None and outVar is None:
            outFile = "/tmp/out.log"
            print(f"WARNING: outFile is not set, the default output file is {outFile}")

        # the process output is exported to the variable with name random_variable_name
        random_variable_name = "outVar" + str(hash(outFile))
        proc = proc or random_variable_name
        self.shell.run_cell_magic("_script", f"bash --bg --outfile {outFile} --proc {proc} --wait-after {delay}", actual_cmd)
        pid = self._find_pid(actual_cmd)
        # if the true pic can't be obtained, use the parent pid
        if pid is not None:
            print(f"Run a subprocess with pid: {pid}. Output to '{outFile}'")
        else:
            self.logger.info(f'Not process with command {actual_cmd} is found. Use the the pid of the parent process')
            child = self.shell.user_ns[proc]
            pid = child.pid
            print(f"Run a subprocess. Its parent process's pid is {pid}. Output to '{outFile}'")
        self.shell.user_ns[proc] = pid

    def system(
        self,
        cmd: str,
        background: bool = False,
        interactive: bool = False,
        outFile: Optional[str] = None,
        outVar: Optional[str] = None,
        proc: Optional[str] = None,
        delay: int = -1,
    ) -> None:
        if outFile is not None and outVar is not None:
            raise Exception("outFile and outVar cannot be set at the same time")
        if interactive and (outFile is not None or outVar is not None):
            raise Exception(
                "interactive and outFile/outVar cannot be set at the same time"
            )
        encoding = "utf8"
        with tempfile.NamedTemporaryFile(
            encoding=encoding, mode="w", delete=False
        ) as fp:
            fp.write(cmd)
            # we know there is no spaces in fp.name so we don't quote it with ' or "
            actual_cmd = f"bash {fp.name}"
            self.logger.debug(f'Saved the content into {fp.name}, the actual command to run is {actual_cmd}')

        if background: 
            self._system_background(actual_cmd, outFile, outVar, proc, delay)
            return

        child = pexpect.spawn(actual_cmd)
        outputter = self.outputterFactory.create_outputter(interactive, outFile, outVar)

        outputter.register_read_callback(child.send)
        self._run_command(child, outputter)

    def _run_command(self, child, outputter: AbstractOutputter):
        prevMessage = ""
        i = 0
        while True:
            try:
                returncode = child.expect_list(
                    [pexpect.TIMEOUT, pexpect.EOF],
                    timeout=0.01,
                )  # fresh terminal per 0.2s
                message = child.before.decode()
                i = self._actionDetector.detect_action_by_chunk(message, i)
                outputter.write(message[len(prevMessage) :])
                outputter.handle_read()
                prevMessage = message
                if returncode != 0:
                    break
            except KeyboardInterrupt:
                child.sendintr()
            except Exception:
                break
