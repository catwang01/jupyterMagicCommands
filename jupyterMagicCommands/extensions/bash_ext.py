import argparse
import os
import tempfile
import time
from dataclasses import dataclass
from logging import ERROR, Logger
from operator import itemgetter
from typing import Optional

import pexpect
from IPython.display import display

from jupyterMagicCommands.filesystem.filesystem_factory import \
    FileSystemFactory
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
    force_create: bool=False
    cwd: str = '.'
    create: bool = False
    initialize: bool = False
    container: Optional[str] = None
    verbose: bool = False
    backend: str = "plain"
    logLevel: int = ERROR
    height: int = 10
    background: bool=False
    outFile: Optional[str]=None

def initTerminal(initialOptions):
    termName = f"term_{time.strftime('%Y_%m_%d_%H_%M_%S')}"
    display({'text/html': template % ({'termName': termName, 'rows': initialOptions['rows']}) }, raw=True)
    displayHandler = display({'text/html': "<div></div>" }, raw=True, display_id=True)
    return termName, displayHandler

def sendToTerminal(termName, displayHandler, message, prevMessage=None):
    currentMessage = message
    if prevMessage is not None:
        currentMessage = message[len(prevMessage):]
    unicodeArray = [ord(ch) for ch in currentMessage]
    template = f"""
<script>
    // window.{termName}.clear();
    window.{termName}.write({unicodeArray});
</script>
"""
    displayHandler.update({'text/html': template}, raw=True)

def plainExecuteCommand(command: str, args: BashArgsNS, **kwargs):
    logger = kwargs.get('logger', NULL_LOGGER)

    verbose, background, interactive, outFile = itemgetter('verbose', 'background', 'interactive', 'outFile')(vars(args))
    logger.debug('### Parameters starts ###')
    logger.debug(f"command: '{command}'")
    logger.debug(f"verbose: '{verbose}'")
    logger.debug(f"kwargs: '{kwargs}'")
    logger.debug('### Parameters ends ###')
    if verbose:
        print(command)
    if kwargs.get('fs', None) is not None:
        kwargs['fs'].system(command,
                            background=background,
                            interactive=interactive,
                            outFile=outFile)
    else:
        raise Exception("FileSystem is not initliazed for a container!")

def xtermExecuteCommand(command: str, args: BashArgsNS, **kwargs):
    logger = kwargs.get('logger', NULL_LOGGER)
    verbose, height = itemgetter('verbose', 'height')(vars(args))
    if verbose:
        print(command)
    encoding = 'utf8'
    with tempfile.NamedTemporaryFile(encoding=encoding, mode='w') as fp:
        fp.write(command)
        fp.seek(0)
        cmd = f"bash '{fp.name}'"
        logger.debug(cmd)
        child = pexpect.spawn(cmd)
        initialOptions = {
            'rows': height
        }
        termName, displayHandler = initTerminal(initialOptions)
        prevMessage = ""
        while True:
            try:
                i = child.expect_list([pexpect.TIMEOUT, pexpect.EOF], timeout=0.2) # fresh terminal per 0.2s
                message = child.before.decode()
                sendToTerminal(termName, displayHandler, message, prevMessage)
                prevMessage = message
                if i != 0: break
            except KeyboardInterrupt:
                child.sendintr()

def executeCmd(command: str, args: BashArgsNS, **kwargs):
    backend = args.backend
    if backend == "plain":
        plainExecuteCommand(command, args, **kwargs)
    elif backend == "xterm":
        if kwargs.get('container', None) is not None:
            raise Exception(f"Backend {backend} doesn't suppor docker running in a container")
        xtermExecuteCommand(command, args, **kwargs)
    else:
        raise NotValidBackend(f"Not a valid backend {backend}")

def preprocessCommand(command: str, args: BashArgsNS) -> str:
    """
    Currently no preprocess is needed
    """
    return command

def _prepare(args: BashArgsNS, fs: IFileSystem, logger: Logger) -> None:
    if fs.exists(args.cwd):
        logger.debug("Folder %r exists", args.cwd)
        if args.force_create:
            fs.removedirs(args.cwd)
    else:
        logger.debug("Folder %r doesn't exist", args.cwd)
        if args.create:
            logger.debug(f"Create folder {args.cwd}")
            fs.makedirs(args.cwd)
        else:
            raise Exception(f"Accessing non existing working directory: {args.cwd}! You can specify --create flag to create an empty working directory")
    fs.chdir(args.cwd)

def get_args(line: str) -> BashArgsNS:
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--d", "--cwd", dest="cwd", type=str, default=".", help="Working directory")
    parser.add_argument("--create",
                        action='store_true',
                        default=False,
                        help="Create the working directory if not existing. Do nothing if the directory exists")
    parser.add_argument("-f", "--force-create",
                        action='store_true',
                        default=False,
                        help="Force create the working directory. If it exists, remove it and create an empty one. if not, create an empty one.")
    parser.add_argument('-c', '--container',
                        help="docker container name or id, if this is specified, the command would run in the specified container ")
    parser.add_argument("-v", "--verbose", action='store_true', default=False)
    parser.add_argument("-b", "--backend", type=str, choices=["plain", "xterm"], default="plain")
    parser.add_argument("--logLevel", type=parse_logLevel, default="ERROR")
    parser.add_argument("--height", type=int, default=10)
    mg = parser.add_mutually_exclusive_group()
    mg.add_argument("-i", "--interactive",
                    action='store_true',
                    default=False,
                    help="Execute the command interactively")
    mg.add_argument("--bg", "--background",
                    dest="background",
                    action='store_true',
                    default=False)
    parser.add_argument("--outfile", "--outFile",
                        dest="outFile",
                        type=str,
                        default=None)
    line = line.strip('\n').strip(' ').lstrip('%%bash')
    if line:
        args = parser.parse_args(line.split(' '), namespace=BashArgsNS())
    else:
        args = parser.parse_args([], namespace=BashArgsNS())
    return args

def _bash(args: BashArgsNS, fs: IFileSystem, cell: str):
    global_logger.debug("Current dir: %s", fs.getcwd())
    global_logger.debug(args)

    command = preprocessCommand(cell, args)
    _prepare(args, fs, global_logger)
    executeCmd(command, args, fs=fs, logger=global_logger)

@suppress(KeyboardInterrupt, onerror=lambda sp: print(f"{os.linesep}KeyboardInteruptted ^C"))
@suppress(Exception)
def bash(line: str, cell: str):
    args = get_args(line)
    global_logger.setLevel(args.logLevel)
    fs = FileSystemFactory.get_filesystem(args.container, global_logger)
    olddir = fs.getcwd()
    try:
        _bash(args, fs, cell)
    finally:
        fs.chdir(olddir)

# load point
def load_ipython_extension(ipython):
    ipython.register_magic_function(bash, 'cell')