# venv_manager.py

import os
import sys
import subprocess
from utils import execute_venv
from ui import ui


def venv():
    meta_dir = os.path.dirname(os.path.realpath(__file__))
    project_dir = os.path.dirname(meta_dir)

    # uninstall all dependencies from meta_dir's requirements.txt in the venv
    path_to_requirements = os.path.join(meta_dir, "requirements.txt")
    execute_venv(
        f"pip uninstall -r {path_to_requirements} -y"
    )

    # install all dependencies from project_dir's requirements-dev.txt in the venv
    path_to_requirements = os.path.join(project_dir, "requirements-dev.txt")
    execute_venv(f"pip install -r {path_to_requirements}")


NOTIFICATION_TEXT = """
Please make sure to select the .venv directory as your interpreter in your IDE:
- For VSCode: Press Ctrl+Shift+P, then type "Python: Select Interpreter."
- For PyCharm: Navigate to File > Settings > Project: [Your Project Name] > Python Interpreter.

For other IDEs, check out the specific documentation.

Alternatively, you can either activate the virtual environment manually with these terminal commands:
- Windows: `.venv\Scripts\activate`
- Linux/Mac: `source .venv/bin/activate`
Or configure your terminal to activate the environment automatically.
"""

PROJECT_TEXT = """
You can now start working on your project. The following invoke tasks are available:
- `invoke test`: Run tests
- `invoke docs`: Build documentation
- `invoke clean`: Remove temporary files
- `invoke package`: Build a source distribution and a wheel
- `invoke publish`: Publish the package to PyPI
"""

FEEDBACK_TEXT = """
Did you find this template useful?
If yes, a star on GitHub would be much appreciated.
Have issues or suggestions?
Please open an issue at: https://github.com/DavidDotCheck/py-lib-template
"""


def user_notification():
    ui.prompt(NOTIFICATION_TEXT, "Got it")
    ui.prompt(PROJECT_TEXT, "Thanks")
    ui.prompt(FEEDBACK_TEXT, "Done")

def clean():
    subprocess.run(["invoke", "clean"], check=True)