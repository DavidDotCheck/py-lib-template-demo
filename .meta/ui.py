from typing import List
from prompt_toolkit.shortcuts import (
    radiolist_dialog,
    input_dialog,
    checkboxlist_dialog,
    message_dialog,
)

class UI:
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

    def input(self, message: str, default: str = ""):
        return input_dialog(title="Input", text=message, default=default).run()

    def prompt(self, message: str, ok_text: str = "Ok"):
        return message_dialog(title="Prompt", text=message, ok_text=ok_text).run()

ui = UI()
