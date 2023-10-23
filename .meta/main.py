from dataclasses import dataclass
import json
import os
import pathlib
import re
import finalize

from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field, root_validator, validator
from enum import Enum

from userdata import UserData, PlaceholderData
from templating import Placeholders, FileGenerator
from ui import ui

ERROR_MESSAGE = """
Something is wrong with your github setup.
Please check that you have:
- Installed the app to your account
- Added the the repo you want to use to the app
"""


class App:
    def install(self):
        load_dotenv()
        generator = FileGenerator("../", "configuration/files")
        generator.generate()
        generator.write()
        choices = generator.get_choices()
        client_id = os.getenv("CLIENT_ID")
        template_data = UserData(client_id).get_data()
        if not template_data:
            ui.prompt(ERROR_MESSAGE)
            exit(1)
        replacer = Placeholders(template_data, choices)
        replacer.replace()
        finalize.venv()
        finalize.user_notification()


if __name__ == "__main__":
    App().install()
