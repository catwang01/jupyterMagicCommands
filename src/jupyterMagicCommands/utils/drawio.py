import json
import logging
import re
import os
import subprocess
import tempfile
from typing import List, Optional
import ipykernel
import nbformat
from IPython.display import Image, display
from lxml import etree

from jupyterMagicCommands.utils.jupyter_client import JupyterClient

MIMETYPE = "application/x-drawio"

class DrawIO:
    def __init__(self, jupyter_client: JupyterClient, logger: Optional[logging.Logger]=None):
        self.jupyter_client = jupyter_client
        self.logger = logger

    def display_drawio(self, xml, **kwargs):
        """Send some xml to the frontend

        Get a handle to update later by calling `display_drawio` with `display_id=True`
        """
        return display({MIMETYPE: xml}, raw=True, **kwargs)

    # def get_current_ipykernel(self) -> dict:
    #     connection_file_path = ipykernel.get_connection_file()
    #     with open(connection_file_path) as f:
    #         return json.load(f)

    def get_current_kernel_id(self) -> str:
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
                break
        notebook_path = session['notebook']['path']
        content = self.jupyter_client.get_notebook_content(notebook_path, include_content=True)
        return content

    def get_xmfile_to_show(self, xml, target_diagram):
        for diagram in list(xml):
            if diagram != target_diagram:
                xml.remove(diagram)
        return etree.tostring(xml).decode()

    def list_diagram_names(self, xml) -> List[str]:
        return [diagram.attrib.get("name") for diagram in xml]

    def normalize_name(self, s: str) -> str:
        return s.lower()

    def get_target_diagram(self, xml, target_name: str):
        for diagram in xml:
            name = diagram.attrib.get("name")
            if self.normalize_name(name) == self.normalize_name(target_name):
                return diagram

    def get_xml(self, content: str) -> etree.XML:
        notebook = nbformat.reads(content, as_version=nbformat.NO_CONVERT)
        xmlStr = notebook.metadata.get("@deathbeds/ipydrawio", {}).get("xml", "")
        xml = etree.XML(xmlStr)
        return xml

    def drawio_image(self, target_name: str, display_options: Optional[dict] = None):
        self.logger.info(f"The page {target_name} is being displayed")
        processed_target_name = self.normalize_name(target_name)
        notebook_json = self.get_current_notebook_json()
        xml = self.get_xml(json.dumps(notebook_json))
        diagram_names = {self.normalize_name(name) for name in self.list_diagram_names(xml)}
        if not diagram_names:
            raise Exception("No diagram found associated to the notebook!")

        target_diagram = self.get_target_diagram(xml, processed_target_name)
        xml_str = self.get_xmfile_to_show(xml, target_diagram)
        with tempfile.TemporaryDirectory() as tempdir:
            xml_file_path = os.path.join(tempdir, 'test.xml')
            png_file_path = os.path.join(tempdir, 'test.xml.png')
            if processed_target_name not in diagram_names:
                print(f"Not a valid diagram '{processed_target_name}'. The valid diagram names are {', '.join(diagram_names)}")
                return
            with open(xml_file_path, 'w') as f:
                f.write(xml_str)
            cmd = f"docker run --rm -v {tempdir}:/files b1f6c1c4/draw.io-export png; exit 0"
            ret = subprocess.check_output(["/bin/bash", "-c", cmd], stderr=subprocess.STDOUT)
            display(Image(filename=png_file_path))

        # self.display_drawio(xml_str, metadata={MIMETYPE: display_options or {}})
