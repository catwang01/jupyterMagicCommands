import json
import logging
import os
import subprocess
import tempfile
from typing import List, Optional

import nbformat
from IPython.display import Image, display
from lxml import etree

from jupyterMagicCommands.utils.jupyterNotebookRetriever import \
    IJupyterNotebookRetriever
from jupyterMagicCommands.utils.log import NULL_LOGGER

MIMETYPE = "application/x-drawio"

class DrawIO:
    def __init__(self, jupyterNotebookRetriever: IJupyterNotebookRetriever, logger: Optional[logging.Logger]=None):
        self.jupyterNotebookRetriever = jupyterNotebookRetriever
        self.logger = logger or NULL_LOGGER

    def display_drawio(self, xml, **kwargs):
        """Send some xml to the frontend

        Get a handle to update later by calling `display_drawio` with `display_id=True`
        """
        return display({MIMETYPE: xml}, raw=True, **kwargs)

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
        notebook_json = self.jupyterNotebookRetriever.get_current_notebook_json()
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