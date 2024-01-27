from jupyterMagicCommands.outputters.abstract_outputter import AbstractOutputter
from overrides import override
from jupyterMagicCommands.outputters.outputter_cb import AbstractOutputterReadCB
from jupyterMagicCommands.utils.general import removeprefix


class BasicInteractiveOutputter(AbstractOutputter):

    @override
    def write(self, s: str):
        print(removeprefix(s, "\x1b[?1h\x1b="), end="")

    @override
    def handle_read(self):
        pass

    @override
    def register_read_callback(self, cb: AbstractOutputterReadCB):
        pass