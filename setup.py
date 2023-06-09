import setuptools

setuptools.setup(
    name="JupyterMagicCommands", # distribution package  name
    version="0.0.2",
    author="ed",
    author_email="edwardelricwzx@example.com",
    description="Some useful magic commands for juypter",
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=['ipython', 'plantuml', 'pandas', 'requests', "pytest", "docker", "openai"]
)
