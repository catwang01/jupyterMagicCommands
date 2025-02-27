from logging import Logger
import os
import re
from typing import Optional, Protocol

import ipykernel
from IPython import get_ipython

from jupyterMagicCommands.utils.jupyter_client import JupyterClient
from jupyterMagicCommands.utils.log import NULL_LOGGER


class IJupyterNotebookRetriever(Protocol):
    def get_current_kernel_id(self) -> Optional[str]: ...

    def get_current_notebook_json(self) -> dict: ...


class JupyterNotebookRetriever(IJupyterNotebookRetriever):

    def __init__(self, jupyter_client: JupyterClient, ipython=None, logger: Optional[Logger]=None):
        self.jupyter_client = jupyter_client
        self.logger = logger or NULL_LOGGER
        self.ipython = ipython or get_ipython()

    def get_current_kernel_id(self) -> Optional[str]:
        connection_file_path = ipykernel.get_connection_file()
        baseName = os.path.basename(connection_file_path)
        ret = re.search("^rik_kernel-(?P<kernel_id>.*?).json$", baseName)
        if ret is None:
            return None
        return ret.group("kernel_id")

    def get_current_notebook_json(self) -> dict:
        current_kernel_id = self.get_current_kernel_id()
        if current_kernel_id is None:
            raise Exception("No kernel_id is found")
        sessions = self.jupyter_client.get_sessions()
        for session in sessions:
            kernel_id = session.get('kernel', {}).get('id')
            if current_kernel_id == kernel_id:
                notebook_path = session['notebook']['path']
                content = self.jupyter_client.get_notebook_content(notebook_path, include_content=True)
                return content
        raise Exception("Can't find the notebook json")

    def get_current_cell_index(self):
        notebook_json = self.get_current_notebook_json()
        cell_id = self.ipython.get_parent()["metadata"]['cellId']
        for i, cell in enumerate(notebook_json["cells"]):
            if cell["id"] == cell_id:
                return  i
        return -1