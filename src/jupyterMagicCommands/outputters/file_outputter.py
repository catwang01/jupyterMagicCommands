from jupyterMagicCommands.outputters.abstract_outputter import AbstractOutputter
from overrides import override


class FileOutputter(AbstractOutputter):

    def __init__(self, file_path: str, **kwargs) -> None:
        self.file_path = file_path
        self.file = open(file_path, "w", **kwargs)

    @override
    def write(self, s: str):
        self.file.write(s)
        self.file.flush()

    @override
    def close(self) -> None:
        if not self.file.closed:
            self.file.close()

    def __del__(self):
        self.close()

    @override
    def handle_read(self):
        pass

    @override
    def register_read_callback(self, cb):
        pass
