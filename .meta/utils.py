import os
import subprocess


def execute_venv(command: str):
    dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    venv = os.path.join(dir, ".venv")
    win_cmd = os.path.join(venv, "Scripts", command)
    unix_cmd = os.path.join(venv, "bin", command)
    if os.name == "nt":
        subprocess.run(win_cmd, cwd=dir)
    else:
        subprocess.run(unix_cmd, cwd=dir)
