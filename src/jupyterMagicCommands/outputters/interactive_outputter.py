from jupyter_ui_poll import ui_events
import ipywidgets as widgets
from jupyterMagicCommands.outputters.outputter_cb import AbstractOutputterReadCB, EmptyOutputterReadCB
from jupyterMagicCommands.outputters.abstract_outputter import AbstractOutputter
from overrides import override
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

    @override
    def register_read_callback(self, cb) -> None:
        self.read_cb = cb
        def wrapped_cb(widget):
            if self.sendEnterWidget.value == 'Send Enter':
                cb(widget.value + '\n')
            else:
               cb(widget.value)
        self.text.on_submit(wrapped_cb)

    @override
    def write(self, s):
        self.out.append_stdout(s)

    @override
    def handle_read(self):
        self.poll(10000)