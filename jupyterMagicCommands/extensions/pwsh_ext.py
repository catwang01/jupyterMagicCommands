import os
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.core.magic_arguments import (argument, magic_arguments,
                                          parse_argstring)

from jupyterMagicCommands.outputters import BasicFileSystemOutputterFactory
from jupyterMagicCommands.outputters.abstract_outputter import \
    AbstractOutputter
from jupyterMagicCommands.session import Session, SessionManager


@dataclass
class PwshArgs:
    sessionId: str

def pwsh(args: PwshArgs, outputter: AbstractOutputter, cell: str):
    manager = SessionManager()
    retriever = lambda : Session('pwsh', outputter=outputter)
    session = manager.getOrCreateSession(args.sessionId, retriever)
    if session is None:
        raise Exception(f"Can't initialize session with id '{args.sessionId}'")

    encoding = 'utf8'
    with TemporaryDirectory() as tmpdirname:
        filePath = Path(os.path.join(tmpdirname, str(int(time.time())) + ".ps1"))
        filePath.write_text(cell, encoding=encoding)
        session.invoke_command(str(filePath))

@magics_class
class PowershellMagicCommand(Magics):

    @magic_arguments()
    @argument(
        "--sessionId",
        default="1",
        help=("Sessoin Id"),
    )
    @cell_magic
    def pwsh(self, line, cell):
        args = parse_argstring(self.pwsh, line)
        outputterFactory = BasicFileSystemOutputterFactory(self.shell)
        outputter = outputterFactory.create_outputter(True)
        # executeCmd(f'pwsh -NoProfile -File "{filePath}"')
        pwsh(args, outputter, cell)

def load_ipython_extension(ipython):
    ipython.register_magics(PowershellMagicCommand)