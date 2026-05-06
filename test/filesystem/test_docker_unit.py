from unittest.mock import MagicMock, patch
import pytest
from jupyterMagicCommands.filesystem.docker import DockerFileSystem


def _make_dockerfs():
    """Create a DockerFileSystem with a fully mocked container."""
    container = MagicMock()
    # exec_run for detecting default_shell
    container.exec_run.return_value = MagicMock(exit_code=0, output=b"bash\n")
    outputter_factory = MagicMock()
    return DockerFileSystem(container, outputter_factory), container


class TestDockerIsDir:

    def test_is_dir_returns_true_for_directory(self):
        fs, container = _make_dockerfs()
        container.exec_run.return_value = MagicMock(exit_code=0, output=b"d\n")
        assert fs.is_dir("/some/dir") is True

    def test_is_dir_returns_false_for_file(self):
        fs, container = _make_dockerfs()
        container.exec_run.return_value = MagicMock(exit_code=0, output=b"f\n")
        assert fs.is_dir("/some/file") is False

    def test_is_dir_strips_whitespace(self):
        fs, container = _make_dockerfs()
        container.exec_run.return_value = MagicMock(exit_code=0, output=b"  d  \n")
        assert fs.is_dir("/some/dir") is True

    def test_is_dir_raises_on_nonzero_exit_code(self):
        fs, container = _make_dockerfs()
        container.exec_run.return_value = MagicMock(exit_code=1, output=b"error msg\n")
        with pytest.raises(Exception, match="error msg"):
            fs.is_dir("/bad/path")
