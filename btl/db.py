# -*- coding: utf-8 -*-
import os
import uuid as UUID

class ToolDB(object):
    def __init__(self):
        self.libraries = dict() # maps library ID to Library
        self.tools = dict()  # maps tool ID to Tool

    def add_library(self, library):
        self.libraries[library.id] = library

    def get_library_by_id(self, id):
        return self.libraries[id]

    def get_libraries(self):
        return list(self.libraries.values())

    def get_tool_by_id(self, id):
        return self.tools[id]

    def get_tools(self):
        return list(self.tools.values())

    def add_tool(self, tool, library=None):
        self.tools[tool.id] = tool
        if library:
           library.tools.append(tool)

    def serialize_libraries(self, serializer):
        for library in self.libraries.values():
            serializer.serialize_library(library)

    def deserialize_libraries(self, serializer):
        self.libraries = dict()
        for library in serializer.deserialize_libraries():
            self.libraries[library.id] = library
            for tool in library.tools:
                if tool.id not in self.tools:
                    self.tools[tool.id] = tool

    def serialize_tools(self, serializer):
        for tool in self.tools.values():
            serializer.serialize_tool(tool)

    def deserialize_tools(self, serializer):
        for tool in serializer.deserialize_tools():
            self.add_tool(tool)

    def serialize(self, serializer):
        self.serialize_libraries(serializer)
        self.serialize_tools(serializer)

    def deserialize(self, serializer):
        self.deserialize_libraries(serializer)
        self.deserialize_tools(serializer)

    def dump(self, unused_tools=True):
        used_tools = set()
        for library in self.libraries.values():
            library.dump()
            used_tools |= set(t.id for t in library.tools)

        if not unused_tools:
            return

        print("------------")
        print("Unused tools")
        print("------------")
        for tool_id, tool in self.tools.items():
            if tool_id not in used_tools:
                tool.dump()
        else:
            print("(none)")
