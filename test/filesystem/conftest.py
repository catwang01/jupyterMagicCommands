import docker
import pytest

from jupyterMagicCommands.filesystem.docker import DockerFileSystem
from jupyterMagicCommands.filesystem.filesystem import FileSystem
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem


@pytest.fixture(scope="module")
def client():
    client = docker.from_env()
    return client


@pytest.fixture(
    scope="module",
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


@pytest.fixture(scope="module")
def dockerfs(container) -> IFileSystem:
    fs = DockerFileSystem(container)
    return fs


@pytest.fixture(scope="module")
def basicfs() -> IFileSystem:
    return FileSystem()


@pytest.fixture(
    scope="module",
    params=["basicfs", "dockerfs"],
)
def fs(request, basicfs, dockerfs) -> IFileSystem:
    fixturename = request.param
    if fixturename == "basicfs":
        return basicfs
    elif fixturename == "dockerfs":
        return dockerfs
    else:
        raise Exception("Not a valid fixture name for {fixturename}")
