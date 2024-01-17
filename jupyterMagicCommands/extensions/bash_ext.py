import argparse
import os
import tempfile
import time
from dataclasses import dataclass
from logging import ERROR, Logger
from operator import itemgetter
from typing import Optional

import pexpect
from IPython import get_ipython
from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.display import display

from jupyterMagicCommands.extensions.constants import (
    EMPTY_CONTAINER_NAME,
    JUPYTER_MAGIC_COMMAND_BASH_CURRENT_CONTAINER,
)

# The class MUST call this class decorator at creation time
from jupyterMagicCommands.filesystem.filesystem_factory import FileSystemFactory
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.utils.functools import suppress
from jupyterMagicCommands.utils.log import NULL_LOGGER, getLogger
from jupyterMagicCommands.utils.parser import parse_logLevel

global_logger = getLogger(__name__)

template = """
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@4.5.0/css/xterm.css" />
    <script src="https://cdn.jsdelivr.net/npm/xterm@4.5.0/lib/xterm.js"></script>
    <div>
    <div id="%(termName)s"></div>
    <script>
        // create an instance of terminal and attach it to window.
        var %(termName)s = new Terminal(
            {
                rows: %(rows)s
            }
        );
        window.%(termName)s.open(document.getElementById('%(termName)s'));
    </script>
    </div>
"""


class NotValidBackend(Exception):
    pass


@dataclass
class BashArgsNS:
    init: bool = False
    cwd: str = "."
    create: bool = False
    init: bool = False
    container: Optional[str] = None
    verbose: bool = False
    backend: str = "plain"
    logLevel: int = ERROR
    height: int = 10
    background: bool = False
    outFile: Optional[str] = None
    outVar: Optional[str] = None
    interactive: bool = False


def initTerminal(initialOptions):
    termName = f"term_{time.strftime('%Y_%m_%d_%H_%M_%S')}"
    display(
        {
            "text/html": template
            % ({"termName": termName, "rows": initialOptions["rows"]})
        },
        raw=True,
    )
    displayHandler = display({"text/html": "<div></div>"}, raw=True, display_id=True)
    return termName, displayHandler


def sendToTerminal(termName, displayHandler, message, prevMessage=None):
    currentMessage = message
    if prevMessage is not None:
        currentMessage = message[len(prevMessage) :]
    unicodeArray = [ord(ch) for ch in currentMessage]
    template = f"""
<script>
    // window.{termName}.clear();
    window.{termName}.write({unicodeArray});
</script>
"""
    displayHandler.update({"text/html": template}, raw=True)


def plainExecuteCommand(command: str, args: BashArgsNS, **kwargs):
    logger: Logger = kwargs.get("logger", NULL_LOGGER)

    verbose, background, interactive, outFile, outVar = itemgetter(
        "verbose", "background", "interactive", "outFile", "outVar"
    )(vars(args))
    logger.debug("### Parameters starts ###")
    logger.debug(f"command: '{command}'")
    logger.debug(f"verbose: '{verbose}'")
    logger.debug(f"kwargs: '{kwargs}'")
    logger.debug("### Parameters ends ###")
    if verbose:
        print(command)
    if kwargs.get("fs", None) is not None:
        kwargs["fs"].system(
            command,
            background=background,
            interactive=interactive,
            outFile=outFile,
            outVar=outVar,
        )
    else:
        raise Exception("FileSystem is not initliazed for a container!")


def xtermExecuteCommand(command: str, args: BashArgsNS, **kwargs):
    logger = kwargs.get("logger", NULL_LOGGER)
    verbose, height = itemgetter("verbose", "height")(vars(args))
    if verbose:
        print(command)
    encoding = "utf8"
    with tempfile.NamedTemporaryFile(encoding=encoding, mode="w") as fp:
        fp.write(command)
        fp.seek(0)
        cmd = f"bash '{fp.name}'"
        logger.debug(cmd)
        child = pexpect.spawn(cmd)
        initialOptions = {"rows": height}
        termName, displayHandler = initTerminal(initialOptions)
        prevMessage = ""
        while True:
            try:
                i = child.expect_list(
                    [pexpect.TIMEOUT, pexpect.EOF], timeout=0.2
                )  # fresh terminal per 0.2s
                message = child.before.decode()
                sendToTerminal(termName, displayHandler, message, prevMessage)
                prevMessage = message
                if i != 0:
                    break
            except KeyboardInterrupt:
                child.sendintr()


def executeCmd(command: str, args: BashArgsNS, **kwargs):
    backend = args.backend
    if backend == "plain":
        plainExecuteCommand(command, args, **kwargs)
    elif backend == "xterm":
        if kwargs.get("container", None) is not None:
            raise Exception(
                f"Backend {backend} doesn't suppor docker running in a container"
            )
        xtermExecuteCommand(command, args, **kwargs)
    else:
        raise NotValidBackend(f"Not a valid backend {backend}")


