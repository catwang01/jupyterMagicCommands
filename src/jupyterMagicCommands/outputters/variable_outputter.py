from typing import Optional

from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell
from overrides import override

from jupyterMagicCommands.outputters.abstract_outputter import \
    AbstractOutputter


class VariableOutputter(AbstractOutputter):

    _default_shell = get_ipython()

    def __init__(self, var_name: str, shell: Optional[InteractiveShell] = None) -> None:
        self.var_name = var_name
        self.shell = shell or self._default_shell
        self._first_write = True

    @override
    def write(self, s: str):
        if self._first_write:
            self.shell.user_ns[self.var_name] = ""
            self._first_write = False
        self.shell.user_ns[self.var_name] += s

    @override
    def handle_read(self):
        pass

    @override
    def register_read_callback(self, cb):
        pass