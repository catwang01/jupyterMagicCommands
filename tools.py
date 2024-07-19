def get_version() -> str:
    main_ns = {}
    with open('src/jupyterMagicCommands/version.py', encoding='utf8') as ver_file:
        exec(ver_file.read(), main_ns)
    if 'version' not in main_ns:
        raise Exception("Can't retrieve version information!")
    return main_ns['version']