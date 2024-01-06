from jupyterMagicCommands.outputters import (
    FileOutputter,
    InteractiveOutputter,
    VariableOutputter,
    BasicInteractiveOutputter,
    AbstractOutputterFactory,
    AbstractOutputter
)
from IPython.core.interactiveshell import InteractiveShell


class BasicFileSystemOutputterFactory(AbstractOutputterFactory):

    def __init__(self, shell: InteractiveShell):
        self.shell = shell

    def create_outputter(self, interactive, outFile, outVar):
        outputter: AbstractOutputter
        if interactive:
            outputter = InteractiveOutputter()
        else:
            if outFile is not None:
                outputter = FileOutputter(outFile)
            elif outVar is not None:
                outputter = VariableOutputter(outVar, self.shell)
            else:
                outputter = BasicInteractiveOutputter()
        return outputter


class DockerFileSystemOutputterFactory(AbstractOutputterFactory):

    def __init__(self, shell: InteractiveShell):
        self.shell = shell

    def create_outputter(self, interactive, outFile, outVar):
        outputter: AbstractOutputter
        if interactive:
            outputter = InteractiveOutputter()
        elif outVar is not None:
            outputter = VariableOutputter(outVar, self.shell)
        else:
            outputter = BasicInteractiveOutputter()
        return outputter