import itertools
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict
from utils import execute_venv


def compare_versions(version1: str, version2: str) -> bool:
    # checks whether version1 is greater or equal to version2
    v1 = [int(x) for x in version1.split(".")]
    v2 = [int(x) for x in version2.split(".")]

    for i in range(max(len(v1), len(v2))):
        v1_val = v1[i] if i < len(v1) else 0
        v2_val = v2[i] if i < len(v2) else 0

        if v1_val > v2_val:
            return True
        elif v1_val < v2_val:
            return False
    return True  # Equal versions


def get_version_from_python(python_exe: str) -> str:
    # get the version from the python executable
    try:
        output = subprocess.check_output(
            [python_exe, "--version"], universal_newlines=True
        )
        version = output.split()[1]
        if not output:
            return None
        return version
    except:
        return None


def discover_python(min_version: str = "3.8") -> Dict[str, str]:
    # discover python versions installed on the system
    versions = {}
    current_version = sys.version_info
    if current_version >= (3, 8):
        versions[".".join(map(str, current_version[:2]))] = sys.executable
    for path in os.environ["PATH"].split(os.pathsep):
        for python_exe in Path(path).glob("python*"):
            version = get_version_from_python(str(python_exe))

            if (
                python_exe.is_file()
                and version
                and compare_versions(version, min_version)
            ):
                versions[version] = str(python_exe)

    # Linux
    for path in itertools.chain(
        Path("/usr/bin").glob("python*"),
        Path("/usr/local/bin").glob("python*"),
    ):
        version = get_version_from_python(str(python_exe))

        if python_exe.is_file() and version and compare_versions(version, min_version):
            versions[version] = python_exe

    # Windows
    for path in itertools.chain(
        Path("C:/Program Files").glob("Python*"),
        Path("C:/Program Files (x86)").glob("Python*"),
        Path("C:/").glob("Python*"),
        Path(os.path.expandvars("%APPDATA%/../Local/Programs/Python"))
        .resolve()
        .glob("Python*"),
    ):
        if path.is_dir():
            for python_exe in path.glob("python.exe"):
                version = get_version_from_python(str(python_exe))
                if (
                    python_exe.is_file()
                    and version
                    and compare_versions(version, min_version)
                ):
                    versions[version] = str(python_exe)
    return versions


def get_python_version() -> str:
    # get the latest python version
    versions = discover_python()
    if not versions:
        print("No python version found")
        exit(1)
    python_exe = sorted(versions.items())[0][1]
    return python_exe


def create_venv():
    path = os.path.dirname(os.path.realpath(__file__))
    # venv
    if not os.path.exists(os.path.join(path, "../.venv")):
        # create virtualenv with the latest python version
        python_exe = get_python_version()
        subprocess.run([python_exe, "-m", "venv", "../.venv"], cwd=path)

    # requirements.txt
    execute_venv("pip install -r .meta/requirements.txt")


if __name__ == "__main__":
    create_venv()
    # run main.py
    execute_venv("python .meta/main.py")
