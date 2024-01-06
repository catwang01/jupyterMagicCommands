from jupyterMagicCommands.outputters.abstract_outputter import AbstractOutputter
from jupyterMagicCommands.utils.general import removeprefix


class BasicInteractiveOutputter(AbstractOutputter):
    def write(self, s):
        print(removeprefix(s, "\x1b[?1h\x1b="), end="")