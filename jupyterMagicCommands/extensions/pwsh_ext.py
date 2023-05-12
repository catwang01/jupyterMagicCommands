import os
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from jupyterMagicCommands.utils.cmd import executeCmd

def pwsh(line, cell):
    encoding = 'utf8'
    with TemporaryDirectory() as tmpdirname:
        filePath = Path(os.path.join(tmpdirname, str(int(time.time())) + ".ps1"))
        filePath.write_text(cell, encoding=encoding)
        executeCmd(f'pwsh -NoProfile -File "{filePath}"')

def load_ipython_extension(ipython):
    ipython.register_magic_function(pwsh, 'cell')
