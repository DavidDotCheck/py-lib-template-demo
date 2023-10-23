# {{project.package_name}}/example_module/example.py
# Author: {{project.author}} <{{project.email}}>

class Example:
    """This is an example class.

    The purpose of this class is to demonstrate how to create a class in Python, run tests on it, and document it.

    Attributes:
        name (str): The name of the example.
    """

    def __init__(self, name="Example"):
        """The constructor for the Example class.

        Args:
            name (str): The name of the example.
        """
        self.name = name

    def print_name(self):
        """Prints the name of the example."""
        print(self.name)

    def __str__(self):
        return self.name
