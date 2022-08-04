import os
from subprocess import Popen, PIPE
from pathlib import Path
import shlex

def _run_command(cmd):
    with Popen(shlex.split(cmd), stdout=PIPE, bufsize=1, universal_newlines=True) as p:
        while True:
            line = p.stdout.readline()
            if not line:
                break
            print(line, end="")
        exit_code = p.poll()
    return exit_code

def executeCmd(cmd, cwd='.', backend=None):
    currentDir = Path.cwd()
    os.chdir(cwd)
    try:
        if backend is None or backend == "ipython":
            get_ipython().system(cmd)
        else:
            _run_command(cmd)
    finally:
        os.chdir(currentDir)
