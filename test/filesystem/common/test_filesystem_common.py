from jupyterMagicCommands.filesystem.fileSystemMode import FileSystemMode


class TestFileSystemCommonOperation:

    def test_read_and_write_mode(self, tmp_path, dockerfs):
        path = f"{tmp_path}/test.txt"

        with dockerfs.open(path, 'w', encoding='utf8') as f:
            f.write("hello")
        
        assert dockerfs.get_mode(path).to_decimal() == 0o644
        dockerfs.chmod(path, FileSystemMode(0o777))
        assert dockerfs.get_mode(path).to_decimal() == 0o777