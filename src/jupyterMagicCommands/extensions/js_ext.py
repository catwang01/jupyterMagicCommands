from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.core.magic_arguments import (magic_arguments, parse_argstring, argument)
from urllib.parse import quote

from IPython.display import IFrame

@magics_class
class JSMagicCommand(Magics):

    @magic_arguments()
    @argument("-w", "--width", type=str, default="100%", help="Width of the iframe")
    @argument("-h", "--height", type=str, default="200px", help="Height of the iframe")
    @cell_magic
    def js(self, line, cell):
        args = parse_argstring(self.js, line)
        escaped = quote(cell)
        src = f"https://catwang.top/console?code={escaped}&autoRun=true&readonly=true"
        return IFrame(src=src, width=args.width, height=args.height)

def load_ipython_extension(ipython):
    ipython.register_magics(JSMagicCommand)