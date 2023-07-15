# -*- coding: utf-8 -*-
import os
import uuid as UUID

class ToolDB(object):
    def __init__(self):
        self.libraries = dict() # maps library ID to Library
        self.tools = dict()  # maps tool ID to Tool

    def get_library_ids(self, serializer):
        return serializer.get_library_ids()

    def get_library_by_id(self, id):
        return self.libraries[id]

    def get_libraries(self):
        return self.libraries.values()

    def get_tool_ids(self, serializer):
        return serializer.get_tool_ids()

    def get_tool_by_id(self, id):
        return self.tools[id]

    def get_tools(self):
        return self.tools.values()

    def add_tool(self, tool, library=None):
        assert tool.id is not None
        self.tools[tool.id] = tool
        if library:
           library.tools.append(tool)

    def serialize_libraries(self, serializer):
        for library in self.libraries.values():
            serializer.serialize_library(library)

    def deserialize_libraries(self, serializer):
        self.libraries = dict()
        for id in serializer.get_library_ids():
            library = serializer.deserialize_library(id)
            self.libraries[library.id] = library
            for tool in library.tools:
                if tool.id not in self.tools:
                    self.tools[tool.id] = tool

    def serialize_tools(self, serializer):
        for tool in self.tools.values():
            serializer.serialize_tool(tool)

    def deserialize_tools(self, serializer):
        for id in serializer.get_tool_ids():
            self.add_tool(serializer.deserialize_tool(id))

    def serialize(self, serializer):
        self.serialize_libraries(serializer)
        self.serialize_tools(serializer)

    def deserialize(self, serializer):
        self.deserialize_libraries(serializer)
        self.deserialize_tools(serializer)

    def dump(self, serializer):
        data = serializer.dump()
