from dataclasses import dataclass
import json
import os
import pathlib
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, root_validator, validator
from enum import Enum
from prompt_toolkit.shortcuts import (
    radiolist_dialog,
    input_dialog,
    checkboxlist_dialog,
    message_dialog,
)


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

    @root_validator(pre=False)
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

    def run(self):
        print("Running file generator...")
        templates = self.load_templates()
        print(templates)
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
            selected_option = self.single_select(
                template.user_prompt.message, selectable_options
            )
            options[selected_option].include = True
        elif template.user_prompt.type == UserPromptType.MULTISELECT:
            selected_options = self.multi_select(
                template.user_prompt.message, selectable_options
            )

            for key in options:
                option = options[key]
                if key in selected_options or option.mandatory:
                    option.include = True

        options = list(filter(lambda x: x.include, options.values()))
        for i in range(len(options)):
            option = options[i]
            if option.action == ActionType.INSERT:
                # move option to position
                options.insert(option.position, options.pop(i))

        print(f"Generating file {file.name}...")

        for option in options:
            self.generate_option(file, option)
            file.content += "\n"

        print(file.content)
        print(file.path)

    def generate_option(self, file: File, option: Option):
        if option.type == OptionType.FILE:
            with open(option.content) as f:
                file.content += f.read()
        elif option.type == OptionType.TEXT:
            file.content += option.content
        elif option.type == OptionType.ARRAY_MULTILINE:
            file.content += "\n".join(option.content)
        elif option.type == OptionType.ARRAY_CONDITONAL:
            for item in option.content:
                if isinstance(item, str):
                    file.content += item
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

    def multi_select(self, message: str, options: List[str]):
        # Open a prompt where the user can select multiple options using prompts_toolkit:

        formatted_options = [(option, option) for option in options]
        # Open prompt
        selected_values = checkboxlist_dialog(
            title="Select options",
            text=message,
            values=formatted_options,
        ).run()

        return selected_values

    def single_select(self, message: str, options: List[str]):
        # Open a prompt where the user can select multiple options using prompts_toolkit:

        formatted_options = [(option, option) for option in options]
        # Open prompt
        selected_value = radiolist_dialog(
            title="Select option",
            text=message,
            values=formatted_options,
        ).run()

        return selected_value


if __name__ == "__main__":
    generator = FileGenerator("target", ".meta/configuration/files")
    generator.run()
