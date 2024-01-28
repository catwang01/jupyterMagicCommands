from jupyterMagicCommands.outputters.abstract_outputter import AbstractOutputter
from overrides import override
import atexit


class FileOutputter(AbstractOutputter):

    def __init__(self, file_path: str, **kwargs) -> None:
        self.file_path = file_path
        self.file = open(file_path, "w", **kwargs)
        atexit.register(self.file.close)

    @override
    def write(self, s: str):
        self.file.write(s)
        self.file.flush()

    @override
    def handle_read(self):
        pass

    @override
    def register_read_callback(self, cb):
        pass