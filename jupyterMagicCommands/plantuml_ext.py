from IPython.display import Image
from io import StringIO
from IPython.core.magic import register_cell_magic
from plantuml import PlantUML

@register_cell_magic
def plantuml(line, cell):
    url = 'http://www.plantuml.com/plantuml/img/'
    processor = PlantUML(url)
    sio = StringIO(cell)
    text = sio.read()
    img = processor.processes(text)
    return Image(img)

def load_ipython_extension(ipython):
    ipython.register_magic_function(plantuml, 'cell')