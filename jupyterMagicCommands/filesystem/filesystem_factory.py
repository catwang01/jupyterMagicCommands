import logging
from typing import Optional

import docker

from jupyterMagicCommands.filesystem.docker import DockerFileSystem
from jupyterMagicCommands.filesystem.filesystem import FileSystem
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.utils.log import NULL_LOGGER


class FileSystemFactory:

    @classmethod
    def get_filesystem(cls, containerName: Optional[str]=None, logger: logging.Logger=NULL_LOGGER) -> IFileSystem:
        fs: IFileSystem
        if containerName is not None:
            client = docker.from_env()
            container = client.containers.get(containerName)
            fs = DockerFileSystem(container, logger=logger)
        else:
            fs = FileSystem(logger)
        return fs

