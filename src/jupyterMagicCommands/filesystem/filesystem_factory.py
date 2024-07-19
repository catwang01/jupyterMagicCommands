import logging
import os
from typing import Optional

import docker
from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell

from jupyterMagicCommands.extensions.constants import (
    EMPTY_CONTAINER_NAME, JUPYTER_MAGIC_COMMAND_BASH_CURRENT_CONTAINER)
from jupyterMagicCommands.filesystem.docker import DockerFileSystem
from jupyterMagicCommands.filesystem.filesystem import FileSystem
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.outputters import (AbstractOutputterFactory,
                                             BasicFileSystemOutputterFactory,
                                             DockerFileSystemOutputterFactory)
from jupyterMagicCommands.utils.log import NULL_LOGGER


class FileSystemFactory:
    _default_shell = get_ipython()

    @classmethod
    def get_filesystem(
        cls,
        containerName: Optional[str] = None,
        shell: Optional[InteractiveShell] = None,
        logger: logging.Logger = NULL_LOGGER,
    ) -> Optional[IFileSystem]:
        if containerName == EMPTY_CONTAINER_NAME:
            logger.error(
                "Trying to use an existing docker but no previously used docker container exists. Use `bash -c <container>` first"
            )
            return None

        if shell is None:
            shell = cls._default_shell

        fs: IFileSystem
        outputterFactory: AbstractOutputterFactory
        if containerName is not None:
            client = docker.from_env()
            outputterFactory = DockerFileSystemOutputterFactory(shell)
            container = client.containers.get(containerName)
            fs = DockerFileSystem(container, outputterFactory, logger=logger)
            os.environ[JUPYTER_MAGIC_COMMAND_BASH_CURRENT_CONTAINER] = containerName
        else:
            outputterFactory = BasicFileSystemOutputterFactory(shell)
            fs = FileSystem(outputterFactory, logger)
        return fs
