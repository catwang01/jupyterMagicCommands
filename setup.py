import setuptools
from tools import get_version

setuptools.setup(
    name="JupyterMagicCommands",  # distribution package  name
    version=get_version(),
    author="ed",
    author_email="edwardelricwzx@example.com",
    description="Some useful magic commands for juypter",
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    python_requires=">=3.8",
    install_requires=[
        "ipython",
        "plantuml",
        "jupyter_ui_poll",
        "pandas",
        "requests",
        "pytest",
        "docker",
        "openai==1.35.0",
        "ipydrawio[all]",
        "urllib3==1.26.18",
        "overrides"
    ],
)
