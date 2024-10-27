import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from jupyterMagicCommands.utils.parser import parse_logLevel
from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.core.magic_arguments import (argument, magic_arguments,
                                          parse_argstring)

from jupyterMagicCommands.outputters import BasicFileSystemOutputterFactory
from jupyterMagicCommands.outputters.abstract_outputter import \
    AbstractOutputter
from jupyterMagicCommands.session import Session, SessionManager
from jupyterMagicCommands.utils.log import NULL_LOGGER, getLogger

global_logger = getLogger(__name__)

@dataclass
class PwshArgs:
    sessionId: str

manager = SessionManager(logger=global_logger)

def pwsh(args: PwshArgs, manager: SessionManager, outputter: AbstractOutputter, cell: str, logger=NULL_LOGGER):
    if sys.platform == 'win32':
        retriever = lambda : Session('powershell', outputter=outputter, logger=logger)
    else:
        retriever = lambda : Session('pwsh', outputter=outputter, logger=logger)
    try:
        session = manager.getOrCreateSession(args.sessionId, retriever)
    except Exception as e:
        raise Exception(f"Can't initialize session with id '{args.sessionId}'") from e

    encoding = 'utf8'
    with TemporaryDirectory() as tmpdirname:
        logger.debug("Entering tmpdir %s", tmpdirname)
        filePath = Path(os.path.join(tmpdirname, str(int(time.time())) + ".ps1"))
        logger.debug("Written command into file %s", filePath)
        filePath.write_text(cell, encoding=encoding)
        session.invoke_command('. '  + str(filePath))

@magics_class
class PowershellMagicCommand(Magics):

    @magic_arguments()
    @argument(
        "--sessionId",
        default="1",
        help=("Sessoin Id"),
    )
    @argument("--logLevel", type=parse_logLevel, default="ERROR")
    @cell_magic
    def pwsh(self, line, cell):
        args = parse_argstring(self.pwsh, line)
        global_logger.setLevel(args.logLevel)
        outputterFactory = BasicFileSystemOutputterFactory(self.shell)
        outputter = outputterFactory.create_outputter(False)
        # executeCmd(f'pwsh -NoProfile -File "{filePath}"')
        pwsh(args, manager, outputter, cell, global_logger)

def load_ipython_extension(ipython):
    ipython.register_magics(PowershellMagicCommand)