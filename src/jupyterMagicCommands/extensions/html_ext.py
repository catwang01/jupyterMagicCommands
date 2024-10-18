from IPython.display import IFrame
from html import escape
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring


class JMCIFrame(IFrame):
    """
    An IFrame class derives from the built-in IFrame class.

    The only difference is that JMCIFrame uses srcdoc attribute instead of src attribute
    """

    iframe = """
        <iframe
            width="{width}"
            height="{height}"
            srcdoc="{src}{params}"
            frameborder="0"
            allowfullscreen
            {extras}
        ></iframe>
        """


@magic_arguments()
@argument("-w", "--width", type=str, default="100%", help="Width of the iframe")
@argument("-h", "--height", type=str, default="200px", help="Height of the iframe")
def html(line: str, cell: str):
    """
    The extension is introduced to replace the built-in html magic.

    The problem of the built-in html magic is that there is no isolation for the html rendered by the magic and the dom of the notebook page.

    The html magic in this extension renders the html in an iframe, which is isolated from the dom of the notebook page.
    """
    args = parse_argstring(html, line)
    return JMCIFrame(escape(cell), width=args.width, height=args.height)


def load_ipython_extension(ipython):
    ipython.register_magic_function(html, "cell")
