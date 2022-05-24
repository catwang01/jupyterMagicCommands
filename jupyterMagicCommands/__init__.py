from . import bash_ext
from . import clickhouse_ext
from . import plantuml_ext
from . import html_ext
from . import writefile_ext
from . import pwsh_ext

def load_ipython_extension(ipython):
        for module in [bash_ext, clickhouse_ext, plantuml_ext, html_ext, writefile_ext, pwsh_ext]:
                module.load_ipython_extension(ipython)
                