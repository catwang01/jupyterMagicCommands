from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
import docker
import pytest
from jupyterMagicCommands.filesystem.docker import DockerFileSystem

@pytest.fixture(scope="class")
def client():
    client = docker.from_env()
    return client

@pytest.fixture
def container(client):
    containerName = "test"
    try:
        newContainer = client.containers.get(containerName)
    except docker.errors.NotFound:
        newContainer = client.containers.run('bash', name=containerName, stdin_open=True, detach=True, remove=True)
    yield newContainer 
    newContainer.stop()

@pytest.fixture
def dockerfilesystem(container) -> IFileSystem:
    fs = DockerFileSystem(container)
    return fs

class TestDockerFileSystem:
    def test_check_whether_file_exists_in_container(self, dockerfilesystem):
        dockerfilesystem.makedirs('/a/b/c')
        assert dockerfilesystem.exists('/a/b/c') == True

    def test_write_file_to_container(self, container, dockerfilesystem):
        path = '/app/a/b/c/test.txt'
        with dockerfilesystem.open(path, 'w', encoding='utf8') as f:
            f.write('hello')
            f.write('hello')
        
        assert dockerfilesystem.exists(path)
        assert container.exec_run(f'cat {path}').output.decode() == "hellohello"

    def test_chdir_and_getcwd_in_container(self, dockerfilesystem):
        path = '/test'
        assert dockerfilesystem.getcwd() == '/'

        dockerfilesystem.makedirs(path)
        assert dockerfilesystem.exists(path) == True

        dockerfilesystem.chdir(path)
        assert dockerfilesystem.getcwd() == path

    def test_chdir_to_relative_path_and_getcwd_in_container(self, dockerfilesystem):
        path = 'test'
        assert dockerfilesystem.getcwd() == '/'

        dockerfilesystem.makedirs(path)
        assert dockerfilesystem.exists(path) == True

        dockerfilesystem.chdir(path)
        assert dockerfilesystem.getcwd() == '/test'

        path2 = '/hello/world'
        dockerfilesystem.makedirs(path2)
        assert dockerfilesystem.exists(path2) == True

        dockerfilesystem.chdir(path2)
        assert dockerfilesystem.getcwd() == path2

    def test_removedirs_in_container(self, dockerfilesystem):
        path = '/app/a/b/c/test.txt'

        assert dockerfilesystem.exists(path) == False

        with dockerfilesystem.open(path, 'w', encoding='utf8') as f:
            f.write('hello')
            f.write('hello')
        assert dockerfilesystem.exists(path) == True

        dockerfilesystem.removedirs(path)
        assert dockerfilesystem.exists(path) == False
