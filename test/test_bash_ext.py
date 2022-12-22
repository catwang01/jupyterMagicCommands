from jupyterMagicCommands.bash_ext import bash

class TestBaseExt:

    def test_bash_ext(self):
        line = "%%bash"
        cell = "ls"
        bash(line, cell)