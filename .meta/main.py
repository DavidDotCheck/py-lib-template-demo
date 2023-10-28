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

from userdata import Github, PlaceholderData
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
        generator = FileGenerator("./", ".meta/configuration/files")
        generator.generate()
        generator.write()
        choices = generator.get_choices()
        client_id = os.getenv("CLIENT_ID")
        gh = Github(client_id)
        template_data = gh.get_data()
        gh.set_repo_settings()
        if not template_data:
            ui.prompt(ERROR_MESSAGE)
            exit(1)
        replacer = Placeholders(template_data, choices)
        replacer.replace()
        finalize.venv()
        finalize.user_notification()
        finalize.clean()


if __name__ == "__main__":
    App().install()
