import logging
import os
import argparse
from argparse import Namespace
from io import StringIO
from logging import DEBUG, ERROR, INFO
import shlex

from jupyterMagicCommands.filesystem.filesystem_factory import \
    FileSystemFactory
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.extensions.constants import \
        EMPTY_CONTAINER_NAME, \
        JUPYTER_MAGIC_COMMAND_BASH_CURRENT_CONTAINER

logger = logging.getLogger(__name__)
logger.setLevel(ERROR)

streamhandler = logging.StreamHandler()
streamhandler.setLevel(DEBUG)

formatter = logging.Formatter("%(asctime)s - %(filename)s - %(name)s - %(levelname)s - %(message)s")
streamhandler.setFormatter(formatter)
logger.addHandler(streamhandler)

def get_args(line: str):
    parser = argparse.ArgumentParser()
    parser.add_argument('filePath')
    parser.add_argument('-c', '--container', type=str,
                        nargs="?",
                        help="docker container name or id, if this is specified, the command would run in the specified container",
                        const=os.environ.get(
                                JUPYTER_MAGIC_COMMAND_BASH_CURRENT_CONTAINER, 
                                EMPTY_CONTAINER_NAME
                            )
                        )
    parser.add_argument('-a', '--append', action='store_true', default=False)
    parser.add_argument('-f', '--force', action='store_true', default=False)
    parser.add_argument('-d', '--directory', default='.')
    parser.add_argument('-l', '--logLevel', choices=[DEBUG, INFO, ERROR], default=INFO)
    args = parser.parse_args(shlex.split(line))
    logger.setLevel(args.logLevel)
    return args

def _writefile(text: str, args: Namespace, fs: IFileSystem) -> None:
    if args.directory is not None:
        filePath = os.path.expanduser(os.path.join(args.directory, args.filePath))
    else:
        filePath= os.path.expanduser(args.filePath)
    dirPath = os.path.dirname(filePath)
    if args.force and not fs.exists(dirPath):
        fs.makedirs(dirPath)
    mode = 'w'
    if args.append:
        mode = 'a'
    message: str = ""
    if fs.exists(filePath):
        if args.append:
            message = f"Appending {filePath}"
        else:
            message = f'Overwriting {filePath}'  
    else:
        if args.append:
            print(f"Trying to append to a non-existing file {filePath}. Can't write such file!")
            return
        else:
            message = f'Writing {filePath}'
    
    with fs.open(filePath, mode, encoding='utf8') as f:
        f.write(text)
    if message: print(message)

def writefile(line, cell):
    sio = StringIO(cell)
    text  = sio.read()
    args = get_args(line)
    fs = FileSystemFactory.get_filesystem(args.container)
    if fs is None:
        return
    _writefile(text, args, fs)
    return

def load_ipython_extension(ipython):
    ipython.register_magic_function(writefile, 'cell')
