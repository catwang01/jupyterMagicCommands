import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

import nbformat
from IPython.display import display, Image
from lxml import etree

MIMETYPE = "application/x-drawio"

def display_drawio(xml, **kwargs):
    """Send some xml to the frontend

    Get a handle to update later by calling `display_drawio` with `display_id=True`
    """
    return display({MIMETYPE: xml}, raw=True, **kwargs)


# this may not work
def get_current_notebook():
    this_notebook = list(Path.cwd().glob("*.ipynb"))[0]
    return this_notebook


def get_xmfile_to_show(xml, target_diagram):
    for diagram in list(xml):
        if diagram != target_diagram:
            xml.remove(diagram)
    return etree.tostring(xml).decode()

def list_diagram_names(xml) -> List[str]:
   return [ diagram.attrib.get("name") for diagram in xml ]

def normalize_name(s: str) -> str:
    return s.lower()

def get_target_diagram(xml, target_name: str):
    for diagram in xml:
        name = diagram.attrib.get("name")
        if normalize_name(name) == normalize_name(target_name):
            return diagram


def get_xml(notebook):
    json = nbformat.read(notebook, as_version=nbformat.NO_CONVERT)
    xmlStr = json.metadata.get("@deathbeds/ipydrawio", {}).get("xml", "")
    xml = etree.XML(xmlStr)
    return xml


def drawio_image(target_name: str, display_options: Optional[dict]=None):
    processed_target_name = normalize_name(target_name)
    notebook = get_current_notebook()
    xml = get_xml(notebook)
    diagram_names = { normalize_name(name) for name in list_diagram_names(xml) }
    if processed_target_name not in diagram_names:
        print(f"Not a valid diagram '{processed_target_name}'. The valid diagram names are {', '.join(diagram_names)}")
        return
    target_diagram = get_target_diagram(xml, processed_target_name)
    xml_str = get_xmfile_to_show(xml, target_diagram)
    with tempfile.TemporaryDirectory() as tempdir:
        xml_file_path = os.path.join(tempdir, 'test.xml')
        png_file_path = os.path.join(tempdir, 'test.xml.png')
        with open(xml_file_path, 'w') as f:
            f.write(xml_str)
        s = f"""docker run --rm \
                -v {tempdir.name}:/files \
                b1f6c1c4/draw.io-export png
        """
        ret = subprocess.call(s)
        display(Image(filename=png_file_path))

    # display_drawio(xml_str, metadata={MIMETYPE: display_options or {}})