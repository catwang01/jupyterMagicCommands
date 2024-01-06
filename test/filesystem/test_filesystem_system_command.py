import re
import textwrap

from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.filesystem.docker import DockerFileSystem

class TestDockerFileSystemSysemCommand:
    def test_filesystem(self, fs: IFileSystem, capsys):
        fs.system("echo hello")
        captured = capsys.readouterr()
        assert captured.out == "hello\r\n"

    def test_filesystem_with_filename_save_output_into_file(
        self, fs: IFileSystem, tmp_path, capsys
    ):
        filePath = tmp_path / "test.txt"
        fs.system("echo hello", outFile=filePath)
        captured = capsys.readouterr()
        assert captured.out == ""
        assert fs.exists(filePath) == True
        with fs.open(filePath, "r", "utf8") as f:
            assert f.read() == "hello\n"

    def test_filesystem_background(self, fs: IFileSystem, capsys):
        filePath = "/tmp/out.log"
        fs.remove(filePath)
        fs.system("echo hello", background=True)
        captured = capsys.readouterr()
        expectedPattern = f"""\
        WARNING: outFile is not set, the default output file is {filePath}
        """
        assert re.search(textwrap.dedent(expectedPattern), captured.out) is not None
        assert fs.exists(filePath) == True
        with fs.open(filePath, "r", "utf8") as f:
            assert f.read() == "hello\n"

    def test_filesystem_background_filename(self, fs: IFileSystem, tmp_path, capsys):
        filePath = tmp_path / "test.txt"
        fs.system("echo hello", background=True, outFile=filePath)
        captured = capsys.readouterr()
        if isinstance(fs, DockerFileSystem):
            assert captured.out == ""
        else:
            pattern = f"""\
            Run subprocess with pid: [0-9]+. Output to '{filePath}'
            """
            assert re.search(textwrap.dedent(pattern), captured.out) is not None
        assert fs.exists(filePath) == True
        with fs.open(filePath, "r", "utf8") as f:
            assert f.read() == "hello\n"
