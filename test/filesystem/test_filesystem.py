import os
import re
import textwrap
from pathlib import Path

import pytest

from jupyterMagicCommands.filesystem.filesystem import FileSystem


@pytest.fixture
def fs():
    return FileSystem()


def test_filesystem(fs, capsys):
    fs.system("echo hello")
    captured = capsys.readouterr()
    assert captured.out == "hello\r\n"


def test_filesystem_with_filename_save_output_into_file(fs, tmp_path, capsys):
    file = tmp_path / "test.txt"
    p = Path(file)
    fs.system("echo hello", outFile=file)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert p.exists() == True
    assert p.read_text() == "hello\n"


def test_filesystem_background(fs, capsys):
    p = Path("/tmp/out.log")
    os.remove("/tmp/out.log")
    fs.system("echo hello", background=True)
    captured = capsys.readouterr()
    expectedPattern = """\
    WARNING: outFile is not set, the default output file is /tmp/out.log
    Run subprocess with pid: [0-9]+. Output to '/tmp/out.log'
    """
    assert re.search(textwrap.dedent(expectedPattern), captured.out) is not None
    assert p.exists() == True
    assert p.read_text() == "hello\n"


def test_filesystem_background_filename(fs, tmp_path, capsys):
    file = tmp_path / "test.txt"
    p = Path(file)
    fs.system("echo hello", background=True, outFile=file)
    captured = capsys.readouterr()
    expectedPattern = f"""\
    Run subprocess with pid: [0-9]+. Output to '{file}'
    """
    assert re.search(textwrap.dedent(expectedPattern), captured.out) is not None
    assert p.exists() == True
    assert p.read_text() == "hello\n"
