import sys
import re
from io import StringIO
from IPython.core.magic import register_cell_magic
import os
from tempfile import TemporaryDirectory
import argparse
import time
from pathlib import Path
import subprocess
import logging
from .utils import executeCmd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

streamhandler = logging.StreamHandler()
streamhandler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(filename)s - %(name)s - %(levelname)s - %(message)s")
streamhandler.setFormatter(formatter)

logger.addHandler(streamhandler)


def analyzeCode(code):
    usingLines = []
    bodyLines = []
    status = 0
    for line in code.split('\n'):
        if status == 0 or status == 1:
            if line.startswith("using"):
                if status == 0: status = 1
                usingLines.append(line)
            elif line.strip() == '': 
                pass
            else:
                status = 2
                bodyLines.append(line)
        else:
            bodyLines.append(line)
            
    return {'using': '\n'.join(usingLines), 'body': "\n".join(bodyLines)}

def completeCode(code, args):
    # TODO: update here 
    if "Main" in code:
        return code
    else:
        analyzedCode = analyzeCode(code)
        skelton = """
        {using}
        namespace DemoApplication {{
            public class Program {{
                public static void Main() {{
                    {body}
                }}
            }}
        }}
        """
        code = skelton.format(**analyzedCode)
    return code

def runCsharp(cell, args):
    code = completeCode(cell, args)
    logger.debug(code)
    with TemporaryDirectory() as tmpDir:
        tmpDir = Path(tmpDir)
        tmpFile = tmpDir / "{}.cs".format(int(time.time()))
        tmpFile.write_text(code)
        logger.debug(code)
        executeCmd(f"csc {tmpFile.name} -out:tmp.exe -nologo", cwd=tmpDir )
        if os.path.exists(tmpDir / "tmp.exe"):
            executeCmd(f"mono tmp.exe", cwd=tmpDir)
                
def transformLogLevel(s):
    level = {
        'INFO': logging.INFO,
        "DEBUG": logging.DEBUG
    }.get(s.upper())
    if level is None:
        print(f"Unsupported level: {level}")
        sys.exit(1)
    return level
                
@register_cell_magic
def cs(line, cell):
    parser = argparse.ArgumentParser()
    parser.add_argument('--logLevel', default=logging.INFO, type=transformLogLevel)
    if line.strip() != '':
        args = parser.parse_args(line.strip(' ').split(' '))
    else:
        args = parser.parse_args([])
    logger.setLevel(args.logLevel)
    runCsharp(cell, args)
    
def load_ipython_extension(ipython):
    ipython.register_magic_function(cs, 'cell')
