from abc import ABCMeta, abstractmethod
from typing import Optional

from jupyterMagicCommands.outputters.abstract_outputter import AbstractOutputter


class AbstractOutputterFactory(metaclass=ABCMeta):
    @abstractmethod
    def create_outputter(
        self, interactive: bool, outFile: Optional[str], outVar: Optional[str]
    ) -> AbstractOutputter:
        pass
