from IPython.display import Image
from io import StringIO
from plantuml import PlantUML

def plantuml(line, cell):
    url = 'http://www.plantuml.com/plantuml/img/'
    processor = PlantUML(url)
    sio = StringIO(cell)
    text = sio.read()
    img = processor.processes(text)
    return Image(img)

def load_ipython_extension(ipython):
    ipython.register_magic_function(plantuml, 'cell')