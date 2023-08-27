from .db import ToolDB
from .library import Library
from .shape import Shape
from .tool import Tool
from .machine import Machine

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    __version__ = "unknown; Python version too old"
else:
    try:
        __version__ = version("btl")
    except PackageNotFoundError:
        __version__ = "unknown version"
