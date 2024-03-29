import setuptools
from tools import get_version

setuptools.setup(
    name="JupyterMagicCommands", # distribution package  name
    version=get_version(),
    author="ed",
    author_email="edwardelricwzx@example.com",
    description="Some useful magic commands for juypter",
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=['ipython', 
                    'plantuml', 
                    'jupyter_ui_poll',
                    'pandas', 
                    'requests', 
                    "pytest",
                    "docker", 
                    "openai", 
                    "ipydrawio[all]"]
)
