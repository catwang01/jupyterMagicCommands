from io import StringIO
from IPython.core.magic import register_cell_magic
from IPython.display import IFrame
import argparse
import os
import hashlib

@register_cell_magic
def html(line: str, cell: str):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-w', '--width', type=int, default=300)
    parser.add_argument('-h', '--height', type=int, default=200) 
    if line:
        args = parser.parse_args(line.strip(' ').split(' '))
    else:
        args = parser.parse_args([])

    cellhash = hashlib.md5(cell.encode('utf8')).hexdigest()
    filename = cellhash + '.html'
    with open(filename, 'w') as f:
        f.write(cell)
    return  IFrame(filename, width=args.width, height=args.height)

def load_ipython_extension(ipython):
    ipython.register_magic_function(html, 'cell')