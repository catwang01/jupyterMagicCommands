import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.core.magic_arguments import (argument, magic_arguments,
                                          parse_argstring)
from pexpect import which

from jupyterMagicCommands.outputters import BasicFileSystemOutputterFactory
from jupyterMagicCommands.outputters.abstract_outputter import \
    AbstractOutputter
from jupyterMagicCommands.session import Session, SessionManager
from jupyterMagicCommands.utils.cmd import executeCmd


@dataclass
class PwshArgs:
    sessionId: str

manager = SessionManager()

def pwsh(args: PwshArgs, manager: SessionManager, outputter: AbstractOutputter, cell: str):
    pwshPath = which('powershell') or which('pwsh')
    encoding = 'utf8'
    with TemporaryDirectory() as tmpdirname:
        filePath = Path(os.path.join(tmpdirname, str(int(time.time())) + ".ps1"))
        filePath.write_text(cell, encoding=encoding)
        if sys.platform == 'win32':
            retriever = lambda : Session(pwshPath, outputter=outputter)
            session = manager.getOrCreateSession(args.sessionId, retriever)
            if session is None:
                raise Exception(f"Can't initialize session with id '{args.sessionId}'")
            session.invoke_command('. '  + str(filePath))
        else:
            executeCmd(pwshPath + ' ' + str(filePath))


@magics_class
class PowershellMagicCommand(Magics):

    @magic_arguments()
    @argument(
        "--sessionId",
        type=int,
        default="-1",
        help=("Sessoin Id"),
    )
    @cell_magic
    def pwsh(self, line, cell):
        args = parse_argstring(self.pwsh, line)
        if args.sessionId != -1 and sys.platform != 'win32':
            raise Exception("Session Id is only supported on non-Windows platforms")
        outputterFactory = BasicFileSystemOutputterFactory(self.shell)
        outputter = outputterFactory.create_outputter(False)
        pwsh(args, manager, outputter, cell)

def load_ipython_extension(ipython):
    ipython.register_magics(PowershellMagicCommand)