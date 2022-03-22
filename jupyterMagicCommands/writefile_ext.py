from io import StringIO
from IPython.core.magic import register_cell_magic
import os

@register_cell_magic
def writefile(line, cell):
    sio = StringIO(cell)
    text  = sio.read()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filePath')
    parser.add_argument('-a', '--append', action='store_true', default=False)
    parser.add_argument('-f', '--force', action='store_true', default=False)
    parser.add_argument('-d', '--directory', default=None)
    args = parser.parse_args(line.strip(' ').split(' '))
    
    if args.directory is not None:
        filePath = os.path.expanduser(os.path.join(args.directory, args.filePath))
    else:
        filePath= os.path.expanduser(args.filePath)
    dirPath = os.path.dirname(filePath)
    if args.force and not os.path.exists(dirPath):
        os.makedirs(dirPath)
    mode = 'w'
    if args.append:
        mode += 'a'
    log = f'Overwriting {filePath}' if os.path.exists(filePath) else f'Writing {filePath}'
    with open(filePath, mode) as f:
        f.write(text)
    print(log)
    return

def load_ipython_extension(ipython):
    ipython.register_magic_function(writefile, 'cell')