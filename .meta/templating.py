from dataclasses import dataclass
import json
import os
import pathlib
import re
from typing import Any, Dict, List, Literal, Optional, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field, root_validator, validator
from enum import Enum

from ui import ui
from userdata import PlaceholderData


# Enum for action type: replace, insert, append, prepend
class ActionType(Enum):
    REPLACE = "replace"
    INSERT = "insert"
    APPEND = "append"
    PREPEND = "prepend"


class UserPromptType(Enum):
    MULTISELECT = "multiselect"
    SELECT = "select"
    INPUT = "input"


class UserPrompt(BaseModel):
    type: UserPromptType
    message: str


class OptionType(Enum):
    FILE = "file"
    TEXT = "text"
    ARRAY_MULTILINE = "array/multiline"
    ARRAY_CONDITONAL = "array/conditional"


class Option(BaseModel):
    content: Union[str, List[str], List[Dict[str, str]], Dict[str, str], Any]
    type: OptionType
    mandatory: Optional[bool]
    position: Optional[int]
    action: Optional[ActionType]
    include: Optional[bool] = False
    meta: Optional[Dict[str, Any]] = None

    @validator("position", always=True)
    def check_position(cls, position, values):
        action = values.get("action")
        if action == ActionType.INSERT and position is None:
            raise ValueError("Position can only be set if action is insert.")
        return position


class Template(BaseModel):
    name: str
    path: str
    json_file: str
    default_action: ActionType = Field(..., alias="default-action")
    user_prompt: UserPrompt = Field(..., alias="user-prompt")
    options: Dict[str, Option]

    @root_validator()
    def check_options_and_user_prompt(cls, values):
        user_prompt = values.get("user_prompt")
        user_prompt_type = user_prompt.type if user_prompt else None

        options = values.get("options")
        default_action = values.get("default_action")

        for option_key in options:
            option = options[option_key]
            type = option.type
            content = option.content
            if option.action is None:
                option.action = default_action

            if user_prompt_type == UserPromptType.MULTISELECT and (
                default_action == ActionType.REPLACE
                or option.action == ActionType.REPLACE
            ):
                raise ValueError(
                    "Multi-select prompts cannot be used with replace actions."
                )

            if option.action == ActionType.INSERT and option.position is None:
                raise ValueError("Position must be set for insert actions.")

            if option.action == ActionType.REPLACE and option.position is not None:
                raise ValueError("Position cannot be set for replace actions.")

            if user_prompt_type == UserPromptType.SELECT and option.mandatory:
                raise ValueError(
                    "Select prompts cannot be used with mandatory options."
                )

            if type == OptionType.TEXT:
                if not isinstance(content, str):
                    raise ValueError("Content must be a string.")
            elif type == OptionType.FILE:
                if not isinstance(content, str):
                    raise ValueError("Content must be a string.")
                dir = os.path.dirname(values["json_file"])
                path = os.path.join(dir, content)
                if not os.path.isfile(path):
                    raise ValueError(f"File {path} does not exist.")
                else:
                    option.content = path
            elif type == OptionType.ARRAY_MULTILINE:
                if not isinstance(content, list):
                    raise ValueError("Content must be a list.")
                for item in content:
                    if not isinstance(item, str):
                        raise ValueError("Content must be a list of strings.")
            elif type == OptionType.ARRAY_CONDITONAL:
                if not isinstance(content, list):
                    raise ValueError("Content must be a list.")
                for item in content:
                    if not (isinstance(item, dict) or isinstance(item, str)):
                        raise ValueError("Content must be a list of dicts or strings.")
                    if isinstance(item, dict) and not ("text" in item):
                        raise ValueError(
                            "Content must be a list of dicts with text key."
                        )

        return values


@dataclass
class File:
    def __init__(self, template: Template, data: str = ""):
        self.path = template.path
        self.name = template.name
        self.template = template
        self.options = template.options
        self.content = data


class Instruction:
    def __init__(
        self, instruction: str, context: Literal["condition", "load"], files: List[File]
    ):
        self.instruction = instruction
        self.context = context
        self.files = files

        self.fill: Union[None, str, List[str]] = None
        self.parse_instruction()

    def parse_instruction(self):
        if self.context == "condition":
            self.parse_condition()
        if self.context == "load":
            self.parse_load()

    def parse_condition(self):
        file_name, option = self.instruction.split("::")
        file = self.get_file(file_name)
        if file is None:
            raise ValueError(
                f"File {file_name} not found. Condition: {self.instruction}"
            )


