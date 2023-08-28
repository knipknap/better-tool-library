import os
import glob
from .. import Library, Tool

class Serializer():
    NAME = None
    LIBRARY_EXT = None

    def __init__(self, *args, **kwargs):
        raise NotImplemented

    def serialize_machines(self, machines):
        # Should do nothing if not supported.
        return

    def deserialize_machines(self):
        # Should return nothing if not supported.
        return []

    def serialize_machine(self, machine):
        # Should do nothing if not supported.
        return

    def deserialize_machine(self, attrs):
        raise NotImplemented

    def serialize_libraries(self, libraries):
        # Should do nothing if not supported.
        return

    def deserialize_libraries(self):
        # Should return nothing if not supported.
        return []

    def serialize_library(self, library, filename=None):
        # Should do nothing if not supported.
        return

    def deserialize_library(self, id):
        raise NotImplemented

    def deserialize_shapes(self):
        # Should return nothing if not supported.
        return []

    def serialize_shape(self, shape):
        # Should do nothing if not supported.
        return

    def deserialize_shape(self, attrs):
        # Should do nothing if not supported.
        return

    def serialize_tools(self, tools):
        # Should do nothing if not supported.
        return

    def deserialize_tools(self):
        # Should return nothing if not supported.
        return []

    def serialize_tool(self, tool):
        # Should do nothing if not supported.
        return

    def deserialize_tool(self, attrs):
        # Should do nothing if not supported.
        return
