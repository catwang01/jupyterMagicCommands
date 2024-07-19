from unittest.mock import Mock

import pytest
from jupyterMagicCommands.extensions.bash_ext import BashExtension, BashArgsNS
import logging
from jupyterMagicCommands.filesystem.dummy_filesystem import DummyFileSystem


def test_create_directory_if_not_exist():
    directory = "/tmp/test"
    args = BashArgsNS(
        create=True,
        init=False,
        cwd=directory,
    )
    fs = DummyFileSystem()
    fs.exists = Mock(return_value=False)
    fs.makedirs = Mock()
    cell = ""
    logger = logging.getLogger(__name__)
    bash = BashExtension(args, fs, cell, logger)
    bash.run()
    fs.makedirs.assert_called_once_with(directory)

def test_skip_if_directory_exists_and_init_not_specified():
    directory = "/tmp/test"
    args = BashArgsNS(
        create=True,
        init=False,
        cwd=directory,
    )
    fs = DummyFileSystem()
    fs.exists = Mock(return_value=True)
    fs.makedirs = Mock()
    cell = ""
    logger = logging.getLogger(__name__)
    bash = BashExtension(args, fs, cell, logger)
    bash.run()
    fs.makedirs.assert_not_called()

def test_throw_exception_if_no_create_flag_and_directory_not_exists():
    directory = "/tmp/test"
    args = BashArgsNS(
        create=False,
        init=False,
        cwd=directory,
    )
    fs = DummyFileSystem()
    fs.exists = Mock(return_value=False)
    cell = ""
    logger = logging.getLogger(__name__)
    bash = BashExtension(args, fs, cell, logger)
    with pytest.raises(Exception) as e:
        bash.run()


def test_no_create_directory_if_no_create_flag_specified_and_directory_exists():
    directory = "/tmp/test"
    args = BashArgsNS(
        create=False,
        init=False,
        cwd=directory,
    )
    fs = DummyFileSystem()
    fs.exists = Mock(return_value=True)
    fs.makedirs = Mock()
    cell = ""
    logger = logging.getLogger(__name__)
    bash = BashExtension(args, fs, cell, logger)
    bash.run()
    fs.makedirs.assert_not_called()
    
def test_first_remove_and_then_create_directory_if_directory_exists_and_with_init_flag():
    directory = "/tmp/test"
    args = BashArgsNS(
        create=True,
        init=True,
        cwd=directory,
    )
    fs = DummyFileSystem()
    fs.exists = Mock(return_value=True)
    fs.makedirs = Mock()
    fs.remove = Mock()
    cell = ""
    logger = logging.getLogger(__name__)
    bash = BashExtension(args, fs, cell, logger)
    bash.run()
    fs.remove.assert_called_once_with(directory)
    fs.makedirs.assert_called_once_with(directory)