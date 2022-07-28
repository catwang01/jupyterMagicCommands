from subprocess import Popen, PIPE
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

def executeCmd(cmd, backend=None):
    if backend is None or backend == "ipython":
        get_ipython().system(cmd)
    else:
        _run_command(cmd)
