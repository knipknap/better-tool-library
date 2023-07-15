# -*- coding: utf-8 -*-
import os
import uuid as UUID

class ToolDB(object):
    def __init__(self):
        self.libraries = []
        self.tools = []

    def get_library_names(self, serializer):
        return serializer.get_library_names()

    def get_tool_names(self, serializer):
        return serializer.get_tool_names()

    def serialize_libraries(self, serializer):
        for library in self.libraries:
            serializer.serialize_library(library)

    def deserialize_libraries(self, serializer):
        for name in serializer.get_library_names():
            self.libraries.append(serializer.deserialize_library(name))

    def serialize_tools(self, serializer):
        for tool in self.tools:
            serializer.serialize_tool(tool)

    def deserialize_tools(self, serializer):
        for name in serializer.get_tool_names():
            self.tools.append(serializer.deserialize_tool(name))

    def serialize(self, serializer):
        self.serialize_libraries(serializer)
        self.serialize_tools(serializer)

    def deserialize(self, serializer):
        self.deserialize_libraries(serializer)
        self.deserialize_tools(serializer)

    def dump(self, serializer):
        data = serializer.dump()
