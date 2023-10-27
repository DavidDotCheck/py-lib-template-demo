# py-lib-template

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](http://unlicense.org/)

`py-lib-template` is a Python library template I wrote to help me get started with new projects.
It includes an example module and test, as well as configuration for building documentation and packaging the project.
It autoconfigures the GITHUB repository and automates testing, branch protection and code coverage reporting without the need for external services.

## Installation

To get started, create a Repo from this template using the 'Use this template' button and clone it to your local machine under the new project name.
Then, navigate to the project root directory and run:

```bash
python .meta/install.py
```

This will first prompt you to select sections for your new README and CONTRIBUTING files, after it will ask for a license type.
It will then authenticate you with GITHUB and help you select all the relevant data like email, name and co.
At the end, the template will also the API to configure the repository for you.

I haven't added any error recovery to the script, so if you make a mistake or an error occurs, you'll have to revert to the initial commit and start over.
Make sure to commit your finished project after running the script.

## Running Tasks

To run a task, navigate to the root folder of the project and execute the following command:

```bash
invoke <script_name>
```

Tasks are defined in the `tasks.py` file.
Available tasks are:

- `test`: Runs the test suite.
- `docs`: Builds the project documentation.
- `package`: Packages the project for distribution.
- `clean`: Cleans the project directory of build artifacts.
- `upload`: Uploads the project to PyPI.

## Repository Configuration

By running the `meta/install.py` script, the repository is configured with the following settings:

- Tests are run on every push and pull request using GITHUB Actions.
- Code coverage is tested using GITHUB Actions.
- The `master` branch is protected and requires passing tests
- The `master` branch requires at least one approval before merging.
- Dependabot is enabled to check for outdated dependencies.

## Example Module

The `{{project.package_name}}/example_module` directory contains an `Example` class in the `example.py` file. This class is documented using docstrings, which are used to generate the project documentation.

## Example Test

The `tests/test_example_module` directory contains an `test_example.py` file with a two simple tests for the `Example` class.

## License

[MIT License](LICENSE)
