from overrides import override
from jupyterMagicCommands.outputters.abstract_outputter import AbstractOutputter

class DummyOutputter(AbstractOutputter):

    @override
    def write(self, s) -> None:
        pass

    @override
    def handle_read(self) -> None:
        pass

    @override
    def register_read_callback(self, cb) -> None:
        pass