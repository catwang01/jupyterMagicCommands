from IPython.core.magic import register_line_magic
from IPython.core.magic_arguments import (argument, magic_arguments,
                                        parse_argstring)

from jupyterMagicCommands.utils.drawio import drawio_image

@magic_arguments()
@argument('-p', '--page', type=str, help="Page name to show")
@argument('--height', type=lambda x: str(x) + "px", default="500", help="Height")
@register_line_magic
def drawio(line):
    args = parse_argstring(drawio, line)
    display_options = {
        'height': args.height
    }
    drawio_image(args.page, display_options)

def load_ipython_extension(ipython):
    ipython.register_magic_function(drawio, 'line')
