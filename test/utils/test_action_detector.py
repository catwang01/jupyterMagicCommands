import json
from pathlib import Path
import pytest
import logging

from IPython.testing.globalipapp import get_ipython
from jupyterMagicCommands.utils.action_detector import ActionDetector

class TestObj:

    def __init__(self):
        self.user_ns = {}

@pytest.fixture
def ipython_shell():
    return TestObj()

@pytest.fixture
def logger():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)
    return logger

@pytest.fixture
def actionDetector(logger, ipython_shell):
    return ActionDetector(logger, ipython_shell)

@pytest.mark.param_file(Path(__file__).parent / 'test_detect_by_line.txt', fmt="dot")
def test_detect_by_line(ipython_shell, actionDetector, file_params):
    d = json.loads(file_params.content)
    actionDetector.detect_action_by_line(d['line'])
    assert ipython_shell.user_ns.get(d['variable'], 'None') == file_params.expected.strip()

@pytest.mark.param_file(Path(__file__).parent / 'test_detect_by_chunk.txt', fmt="dot")
def test_detect_by_chunk(ipython_shell, actionDetector, file_params):
    d = json.loads(file_params.content)
    j = actionDetector.detect_action_by_chunk(d['chunk'], d['i'])

    expected = json.loads(file_params.expected)
    expected_ns = expected['ns']
    expected_j = expected['j']
    assert j == expected_j
    result = {k: ipython_shell.user_ns.get(k, 'None') for k in expected_ns}
    assert result == expected_ns