class FileGenerator:
    def __init__(self, target_dir: str, template_dir: str):
        self.target_dir = target_dir
        self.template_dir = template_dir
        self.files: List[File] = []
        self.choices: Dict[str, str] = {}

    def generate(self):
        templates = self.load_templates()
        self.index_templates(templates)
        self.generate_files()

    def load_templates(self) -> List[Template]:
        templates = []
        print(self.template_dir)
        for json_file in pathlib.Path(self.template_dir).glob("*.json"):
            print(json_file)
            with open(json_file) as f:
                data = json.load(f)
                data["path"] = self.target_dir + "/" + data["path"]
                data["json_file"] = str(json_file)
                templates.append(Template(**data))

        return templates

    def index_templates(self, templates: List[Template]):
        for template in templates:
            self.files.append(File(template))

    def generate_files(self):
        for file in self.files:
            self.generate_file(file)

    def generate_file(self, file: File):
        # empty utf-8 file object
        template = file.template
        options: Dict[str, Option] = file.options
        print(options)
        # only non mandatory options
        selectable_options = list(
            filter(lambda x: not options[x].mandatory, options.keys())
        )

        if template.user_prompt.type == UserPromptType.SELECT:
            selected_option = ui.single_select(
                template.user_prompt.message, selectable_options
            )
            options[selected_option].include = True
            # {file: choice}
            self.choices[file.name] = options[selected_option]
        elif template.user_prompt.type == UserPromptType.MULTISELECT:
            selected_options = ui.multi_select(
                template.user_prompt.message, selectable_options
            )

            for key in options:
                option = options[key]
                if key in selected_options or option.mandatory:
                    # {file:{key: choice}}}
                    self.choices[file.name] = {key: option for key in selected_options}
                    option.include = True

        options_list = list(filter(lambda x: x.include, options.values()))
        for i in range(len(options_list)):
            option = options_list[i]
            if option.action == ActionType.INSERT:
                # move option to position
                options_list.insert(option.position, options_list.pop(i))

        print(f"Generating file {file.name}...")

        for option in options_list:
            self.generate_option(file, option)
            file.content += "\n"

        print(file.content)
        print(file.path)

    def generate_option(self, file: File, option: Option):
        if option.type == OptionType.FILE:
            with open(option.content, "r", encoding="utf-8") as f:
                file.content += f.read()
        elif option.type == OptionType.TEXT:
            file.content += option.content
        elif option.type == OptionType.ARRAY_MULTILINE:
            file.content += "\n".join(option.content)
        elif option.type == OptionType.ARRAY_CONDITONAL:
            for item in option.content:
                if isinstance(item, str):
                    file.content += item + "\n"
                else:
                    condition = item.get("if")
                    text = item.get("text") + "\n"
                    if condition is None:
                        file.content += text

                    else:
                        file_name, option_name = condition.split("::")
                        if self.get_option(file_name, option_name).include:
                            file.content += text

    def get_option(self, file_name: str, option_name: str) -> Option:
        file = self.get_file(file_name)
        return file.options[option_name]

    def get_file(self, file_name: str) -> File:
        return next(file for file in self.files if file.name == file_name)

    def get_files(self, *file_names: str) -> List[File]:
        return (
            [self.get_file(file_name) for file_name in file_names]
            if file_names
            else self.files
        )

    def write(self):
        for file in self.files:
            self.write_file(file)

    def write_file(self, file: File):
        path = file.path
        dir = os.path.dirname(path)
        os.makedirs(dir, exist_ok=True)
        # write file, overwrite if exists, utf-8 encoding
        with open(path, "w", encoding="utf-8") as f:
            f.write(file.content)

    def get_choices(self):
        return self.choices


class Placeholders:
    def __init__(self, data: PlaceholderData, choices: Optional[dict] = None):
        self.data = data
        if choices:
            self.data.choices = choices

    def _extract_placeholders(self, text: str):
        regex = r"(?<!\$)\{\{([a-zA-Z0-9_]+)(.[a-zA-Z0-9_]+)*\}\}"
        matches = re.finditer(regex, text, re.MULTILINE)
        placeholders = []
        for match in matches:
            placeholders.append(match.group())
        return placeholders

    def _get_placeholder_value(self, placeholders: str):
        # get value from self.data
        # for example: project, project.package_name, user.name, user.email
        data = self.data.dict()
        keys = placeholders.strip("{{").strip("}}").split(".")
        for key in keys:
            if key in data:
                data = data[key]
            else:
                return None
        return data

    def _replace_placeholders(self, text: str):
        placeholders = self._extract_placeholders(text)
        for placeholder in placeholders:
            value = self._get_placeholder_value(placeholder)
            # check if not string and __str__ method exists
            if not hasattr(value, "__str__"):
                raise ValueError(
                    f"Placeholder {placeholder} has no string representation."
                )
            else:
                value = str(value)
            if value is not None:
                text = text.replace(placeholder, value)
            else:
                raise ValueError(f"No value found for placeholder string {placeholder}")
        return text

    def check_path(self, path: pathlib.Path):
        INCLUDE_PATHS = os.environ.get("INCLUDE_PATHS").split(",")
        relative_path = path.relative_to(pathlib.Path(__file__).parent.parent)
        if str(relative_path) in INCLUDE_PATHS:
            return True
        for part in path.parts:
            if part.startswith(".") or part.startswith("_"):
                return False
        return True

    def replace(self):
        # use pathlib glob to go through all files, directories and subdirectories in the parent directory
        parent_dir = pathlib.Path(__file__).parent.parent
        paths = parent_dir.glob("**/*")
        paths = list(paths)
        include_paths = os.environ.get("INCLUDE_PATHS").split(",")
        include_paths = map(lambda x: parent_dir / x, include_paths)
        paths.extend(include_paths)
        for path in paths:
            if path.is_dir() or path.is_file():
                if not self.check_path(path):
                    continue

                if path.is_dir():
                    new_dir = self._replace_placeholders(path.name)
                    path.rename(path.parent / new_dir)

                elif path.is_file():
                    new_name = self._replace_placeholders(path.name)
                    path = path.rename(path.parent / new_name)

                    with open(path, "r", encoding="utf-8") as f:
                        text = f.read()
                    text = self._replace_placeholders(text)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(text)
