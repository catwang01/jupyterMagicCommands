import pytest
from jupyterMagicCommands.outputters.file_outputter import FileOutputter


class TestFileOutputter:

    def test_write_creates_file_with_content(self, tmp_path):
        path = str(tmp_path / "out.txt")
        outputter = FileOutputter(path)
        outputter.write("hello")
        outputter.close()
        assert open(path).read() == "hello"

    def test_close_is_idempotent(self, tmp_path):
        path = str(tmp_path / "out.txt")
        outputter = FileOutputter(path)
        outputter.write("hello")
        outputter.close()
        outputter.close()  # should not raise
        assert open(path).read() == "hello"

    def test_file_is_closed_after_close(self, tmp_path):
        path = str(tmp_path / "out.txt")
        outputter = FileOutputter(path)
        outputter.close()
        assert outputter.file.closed

    def test_write_flushes_immediately(self, tmp_path):
        path = str(tmp_path / "out.txt")
        outputter = FileOutputter(path)
        outputter.write("flushed")
        # Read before close — flush() should have written it
        assert open(path).read() == "flushed"
        outputter.close()

    def test_multiple_writes(self, tmp_path):
        path = str(tmp_path / "out.txt")
        outputter = FileOutputter(path)
        outputter.write("hello ")
        outputter.write("world")
        outputter.close()
        assert open(path).read() == "hello world"