def preprocessCommand(command: str, args: BashArgsNS) -> str:
    """
    Currently no preprocess is needed
    """
    return command


def get_args(line: str) -> BashArgsNS:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--d",
        "--cwd",
        dest="cwd",
        type=str,
        default=".",
        help="Working directory",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        default=False,
        help="Create the working directory if not existing. Do nothing if the directory exists",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        default=False,
        help="Force create the working directory. If it exists, remove it and create an empty one. if not, create an empty one. It can't be used without --create",
    )
    parser.add_argument(
        "-c",
        "--container",
        help="docker container name or id, if this is specified, the command would run in the specified container",
        nargs="?",
        const=os.environ.get(
            JUPYTER_MAGIC_COMMAND_BASH_CURRENT_CONTAINER, EMPTY_CONTAINER_NAME
        ),
    )
    parser.add_argument("-v", "--verbose", action="store_true", default=False)
    parser.add_argument(
        "-b", "--backend", type=str, choices=["plain", "xterm"], default="plain"
    )
    parser.add_argument("--logLevel", type=parse_logLevel, default="ERROR")
    parser.add_argument("--height", type=int, default=10)
    mg = parser.add_mutually_exclusive_group()
    mg.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        default=False,
        help="Execute the command interactively",
    )
    mg.add_argument(
        "--bg", "--background", dest="background", action="store_true", default=False
    )
    outputMg = parser.add_mutually_exclusive_group()
    outputMg.add_argument(
        "--outfile", "--outFile", dest="outFile", type=str, default=None
    )
    outputMg.add_argument(
        "--outvar",
        "--outVar",
        type=str,
        const="_",
        dest="outVar",
        nargs="?",
        default=None,
        help="save output into a variable",
    )
    line = line.strip("\n").strip(" ").lstrip("%%bash")
    if line:
        args = parser.parse_args(line.split(" "), namespace=BashArgsNS())
    else:
        args = parser.parse_args([], namespace=BashArgsNS())
    if args.container == EMPTY_CONTAINER_NAME:
        global_logger.error(
            "Trying to use an existing docker but no previously used docker container exists. Use `bash -c <container>` first"
        )
        exit(-1)
    if args.init and not args.create:
        global_logger.error("--init can't be used without --create!")
        exit(-1)
    return args


class BashExtension:
    def __init__(self, args: BashArgsNS, fs: IFileSystem, cell: str, logger: Logger):
        self.args = args
        self.fs = fs
        self.cell = cell
        self.logger = logger

    def run(self) -> None:
        self.logger.setLevel(self.args.logLevel)
        if self.fs is None:
            return
        olddir = self.fs.getcwd()
        try:
            self.logger.debug("Current dir: %s", self.fs.getcwd())
            self.logger.debug("The argument are %s", self.args)

            command = preprocessCommand(self.cell, self.args)
            self._prepare(self.args, self.fs, self.logger)
            executeCmd(command, self.args, fs=self.fs, logger=self.logger)
        finally:
            self.fs.chdir(olddir)

    def _prepare(self, args: BashArgsNS, fs: IFileSystem, logger: Logger) -> None:
        folderExists = fs.exists(args.cwd)
        if args.create:
            if folderExists:
                if args.init:
                    logger.debug(
                        "Folder %r exists and we need to remove it because --init is specified",
                        args.cwd,
                    )
                    fs.remove(args.cwd)
                    fs.makedirs(args.cwd)
                else:
                    logger.debug(
                        "Folder %r exists and we don't need to remove it", args.cwd
                    )
            else:
                fs.makedirs(args.cwd)
        else:
            if not folderExists:
                raise Exception(
                    f"Accessing non existing working directory: {args.cwd}! You can specify --create flag to create an empty working directory"
                )
        fs.chdir(args.cwd)


@magics_class
class BashMagics(Magics):
    @cell_magic
    @suppress(
        KeyboardInterrupt,
        onerror=lambda sp: print(f"{os.linesep}KeyboardInteruptted ^C"),
    )
    @suppress(Exception)
    def bash(self, line: str, cell: str):
        args = get_args(line)
        fs = FileSystemFactory.get_filesystem(
            args.container, get_ipython(), global_logger
        )
        if fs is None:
            global_logger.error("Initialize a None FileSystem")
            return
        bash = BashExtension(args, fs, cell, global_logger)
        bash.run()


# load point
def load_ipython_extension(ipython):
    ipython.register_magics(BashMagics)
