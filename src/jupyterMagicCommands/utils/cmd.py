import os
import logging
from IPython import get_ipython
import subprocess
from subprocess import Popen, PIPE, STDOUT
from pathlib import Path
import shlex

logger = logging.getLogger(__name__)

def _run_command(cmd):
    with Popen(shlex.split(cmd), stdout=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True) as p:
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
    ret = None
    try:
        if not verbose: 
            ret = subprocess.run(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        elif backend is None or backend == "ipython":
            get_ipython().system(cmd)
        elif backend.lower() == "popen":
            _run_command(cmd)
        else:
            raise ValueError(f"Unsupported backend: {backend}")
    finally:
        os.chdir(currentDir)
    return ret
