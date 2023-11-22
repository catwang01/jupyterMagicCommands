import os
import logging
from typing import Optional

import docker
from jupyterMagicCommands.extensions.constants import JUPYTER_MAGIC_COMMAND_BASH_CURRENT_CONTAINER, EMPTY_CONTAINER_NAME

from jupyterMagicCommands.filesystem.docker import DockerFileSystem
from jupyterMagicCommands.filesystem.filesystem import FileSystem
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.utils.log import NULL_LOGGER


class FileSystemFactory:

    @classmethod
    def get_filesystem(cls, containerName: Optional[str]=None, logger: logging.Logger=NULL_LOGGER) -> Optional[IFileSystem]:

        if containerName == EMPTY_CONTAINER_NAME:
            logger.error("Trying to use an existing docker but no previously used docker container exists. Use `bash -c <container>` first")
            return None

        fs: IFileSystem
        if containerName is not None:
            client = docker.from_env()
            container = client.containers.get(containerName)
            fs = DockerFileSystem(container, logger=logger)
            os.environ[JUPYTER_MAGIC_COMMAND_BASH_CURRENT_CONTAINER] = containerName
        else:
            fs = FileSystem(logger)
        return fs
