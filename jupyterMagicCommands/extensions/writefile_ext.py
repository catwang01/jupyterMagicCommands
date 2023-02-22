import os
from argparse import Namespace
from io import StringIO
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.filesystem.docker import DockerFileSystem

def _writefile(text: str, args: Namespace, fs: IFileSystem):
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
    
    with fs.open(filePath, mode) as f:
        f.write(text)
    print(log)

def writefile(line, cell):
    sio = StringIO(cell)
    text  = sio.read()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filePath')
    parser.add_argument('-i', '--container', type=str, default=None)
    parser.add_argument('-a', '--append', action='store_true', default=False)
    parser.add_argument('-f', '--force', action='store_true', default=False)
    parser.add_argument('-d', '--directory', default=None)
    args = parser.parse_args(line.strip(' ').split(' '))

    fs = DockerFileSystem()
    _writefile(text, args, fs)
    
    return

def load_ipython_extension(ipython):
    ipython.register_magic_function(writefile, 'cell')
