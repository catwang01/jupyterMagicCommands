import re
import textwrap

import docker
import pytest

from jupyterMagicCommands.filesystem.docker import DockerFileSystem
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem


@pytest.fixture(scope="class")
def client():
    client = docker.from_env()
    return client


@pytest.fixture(
    scope="class",
    params=[
        ("bash", "bash-test"),
        ("ubuntu", "ubuntu-test"),
        ("docker:dind", "dind-test"),
    ],
)
def container(client, request):
    imageName, containerName = request.param
    try:
        newContainer = client.containers.get(containerName)
    except docker.errors.NotFound:
        newContainer = client.containers.run(
            imageName,
            name=containerName,
            stdin_open=True,
            remove=True,
            detach=True,
            privileged=True,
        )
    yield newContainer
    # newContainer.stop()


@pytest.fixture
def fs(container) -> IFileSystem:
    fs = DockerFileSystem(container)
    return fs


class TestDockerFileSystem:
    def test_if_default_shell_can_be_detect_correctly(self, container, fs):
        if container.name == "dind-test":
            assert fs.default_shell == "sh"
        else:
            assert fs.default_shell == "bash"

    def test_check_whether_file_exists_in_container(self, tmp_path, fs):
        path = f"{tmp_path}/a/b/c"
        fs.makedirs(path)
        assert fs.exists(path) == True

    def test_write_file_to_container(self, tmp_path, container, fs):
        path = f"/{tmp_path}/app/a/b/c/test.txt"
        with fs.open(path, "w", encoding="utf8") as f:
            f.write("hello")
            f.write("hello")

        assert fs.exists(path)
        assert container.exec_run(f"cat {path}").output.decode() == "hellohello"

    def test_chdir_and_getcwd_in_container(self, tmp_path, fs):
        path = f"{tmp_path}/test"
        assert fs.getcwd() == "/"

        fs.makedirs(path)
        assert fs.exists(path) == True

        fs.chdir(path)
        assert fs.getcwd() == path

    def test_chdir_to_relative_path_and_getcwd_in_container(self, tmp_path, fs):
        path = f"{tmp_path}/test"
        assert fs.getcwd() == "/"

        fs.makedirs(path)
        assert fs.exists(path) == True

        fs.chdir(path)
        assert fs.getcwd() == path

        path2 = f"{tmp_path}/hello/world"
        fs.makedirs(path2)
        assert fs.exists(path2) == True

        fs.chdir(path2)
        assert fs.getcwd() == path2

    def test_removedirs_in_container(self, tmp_path, fs):
        path = f"{tmp_path}/app/a/b/c/test.txt"

        assert fs.exists(path) == False

        with fs.open(path, "w", encoding="utf8") as f:
            f.write("hello")
            f.write("hello")
        assert fs.exists(path) == True

        fs.removedirs(path)
        assert fs.exists(path) == False

    def test_file_append(self, tmp_path, container, fs):
        path = f"{tmp_path}/test.txt"

        with fs.open(path, "w", encoding="utf8") as f:
            f.write("hello")
        assert container.exec_run(f"cat {path}").output.decode() == "hello"

        with fs.open(path, "a", encoding="utf8") as f:
            f.write(" world")
        assert container.exec_run(f"cat {path}").output.decode() == "hello world"

        with fs.open(path, "r", encoding="utf8") as f:
            s = f.read()
        assert s == "hello world"

    def test_copy_to_container(self, tmp_path, fs):
        p = str(tmp_path / "test.txt")
        with open(p, "w", encoding="utf8") as f:
            f.write("hello world")
        fs.copy_to_container(p, p)
        assert fs.exists(p)


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
        fs.removedirs(filePath)
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
        assert captured.out == ""
        assert fs.exists(filePath) == True
        with fs.open(filePath, "r", "utf8") as f:
            assert f.read() == "hello\n"
