import logging
import os
from argparse import Namespace
from io import StringIO
from logging import DEBUG, ERROR, INFO

from jupyterMagicCommands.filesystem.filesystem_factory import \
    FileSystemFactory
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem

logger = logging.getLogger(__name__)
logger.setLevel(ERROR)

streamhandler = logging.StreamHandler()
streamhandler.setLevel(DEBUG)

formatter = logging.Formatter("%(asctime)s - %(filename)s - %(name)s - %(levelname)s - %(message)s")
streamhandler.setFormatter(formatter)
logger.addHandler(streamhandler)

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
    if fs.exists(filePath):
        if args.append:
            log = f"Appending {filePath}"
        else:
            log = f'Overwriting {filePath}'  
    else:
        if args.append:
            print(f"Trying to append to a non-existing file {filePath}. Can't write such file!")
            return
        else:
            log = f'Writing {filePath}'
    
    with fs.open(filePath, mode, encoding='utf8') as f:
        f.write(text)
    print(log)

def writefile(line, cell):
    sio = StringIO(cell)
    text  = sio.read()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filePath')
    parser.add_argument('-c', '--container', type=str, default=None)
    parser.add_argument('-a', '--append', action='store_true', default=False)
    parser.add_argument('-f', '--force', action='store_true', default=False)
    parser.add_argument('-d', '--directory', default=None)
    parser.add_argument('-l', '--logLevel', choices=[DEBUG, INFO, ERROR], default=INFO)
    args = parser.parse_args(line.strip(' ').split(' '))

    logger.setLevel(args.logLevel)

    fs = FileSystemFactory.get_filesystem(args.container)
    _writefile(text, args, fs)
    
    return

def load_ipython_extension(ipython):
    ipython.register_magic_function(writefile, 'cell')
