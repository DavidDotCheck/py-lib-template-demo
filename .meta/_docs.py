"""This file is used to generate the documentation for the project.
It is currently not used in the project, but can be used to generate the `docs` folder
for the project. The `docs` folder is already generated and is included in the project.
Sphinx must be installed in the virtual environment for this file to work.
"""

import os
import re
import subprocess
from utils import execute_venv


class DocInstaller:
    def __init__(self, path: str, project_name: str, author: str):
        self.path = os.path.join(os.path.dirname(os.path.realpath(__file__)), path)
        self.project_name = project_name
        self.author = author

    def install(self):
        os.makedirs(self.path, exist_ok=True)

        # run sphinx-quickstart using venv/scripts or venv/bin depending on os using execute_venv
        args = [
            "sphinx-quickstart",
            self.path,
            "--sep",
            ## project release
            "--release",
            "0.0.1",
            # language
            "--language",
            "en",
            "--project",
            self.project_name,
            "--author",
            self.author,
            "--ext-autodoc",
            "--ext-viewcode",
            "--ext-todo",
            "-q",
        ]

        execute_venv(" ".join(args))

        # Modify the conf.py file to include settings not included by sphinx-quickstart
        with open(os.path.join(self.path, "source", "conf.py"), "r+") as file:
            filedata = file.read()
            # Add the autosummary extension
            filedata = filedata.replace(
                "'sphinx.ext.todo',",
                "'sphinx.ext.todo',\n    'sphinx.ext.autosummary',",
            )

            # set the theme to readthedocs
            filedata = re.sub(
                r"html_theme = '[a-zA-Z0-9]+'",
                "html_theme = 'sphinx_rtd_theme'",
                filedata,
            )

            # enable the autosummary_generate option
            filedata = (
                f"import os\nimport sys\nsys.path.insert(0, os.path.abspath('../{self.project_name}/'))\n"
                + filedata
                + "\nautosummary_generate = True"
            )

            file.seek(0)
            file.write(filedata)
            file.truncate()


if __name__ == "__main__":
    installer = DocInstaller(
        path="docs",
        project_name="{{repo.name}}",
        author="{{project.author}}",
    )
    installer.install()
