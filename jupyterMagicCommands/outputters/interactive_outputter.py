from jupyter_ui_poll import ui_events
import ipywidgets as widgets
from jupyterMagicCommands.outputters.outputter import AbstractOutputterReadCB
from jupyterMagicCommands.outputters.outputter import AbstractOutputter, EmptyOutputterReadCB


from IPython.display import display


class InteractiveOutputter(AbstractOutputter):

    def __init__(self):
        self.ui = ui_events()
        self.poll = self.ui.__enter__()
        self.out = widgets.Output()
        self.text = widgets.Text(placeholder='input')
        self.read_cb: AbstractOutputterReadCB = EmptyOutputterReadCB()
        display(widgets.VBox([self.out, self.text]))

    def register_read_callback(self, cb) -> None:
        self.read_cb = cb
        self.text.on_submit(lambda widget: cb(widget.value))

    def write(self, s):
        self.out.append_stdout(s)

    def handle_read(self):
        self.poll(10)