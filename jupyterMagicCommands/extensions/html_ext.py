from io import StringIO
from IPython.display import HTML
import argparse
import os
import hashlib

def html(line: str, cell: str):
    parser = argparse.ArgumentParser(add_help=False)
    if line:
        args = parser.parse_args(line.strip(' ').split(' '))
    else:
        args = parser.parse_args([])

    return HTML(cell)

def load_ipython_extension(ipython):
    ipython.register_magic_function(html, 'cell')