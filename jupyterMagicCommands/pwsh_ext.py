import os
import time
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from IPython.core.magic import register_cell_magic

@register_cell_magic
def pwsh(line, cell):
    encoding = 'utf8'
    with TemporaryDirectory() as tmpdirname:
        filePath = Path(os.path.join(tmpdirname, str(int(time.time())) + ".ps1"))
        filePath.write_text(cell, encoding=encoding)
        subprocess.run(f'pwsh -NoProfile -File "{filePath}"', shell=True)

def load_ipython_extension(ipython):
    ipython.register_magic_function(pwsh, 'cell')
