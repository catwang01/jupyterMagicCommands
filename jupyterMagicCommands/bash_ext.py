# ~/.ipython/extensions/bash_ext.py

import os
import time
import pexpect
import argparse
from IPython.display import display
from IPython.core.magic import register_cell_magic

template = """
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@4.5.0/css/xterm.css" />
    <script src="https://cdn.jsdelivr.net/npm/xterm@4.5.0/lib/xterm.js"></script>
    <div>
    <div id="%(termName)s"></div>
    <script>
        // create an instance of terminal and attach it to window.
        var %(termName)s = new Terminal();
        window.%(termName)s.open(document.getElementById('%(termName)s'));
    </script>
    </div>
""" 

def initTerminal():
    termName = f"term_{time.strftime('%Y_%m_%d_%H_%M_%S')}"
    display({'text/html': template % ({'termName': termName}) }, raw=True)
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

def executeCmd(command, verbose=False, **kwargs):
    if verbose:
        print(command)
    encoding = "utf-8"
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdirname:
        filePath = os.path.join(tmpdirname, str(int(time.time())) + ".sh")
        with open(filePath, 'w', encoding=encoding) as f:
            f.write(command)
        child = pexpect.spawn(f"bash {filePath}")
        termName, displayHandler = initTerminal()
        prevMessage = None
        while True:
            i = child.expect_list([pexpect.TIMEOUT, pexpect.EOF], timeout=0.2) # fresh terminal per 0.2s
            message = child.before.decode()
            sendToTerminal(termName, displayHandler, message, prevMessage)
            prevMessage = message
            if i == 1: break

def preprocessCommand(command: str, args: argparse.Namespace) -> str:
    command = "cd {}\n".format(args.cwd) + command
    return command

@register_cell_magic
def bash(line, cell):
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--d", "--cwd", dest="cwd", type=str, default=".")
    parser.add_argument("-v", "--verbose", action='store_true', default=False)
    line = line.strip('\n').strip(' ').lstrip('%%bash')
    if line:
        args = parser.parse_args(line.split(' '))
    else:
        args = parser.parse_args([])
    command = preprocessCommand(cell, args)
    executeCmd(command, args.verbose)

def load_ipython_extension(ipython):
    ipython.register_magic_function(bash, 'cell')
