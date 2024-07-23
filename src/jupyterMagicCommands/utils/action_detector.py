import re
from typing import Optional

from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell


class ActionDetector:

    def __init__(self, logger, shell: Optional[InteractiveShell] = None):
        self.logger = logger
        self.shell = shell or get_ipython()

    def detect_action_by_line(self, line: str) -> None:
        template = r"##jmc\[action.setvariable (?P<variable>.*?)\](?P<value>.*)(\r)$"
        self.logger.debug("Detecting action from line")
        self.logger.debug(f"{line=}")
        ret = re.search(template)
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
            k = chunk[j:].find('\n')
            if k == -1: # can't find a newline, the line is incomplete
                break
            line = chunk[j:k]
            j = k + 1
            self.detect_action_by_line(line)
        return j
