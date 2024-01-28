from pathlib import Path

import nbformat
from IPython.display import display
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


def get_target_diagram(xml, target_name):
    for diagram in xml:
        name = diagram.attrib.get("name")
        if name == target_name:
            return diagram


def get_xml(notebook):
    json = nbformat.read(notebook, as_version=nbformat.NO_CONVERT)
    xmlStr = json.metadata.get("@deathbeds/ipydrawio", {}).get("xml", "")
    xml = etree.XML(xmlStr)
    return xml


def drawio_image(target_name, display_options=None):
    notebook = get_current_notebook()
    xml = get_xml(notebook)
    target_diagram = get_target_diagram(xml, target_name)
    xml_str = get_xmfile_to_show(xml, target_diagram)
    display_drawio(xml_str, metadata={MIMETYPE: display_options or {}})
