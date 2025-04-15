import pytest
from jupyterMagicCommands.filesystem.fileSystemMode import FileSystemMode


def test_fileSystemMode_to_octal():
    assert FileSystemMode(0o777).to_octal() == 777
    
def test_fileSystemMode_to_decimal():
    assert FileSystemMode(0o777).to_decimal() == 0o777

@pytest.mark.parametrize(
    "value",
    [
        777,
        -1,
    ],
)
def test_fileSystemMode_failed_with_valueError(value):
    with pytest.raises(ValueError):
        FileSystemMode(value)

def test_fileSystemMode_eq():
    assert FileSystemMode(0o777) == FileSystemMode(0o777)

def test_fileSystemMode_hash():
    s = set()
    s.add(FileSystemMode(0o777))
    s.add(FileSystemMode(0o777))
    assert len(s) == 1

def test_fileSystemMode_from_string():
    assert FileSystemMode.from_string("777") == FileSystemMode(0o777)