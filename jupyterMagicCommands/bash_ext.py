# ~/.ipython/extensions/bash_ext.py

import os
import time
import pexpect
import tempfile
import argparse
from IPython.display import display
from IPython import get_ipython
from IPython.core.magic import register_cell_magic

template = """
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@4.5.0/css/xterm.css" />
    <script src="https://cdn.jsdelivr.net/npm/xterm@4.5.0/lib/xterm.js"></script>
    <div>
    <div id="%(termName)s"></div>
    <script>
        // create an instance of terminal and attach it to window.
        var %(termName)s = new Terminal(
            {
                rows: %(rows)s
            }
        );
        window.%(termName)s.open(document.getElementById('%(termName)s'));
    </script>
    </div>
""" 

class NotValidBackend(Exception):
    pass

def initTerminal(initialOptions):
    termName = f"term_{time.strftime('%Y_%m_%d_%H_%M_%S')}"
    display({'text/html': template % ({'termName': termName, 'rows': initialOptions['rows']}) }, raw=True)
    displayHandler = display({'text/html': "<div></div>" }, raw=True, display_id=True)
    return termName, displayHandler

def sendToTerminal(termName, displayHandler, message, prevMessage=None):
    currentMessage = message
    if prevMessage is not None:
        currentMessage = message[len(prevMessage):]
    unicodeArray = [ord(ch) for ch in currentMessage]
    template = f"""
<script> 
    // window.{termName}.clear();
    window.{termName}.write({unicodeArray});
</script>
"""
    displayHandler.update({'text/html': template}, raw=True)

def plainExecuteCommand(command, verbose=False, **kwargs):
    if verbose:
        print(command)
    encoding = "utf-8"
    with tempfile.NamedTemporaryFile(encoding=encoding, mode='w') as fp:
        fp.write(command)
        fp.seek(0)
        cmd = f"bash '{fp.name}'"
        get_ipython().system(cmd)

def xtermExecuteCommand(command, verbose=False, **kwargs):
    if verbose:
        print(command)
    encoding = 'utf8'
    with tempfile.NamedTemporaryFile(encoding=encoding, mode='w') as fp:
        fp.write(command)
        fp.seek(0)
        child = pexpect.spawn(f"bash {fp.name}")
        initialOptions = {
            'rows': kwargs.get('height', 10)
        }
        termName, displayHandler = initTerminal(initialOptions)
        prevMessage = ""
        while True:
            try:
                i = child.expect_list([pexpect.TIMEOUT, pexpect.EOF], timeout=0.2) # fresh terminal per 0.2s
                message = child.before.decode()
                sendToTerminal(termName, displayHandler, message, prevMessage)
                prevMessage = message
                if i != 0: break
            except KeyboardInterrupt:
                child.sendintr()

def executeCmd(*args, backend="plain", **kwargs):
    if backend == "plain":
        plainExecuteCommand(*args, **kwargs)
    elif backend == "xterm":
        xtermExecuteCommand(*args, **kwargs)
    else:
        raise NotValidBackend(f"Not a valid backend {backend}")

def preprocessCommand(command: str, args: argparse.Namespace) -> str:
    command = "cd {}\n".format(args.cwd) + command
    return command

@register_cell_magic
def bash(line, cell):
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--d", "--cwd", dest="cwd", type=str, default=".")
    parser.add_argument("-v", "--verbose", action='store_true', default=False)
    parser.add_argument("-b", "--backend", type=str, default="plain")
    parser.add_argument("--height", type=int, default=10)
    line = line.strip('\n').strip(' ').lstrip('%%bash')
    if line:
        args = parser.parse_args(line.split(' '))
    else:
        args = parser.parse_args([])
    command = preprocessCommand(cell, args)
    executeCmd(command, verbose=args.verbose, backend=args.backend, height=args.height)

def load_ipython_extension(ipython):
    ipython.register_magic_function(bash, 'cell')
