# -*- coding: utf-8 -*-
import os
import uuid as UUID

class ToolDB(object):
    def __init__(self):
        self.libraries = set()
        self.tools = set()

    def get_library_names(self, serializer):
        return serializer.get_library_names()

    def get_library_by_name(self, name):
        for lib in self.libraries:
            if name == lib.name:
                return lib

    def get_tool_names(self, serializer):
        return serializer.get_tool_names()

    def get_tool_by_name(self, name):
        for tool in self.tools:
            if name == tool.name:
                return tool

    def _get_next_tool_id(self):
        if not self.tools:
            return 1
        max_id = max([int(t.id or 0) for t in self.tools])
        return max_id+1

    def add_tool(self, tool, library=None):
        if not tool.id:
            tool.id = self._get_next_tool_id()
        self.tools.add(tool)
        if library:
           library.tools.append(tool)

    def serialize_libraries(self, serializer):
        for library in self.libraries:
            serializer.serialize_library(library)

    def deserialize_libraries(self, serializer):
        self.libraries = []
        for name in serializer.get_library_names():
            library = serializer.deserialize_library(name)
            self.libraries.append(library)
            self.tools |= set(library.tools)

    def serialize_tools(self, serializer):
        for tool in self.tools:
            serializer.serialize_tool(tool)

    def deserialize_tools(self, serializer):
        for name in serializer.get_tool_names():
            self.add_tool(serializer.deserialize_tool(name))

    def serialize(self, serializer):
        self.serialize_libraries(serializer)
        self.serialize_tools(serializer)

    def deserialize(self, serializer):
        self.deserialize_libraries(serializer)
        self.deserialize_tools(serializer)

    def dump(self, serializer):
        data = serializer.dump()
