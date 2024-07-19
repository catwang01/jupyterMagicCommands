class TestDockerFileSystem:
    def test_if_default_shell_can_be_detect_correctly(self, container, dockerfs):
        if container.name == "dind-test":
            assert dockerfs.default_shell == "sh"
        else:
            assert dockerfs.default_shell == "bash"

    def test_check_whether_file_exists_in_container(self, tmp_path, dockerfs):
        path = f"{tmp_path}/a/b/c"
        dockerfs.makedirs(path)
        assert dockerfs.exists(path) == True

    def test_write_file_to_container(self, tmp_path, container, dockerfs):
        path = f"/{tmp_path}/app/a/b/c/test.txt"
        with dockerfs.open(path, "w", encoding="utf8") as f:
            f.write("hello")
            f.write("hello")

        assert dockerfs.exists(path)
        assert container.exec_run(f"cat {path}").output.decode() == "hellohello"

    def test_chdir_and_getcwd_in_container(self, tmp_path, dockerfs):
        path = f"{tmp_path}/test"
        assert dockerfs.getcwd() == "/"

        dockerfs.makedirs(path)
        assert dockerfs.exists(path) == True

        dockerfs.chdir(path)
        assert dockerfs.getcwd() == path

    def test_chdir_to_relative_path_and_getcwd_in_container(self, tmp_path, dockerfs):
        dockerfs.chdir("/")

        path = f"{tmp_path}/test"
        assert dockerfs.getcwd() == "/"

        dockerfs.makedirs(path)
        assert dockerfs.exists(path) == True

        dockerfs.chdir(path)
        assert dockerfs.getcwd() == path

        path2 = f"{tmp_path}/hello/world"
        dockerfs.makedirs(path2)
        assert dockerfs.exists(path2) == True

        dockerfs.chdir(path2)
        assert dockerfs.getcwd() == path2

    def test_remove_in_container(self, tmp_path, dockerfs):
        path = f"{tmp_path}/app/a/b/c/test.txt"

        assert dockerfs.exists(path) == False

        with dockerfs.open(path, "w", encoding="utf8") as f:
            f.write("hello")
            f.write("hello")
        assert dockerfs.exists(path) == True

        dockerfs.remove(path)
        assert dockerfs.exists(path) == False

    def test_file_append(self, tmp_path, container, dockerfs):
        path = f"{tmp_path}/test.txt"

        with dockerfs.open(path, "w", encoding="utf8") as f:
            f.write("hello")
        assert container.exec_run(f"cat {path}").output.decode() == "hello"

        with dockerfs.open(path, "a", encoding="utf8") as f:
            f.write(" world")
        assert container.exec_run(f"cat {path}").output.decode() == "hello world"

        with dockerfs.open(path, "r", encoding="utf8") as f:
            s = f.read()
        assert s == "hello world"

    def test_copy_to_container(self, tmp_path, dockerfs):
        p = str(tmp_path / "test.txt")
        with open(p, "w", encoding="utf8") as f:
            f.write("hello world")
        dockerfs.copy_to_container(p, p)
        assert dockerfs.exists(p)
