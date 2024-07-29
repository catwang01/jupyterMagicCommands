import os
from IPython.core.magic import register_line_magic
from IPython.core.magic_arguments import (argument, magic_arguments,
                                        parse_argstring)

from jupyterMagicCommands.utils.drawio import DrawIO
from jupyterMagicCommands.utils.jupyter_client import JupyterClient
from jupyterMagicCommands.utils.log import getLogger
from jupyterMagicCommands.utils.parser import parse_logLevel

logger = getLogger(__name__)

@magic_arguments()
@argument('-p', '--page', type=str, required=True, help="Page name to show, case-sensitive")
@argument('--url', type=str, default=os.getenv("JMC_JUPYTER_BASE_URL"), help="Base url of the jupyterlab")
@argument('--password', type=str, default=os.getenv("JMC_JUPYTER_PASSWORD"), help="Password of the jupyterlab")
@argument("--logLevel", type=parse_logLevel, default="ERROR", choices=["ERROR", "DEBUG", "INFO"])
@register_line_magic
def drawio(line):
    args = parse_argstring(drawio, line)
    if not args.url:
        raise Exception("You need to set the base url by --url option or JMC_JUPYTER_BASE_URL environment variable")
    if not args.password:
        raise Exception("You need to set the password by --password option or JMC_JUPYTER_PASSWORD environment")
    logger.setLevel(args.logLevel)
    jupyter_client = JupyterClient(
        base_url=args.url, 
        password=args.password,
        logger=logger
    )
    drawioObj = DrawIO(jupyter_client, logger)
    drawioObj.drawio_image(args.page)

def load_ipython_extension(ipython):
    ipython.register_magic_function(drawio, 'line')
