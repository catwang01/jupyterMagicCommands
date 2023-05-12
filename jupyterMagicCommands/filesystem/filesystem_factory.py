from typing import Optional
import docker
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem

from jupyterMagicCommands.filesystem.docker import DockerFileSystem
from jupyterMagicCommands.filesystem.filesystem import FileSystem

class FileSystemFactory:

    @classmethod
    def get_filesystem(cls, containerName: Optional[str]=None) -> IFileSystem:
        fs: IFileSystem
        if containerName is not None:
            client = docker.from_env()
            container = client.containers.get(containerName)
            fs = DockerFileSystem(container)
        else:
            fs = FileSystem()
        return fs

