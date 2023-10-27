import os
import shutil
import sys
from invoke import task, context
import subprocess


def check_package(c, package_name):
    result = c.run("pip list --format=freeze", hide=True)
    installed_packages = result.stdout.split("\n")
    return any(package_name in pkg for pkg in installed_packages)


def install_packages(c, packages):
    print(f"Installing missing packages...")
    c.run(f'pip install {" ".join(packages)}')


@task
def test(c):
    c.run("pytest tests")


@task
def docs(c):
    c.run("sphinx-apidoc -f -o docs/source {{project.package_name}}")
    c.run("sphinx-build -b html docs/source docs/build")


@task
def clean(c):
    paths = [
        "build",
        "dist",
        "docs/build",
        "docs/modules.rst",
        "docs/{{project.package_name}}.rst",
        "{{project.package_name}}.egg-info",
        ".meta",        
    ]

    for path in paths:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)


@task
def check_requirements(c):
    packages = ["setuptools", "wheel", "twine"]
    missing_packages = [pkg for pkg in packages if not check_package(c, pkg)]

    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        choice = input("Do you want to auto-install the missing packages? [y/n]: ")

        if choice.lower() == "y":
            install_packages(c, missing_packages)
        else:
            print("> Required packages are missing. Task failed.")
            sys.exit(1)
    else:
        print("All required packages are installed.")


@task(pre=[check_requirements])
def package(c):
    print("Creating distribution package...")
    c.run("python setup.py sdist bdist_wheel")
    print("Package created.")


@task(pre=[check_requirements, package])
def upload(c):
    print("Uploading package to PyPI...")
    c.run("twine upload dist/*")
    print("Package uploaded.")
