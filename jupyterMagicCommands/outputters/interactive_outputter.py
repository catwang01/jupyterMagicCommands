from jupyter_ui_poll import ui_events
import ipywidgets as widgets
from jupyterMagicCommands.outputters.abstract_outputter import AbstractOutputterReadCB
from jupyterMagicCommands.outputters.abstract_outputter import AbstractOutputter, EmptyOutputterReadCB


from IPython.display import display


class InteractiveOutputter(AbstractOutputter):

    def __init__(self):
        self.ui = ui_events()
        self.poll = self.ui.__enter__()
        self.out = widgets.Output()
        self.text = widgets.Text(placeholder='input')
        self.sendEnterWidget = widgets.ToggleButtons(
            options=['Send Enter', "Don't send enter"],
            description='Send enter?:',
            disabled=False,
        )
        self.read_cb: AbstractOutputterReadCB = EmptyOutputterReadCB()
        display(widgets.VBox([self.out, self.text, self.sendEnterWidget]))

    def register_read_callback(self, cb) -> None:
        self.read_cb = cb
        def wrapped_cb(widget):
            if self.sendEnterWidget.value == 'Send Enter':
                cb(widget.value + '\n')
            else:
               cb(widget.value)
        self.text.on_submit(wrapped_cb)

    def write(self, s):
        self.out.append_stdout(s)

    def handle_read(self):
        self.poll(10000)