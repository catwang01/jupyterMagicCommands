import logging
import re
from typing import Optional

from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell

from jupyterMagicCommands.utils.log import NULL_LOGGER


class ActionDetector:

    def __init__(self, logger: Optional[logging.Logger]=None, shell: Optional[InteractiveShell] = None):
        self.logger = logger or NULL_LOGGER
        self.shell = shell or get_ipython()

    def detect_action_by_line(self, line: str) -> None:
        i = line.find('\n') 
        if i != -1:
            self.logger.error("Multiple lines detected, only the first line will be used. If you want to detect action in multiple lines, use detect_action_by_chunk instead")
            line = line[:i]
        template = r"^##jmc\[action.setvariable variable=(?P<variable>.*?)\](?P<value>.*)(\r)?$"
        self.logger.debug("Detecting action from line")
        self.logger.debug(f"{line=}")
        ret = re.search(template, line)
        self.logger.debug(f"{ret=}")
        if ret is None:
            return
        variable = ret.group("variable")
        value = ret.group("value")
        self.logger.info(f"Setting variable {variable} to {value}")
        self.shell.user_ns[variable] = value

    def detect_action_by_chunk(self, chunk: str, start: int) -> int:
        """Detects action from chunk of text, starting at index start, returns the index where the action ends
        """
        j = start
        n = len(chunk)
        while j < n:
            k = chunk.find('\n', j)
            if k == -1: # can't find a newline, the line is incomplete
                break
            line = chunk[j:k]
            self.logger.debug(f"{j=} {n=} {k=}, {line=}")
            j = k + 1
            self.detect_action_by_line(line)
        return j
