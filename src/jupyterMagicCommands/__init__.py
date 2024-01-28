from IPython import get_ipython

IS_IN_JUPYTER = get_ipython() is not None
if IS_IN_JUPYTER:
    from .extensions import bash_ext
    from .extensions import clickhouse_ext
    from .extensions import plantuml_ext
    from .extensions import writefile_ext
    from .extensions import pwsh_ext
    from .extensions import cs_ext
    from .extensions import ai_ext
    from .extensions import drawio_ext
    from .version import version

    def load_ipython_extension(ipython):
        for module in [
            bash_ext,
            clickhouse_ext,
            plantuml_ext,
            writefile_ext,
            pwsh_ext,
            cs_ext,
            ai_ext,
            drawio_ext,
        ]:
            module.load_ipython_extension(ipython)
