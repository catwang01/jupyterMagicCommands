from jupyterMagicCommands.outputters.abstract_outputter import AbstractOutputter


import atexit


class FileOutputter(AbstractOutputter):
    def __init__(self, file_path: str, **kwargs) -> None:
        self.file_path = file_path
        self.file = open(file_path, "w", **kwargs)
        atexit.register(self.file.close)

    def write(self, s: str):
        self.file.write(s)
        self.file.flush()