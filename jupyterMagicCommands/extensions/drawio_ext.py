from pathlib import Path
import nbformat
from IPython.display import display
from lxml import etree
from IPython.core.magic import register_line_magic
from IPython.core.magic_arguments import (argument, magic_arguments,
                                        parse_argstring)

MIMETYPE = "application/x-drawio"

# this may not work
def get_current_notebook():
    this_notebook = list(Path.cwd().glob('*.ipynb'))[0]
    return this_notebook

def get_xml(notebook):
    json = nbformat.read(notebook, as_version=nbformat.NO_CONVERT)
    xmlStr = json.metadata.get('@deathbeds/ipydrawio', {}).get('xml', '')
    xml = etree.XML(xmlStr)
    return xml

def get_target_diagram(xml, target_name):
    for diagram in xml:
        name = diagram.attrib.get('name')
        if name == target_name:
            return diagram

def get_xmfile_to_show(xml, target_diagram):
    for diagram in list(xml):
        if diagram != target_diagram:
            xml.remove(diagram)
    return etree.tostring(xml).decode()

def display_drawio(xml, **kwargs):
    """Send some xml to the frontend

    Get a handle to update later by calling `display_drawio` with `display_id=True`
    """
    return display({MIMETYPE: xml}, raw=True, **kwargs)

def _drawio_image(target_name, display_options=None):
    notebook = get_current_notebook()
    xml = get_xml(notebook)
    target_diagram = get_target_diagram(xml, target_name)
    xml_str = get_xmfile_to_show(xml, target_diagram)
    display_drawio(xml_str, metadata={
        MIMETYPE: display_options or {}
    })

@magic_arguments()
@argument('-p', '--page', type=str, help="Page name to show")
@argument('-f', '--format', choices=['svg', 'drawio'], default='drawio', help="Format to show")
@argument('--height', type=lambda x: str(x) + "px", default="500", help="Height")
@register_line_magic
def drawio(line):
    args = parse_argstring(drawio, line)
    display_options = {
        'height': args.height
    }
    _drawio_image(args.page, display_options)

def load_ipython_extension(ipython):
    ipython.register_magic_function(openai_magic, 'line')
