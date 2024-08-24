from enum import Enum
import logging
from typing import Optional

from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell
from lark import Lark, Transformer

from jupyterMagicCommands.utils.log import NULL_LOGGER

class LoggingCommandTransformer(Transformer):
    
    def start(self, children):
        parameters = children[1] if children[1] else []
        return {
            "action_name": children[0],
            "parameters":  {
                parameter["parameter_name"]: parameter["parameter_value"] 
                    for parameter in parameters
            },
            "value": children[2] if len(children) == 3 and children[2] else None
        }
    
    def action_name(self, children):
        return ".".join(children)
    
    def ANYCONTENT(self, item):
        return item.value
    
    def IDENTIFIER(self, item):
        return item.value
    
    def single_parameter_assignment(self, item):
        return  { child.data: child.children[0] for child in item }
    
    def parameter_assignments(self, children):
        return children
    
    def logging_command_value(self, children):
        return "".join(children)


class LoggingCommandAction(Enum):
    ACTION_SETVARIABLE = "action.setvariable"

class LoggingCommandParser:

    def __init__(self):
        self._parser = Lark(r"""
            start: "##jmc[" action_name parameter_assignments? "]" logging_command_value
            
            action_name: IDENTIFIER ("." IDENTIFIER)*
            
            parameter_assignments: single_parameter_assignment (";" single_parameter_assignment)*
            
            single_parameter_assignment: parameter_name "=" parameter_value
            
            parameter_name: IDENTIFIER
            parameter_value: IDENTIFIER
            
            logging_command_value: ANY_CONTENT?
            
            ANY_CONTENT: /.+/
            IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/

            %import common.ESCAPED_STRING
            %import common.SIGNED_NUMBER
            %import common.WS
            %ignore WS
            """)
        self._transformer = LoggingCommandTransformer()

    def parse(self, s):
        return self._transformer.transform(
            self._parser.parse(s)
        )


class ActionDetector:

    def __init__(self, logger: Optional[logging.Logger]=None, shell: Optional[InteractiveShell] = None):
        self.logger = logger or NULL_LOGGER
        self.shell = shell or get_ipython()
        self._logging_command_parser = LoggingCommandParser()

    def detect_action_by_line(self, line: str) -> None:
        i = line.find('\n') 
        if i != -1:
            self.logger.warn("Multiple lines detected, only the first line will be used. If you want to detect action in multiple lines, use detect_action_by_chunk instead")
            line = line[:i]
        self.logger.debug("Detecting action from line")
        self.logger.debug(f"{line=}")
        try:
            logging_command = self._logging_command_parser.parse(line)
        except Exception:
            self.logger.warn(f"Can't parse action from the line")
            return
        if LoggingCommandAction.ACTION_SETVARIABLE.value != logging_command.get('action_name', ""):
            self.logger.warn(f"Unknown action {logging_command.get('action_name')}")
            return
        self.logger.debug(f"{logging_command=}")
        variable = logging_command.get('parameters', {}).get('variable')
        value = logging_command.get('value')
        if variable is None:
            raise ValueError("Variable name is not provided from the line: '{line}'")
        if value is not None:
            value = value.rstrip('\r')
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
