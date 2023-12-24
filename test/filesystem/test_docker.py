import docker
import pytest

from jupyterMagicCommands.filesystem.docker import DockerFileSystem
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem


@pytest.fixture(scope="class")
def client():
    client = docker.from_env()
    return client

@pytest.fixture(scope="class", params=[("bash", "bash-test"), ("docker:dind", "dind-test")])
def container(client, request):
    imageName, containerName = request.param
    try:
        newContainer = client.containers.get(containerName)
    except docker.errors.NotFound:
        newContainer = client.containers.run(
            imageName, name=containerName, stdin_open=True, detach=True, remove=True
        )
    yield newContainer
    newContainer.stop()


@pytest.fixture
def dockerfilesystem(container) -> IFileSystem:
    fs = DockerFileSystem(container)
    return fs


class TestDockerFileSystem:
    def test_if_default_shell_can_be_detect_correctly(self, container, dockerfilesystem):
        if container.name == "dind-test":
            assert dockerfilesystem.default_shell == "sh"
        else:
            assert dockerfilesystem.default_shell == "bash"

    def test_check_whether_file_exists_in_container(self, tmp_path, dockerfilesystem):
        path = f"{tmp_path}/a/b/c"
        dockerfilesystem.makedirs(path)
        assert dockerfilesystem.exists(path) == True

    def test_write_file_to_container(self, tmp_path, container, dockerfilesystem):
        path = f"/{tmp_path}/app/a/b/c/test.txt"
        with dockerfilesystem.open(path, "w", encoding="utf8") as f:
            f.write("hello")
            f.write("hello")

        assert dockerfilesystem.exists(path)
        assert container.exec_run(f"cat {path}").output.decode() == "hellohello"

    def test_chdir_and_getcwd_in_container(self, tmp_path, dockerfilesystem):
        path = f"{tmp_path}/test"
        assert dockerfilesystem.getcwd() == "/"

        dockerfilesystem.makedirs(path)
        assert dockerfilesystem.exists(path) == True

        dockerfilesystem.chdir(path)
        assert dockerfilesystem.getcwd() == path

    def test_chdir_to_relative_path_and_getcwd_in_container(
        self, tmp_path, dockerfilesystem
    ):
        path = f"{tmp_path}/test"
        assert dockerfilesystem.getcwd() == "/"

        dockerfilesystem.makedirs(path)
        assert dockerfilesystem.exists(path) == True

        dockerfilesystem.chdir(path)
        assert dockerfilesystem.getcwd() == path

        path2 = f"{tmp_path}/hello/world"
        dockerfilesystem.makedirs(path2)
        assert dockerfilesystem.exists(path2) == True

        dockerfilesystem.chdir(path2)
        assert dockerfilesystem.getcwd() == path2

    def test_removedirs_in_container(self, tmp_path, dockerfilesystem):
        path = f"{tmp_path}/app/a/b/c/test.txt"

        assert dockerfilesystem.exists(path) == False

        with dockerfilesystem.open(path, "w", encoding="utf8") as f:
            f.write("hello")
            f.write("hello")
        assert dockerfilesystem.exists(path) == True

        dockerfilesystem.removedirs(path)
        assert dockerfilesystem.exists(path) == False

    def test_file_append(self, tmp_path, container, dockerfilesystem):
        path = f"{tmp_path}/test.txt"

        with dockerfilesystem.open(path, "w", encoding="utf8") as f:
            f.write("hello")
        assert container.exec_run(f"cat {path}").output.decode() == "hello"

        with dockerfilesystem.open(path, "a", encoding="utf8") as f:
            f.write(" world")
        assert container.exec_run(f"cat {path}").output.decode() == "hello world"

        with dockerfilesystem.open(path, "r", encoding="utf8") as f:
            s = f.read()
        assert s == "hello world"