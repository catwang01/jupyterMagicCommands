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
    newContainer = client.containers.run('bash', name="test", stdin_open=True, detach=True, remove=True)
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
