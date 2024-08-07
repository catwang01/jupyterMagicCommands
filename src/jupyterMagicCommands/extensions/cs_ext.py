import argparse
import logging
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from jupyterMagicCommands.utils.cmd import executeCmd

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
    # since C#9, there is no need to have a Main
    # code = completeCode(cell, args)
    code = cell
    logger.debug(code)
    verbose = args.verbose
    with TemporaryDirectory() as tmpDir:
        executeCmd(f"dotnet new console", cwd=tmpDir, verbose=verbose)
        tmpFile = Path(tmpDir) / 'Program.cs'
        tmpFile.write_text(code)
        for packageInfo in args.packageInfos:
            if "version" in packageInfo:
                executeCmd(f"dotnet add package {packageInfo['name']} --version {packageInfo['version']}", cwd=tmpDir, verbose=verbose)
            else:
                executeCmd(f"dotnet add package {packageInfo['name']}", cwd=tmpDir, verbose=verbose)
        executeCmd("dotnet run", cwd=tmpDir, verbose=True)
                
def transformLogLevel(s):
    level = {
        'INFO': logging.INFO,
        "DEBUG": logging.DEBUG
    }.get(s.upper())
    if level is None:
        print(f"Unsupported level: {s}")
        sys.exit(1)
    return level

def processPackageInfo(s):
    ret = {}
    infos = s.split("@")
    if len(infos) == 1:
        ret['name'] = infos[0]
    elif len(infos) == 2:
        ret['name'] = infos[0]
        ret['version'] = infos[1]
    else:
        raise Exception(f"Not a valid package info: {s}. Package info should be <package-name> or <package-name>@<version>")
    return ret

def cs(line, cell):
    parser = argparse.ArgumentParser()
    parser.add_argument('--logLevel', default='INFO', type=transformLogLevel)
    parser.add_argument('--addPackage', dest="packageInfos", type=processPackageInfo , action="append" , default=[], help="package information formatted as <packagename>@<version>")
    parser.add_argument('--verbose', action="store_true", default=False)
    if line.strip() != '':
        args = parser.parse_args(line.strip(' ').split(' '))
    else:
        args = parser.parse_args([])
    logger.setLevel(args.logLevel)
    logger.debug("args: %s", args)
    runCsharp(cell, args)
    
def load_ipython_extension(ipython):
    ipython.register_magic_function(cs, 'cell')
