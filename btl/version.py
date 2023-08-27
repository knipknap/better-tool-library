import os
import subprocess

__dir__ = os.path.dirname(__file__)

def get_version_from_git() -> str:
    try:
        output = subprocess.check_output(['git', 'describe'],
                                         stderr=subprocess.DEVNULL,
                                         cwd=__dir__)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return output.decode('ascii').strip()

def get_version_from_pkg() -> str:
    try:
        from importlib.metadata import version, PackageNotFoundError
    except ImportError:
        return None

    try:
        return version("btl")
    except PackageNotFoundError:
        return None
