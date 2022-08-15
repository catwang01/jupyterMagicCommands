import os
import subprocess
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

def executeCmd(cmd, cwd='.', verbose=True, backend=None):
    currentDir = Path.cwd()
    os.chdir(cwd)
    try:
        if verbose == False:
            ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
        elif backend is None or backend == "ipython":
            get_ipython().system(cmd)
        else:
            _run_command(cmd)
    finally:
        os.chdir(currentDir)
