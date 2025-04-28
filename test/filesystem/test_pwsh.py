from jupyterMagicCommands.extensions.pwsh_ext import PwshArgs, pwsh
from unittest.mock import MagicMock

from jupyterMagicCommands.outputters import DummyOutputter
from jupyterMagicCommands.session.manager import SessionManager

outputter = DummyOutputter()
outputter.write = MagicMock()

manager = SessionManager()

def test_pwsh():
    cell = "Write-Host 'Hello, World!'"
    args = PwshArgs(sessionId='1')
    pwsh(args, manager, outputter, cell)
    outputter.write.assert_called_with('Hello, World!\n')