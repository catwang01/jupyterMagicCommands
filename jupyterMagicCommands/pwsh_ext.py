import os
import time
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from IPython.core.magic import register_cell_magic
from IPython import get_ipython

@register_cell_magic
def pwsh(line, cell):
    encoding = 'utf8'
    "Magic that works both as %ps and as %%ps" 
    with TemporaryDirectory() as tmpdirname:
        filePath = Path(os.path.join(tmpdirname, str(int(time.time())) + ".ps1"))
        filePath.write_text(cell, encoding=encoding)
        get_ipython().system(f'pwsh -NoProfile -File "{filePath}"')

def load_ipython_extension(ipython):
    ipython.register_magic_function(pwsh, 'cell')
