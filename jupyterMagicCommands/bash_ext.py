# ~/.ipython/extensions/bash_ext.py

import os
import time
import argparse
from IPython import get_ipython
from IPython.core.magic import register_cell_magic

def executeCmd(command, verbose=False, **kwargs):
    if verbose:
        print(command)
    encoding = "utf-8"
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdirname:
        filePath = os.path.join(tmpdirname, str(int(time.time())) + ".sh")
        with open(filePath, 'w', encoding=encoding) as f:
            f.write(command)
        get_ipython().system(f"bash {filePath}")

def preprocessCommand(command: str, args: argparse.Namespace) -> str:
    command = "cd {}\n".format(args.cwd) + command
    return command

@register_cell_magic
def bash(line, cell):
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", type=str, default=".")
    line = line.strip('\n').strip(' ').lstrip('%%bash')
    if line:
        args = parser.parse_args(line.split(' '))
    else:
        args = parser.parse_args([])
    command = preprocessCommand(cell, args)
    executeCmd(command, args)

def load_ipython_extension(ipython):
    ipython.register_magic_function(bash, 'cell')