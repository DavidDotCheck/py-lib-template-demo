import os
import glob
import subprocess
import re
import sys

project_name = input("Enter the name of the project: ")
author = input("Enter your name: ")
email = input("Enter your email: ")

# rename '{project_name}' to new_name
os.rename("{project_name}", project_name)

# rename '{project_name}', {author_name}, and {author_email} in all files to new_name, new_author, and new_email.
for filename in glob.iglob("**/*", recursive=True):
    if os.path.isfile(filename):
        with open(filename, "r+") as file:
            filedata = file.read()
            filedata = filedata.replace("{project_name}", project_name)
            filedata = filedata.replace("{author_name}", author)
            filedata = filedata.replace("{author_email}", email)
            file.seek(0)
            file.write(filedata)
            file.truncate()

# install the module
installation_result = subprocess.run(["pip", "install", "-e", "."], capture_output=True)
if installation_result.returncode != 0:
    print("Installation failed!")
    print(installation_result.stderr.decode())
    sys.exit(1)
    
# Run sphinx-quickstart with the new settings in the docs folder
os.makedirs("docs", exist_ok=True)
subprocess.run(
    [
        "sphinx-quickstart",
        "docs",
        "--project",
        project_name,
        "--author",
        author,
        "--ext-autodoc",
        "--ext-viewcode",
        "--ext-todo",
        "-q",
    ]
)


# Modify the conf.py file to include settings not included by sphinx-quickstart
with open("docs/conf.py", "r+") as file:
    filedata = file.read()
    # Add the autosummary extension
    filedata = filedata.replace(
        "'sphinx.ext.todo',", "'sphinx.ext.todo',\n    'sphinx.ext.autosummary',"
    )

    # set the theme to readthedocs
    filedata = re.sub(
        r"html_theme = '[a-zA-Z0-9]+'",
        "html_theme = 'sphinx_rtd_theme'",
        filedata,
    )
    
    # enable the autosummary_generate option
    filedata = (
        f"import os\nimport sys\nsys.path.insert(0, os.path.abspath('../{project_name}/'))\n"
        + filedata
        + "\nautosummary_generate = True"
    )

    file.seek(0)
    file.write(filedata)
    file.truncate()


# Invoke docs task to generate the documentation
subprocess.run(["invoke", "docs"])


# remove this script
os.remove("configure.py")

print("Done!")
