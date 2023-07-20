# -*- coding: utf-8 -*-
import os
import uuid as UUID
from itertools import chain
from .shape import Shape

class ToolDB(object):
    def __init__(self):
        self.libraries = dict() # maps library ID to Library
        self.tools = dict()  # maps tool ID to Tool
        self.shapes = dict()  # maps shape name to Shape
        self.builtin_shapes = dict()  # maps shape name to Shape

    def add_library(self, library):
        self.libraries[library.id] = library

    def get_library_by_id(self, id):
        return self.libraries[id]

    def get_libraries(self):
        return list(self.libraries.values())

    def remove_library(self, library):
        self.libraries.pop(library.id, None)

    def add_shape(self, shape):
        self.shapes[shape.name] = shape

    def load_builtin_shapes(self):
        for name in Shape.builtin:
            shape = Shape(name)
            self.builtin_shapes[shape.name] = shape

    def get_shapes(self, builtin=True):
        if builtin:
            return chain(self.builtin_shapes.values(),
                         self.shapes.values())
        return self.shapes.values()

    def get_builtin_shapes(self):
        return self.builtin_shapes.values()

    def get_custom_shapes(self):
        return self.shapes.values()

    def get_tool_by_id(self, id):
        return self.tools[id]

    def get_tools(self):
        return list(self.tools.values())

    def add_tool(self, tool, library=None):
        self.tools[tool.id] = tool
        if library:
           library.tools.append(tool)

    def remove_tool(self, tool, library=None):
        if library:
           library.remove_tool(tool)
           return
        for library in self.libraries.values():
           library.remove_tool(tool)
        self.tools.pop(tool.id, None)

    def serialize_libraries(self, serializer):
        serializer.serialize_libraries(self.libraries.values())

    def deserialize_libraries(self, serializer):
        self.libraries = dict()
        for library in serializer.deserialize_libraries():
            self.libraries[library.id] = library
            for tool in library.tools:
                if tool.id not in self.tools:
                    self.tools[tool.id] = tool

    def serialize_shapes(self, serializer):
        for shape in self.shapes.values():
            serializer.serialize_shape(shape)

    def deserialize_shapes(self, serializer):
        for shape in serializer.deserialize_shapes():
            self.add_shape(shape)

    def serialize_tools(self, serializer):
        for tool in self.tools.values():
            serializer.serialize_tool(tool)

    def deserialize_tools(self, serializer):
        for tool in serializer.deserialize_tools():
            self.add_tool(tool)

    def serialize(self, serializer):
        self.serialize_libraries(serializer)
        self.serialize_shapes(serializer)
        self.serialize_tools(serializer)

    def deserialize(self, serializer):
        self.deserialize_libraries(serializer)
        self.deserialize_shapes(serializer)
        self.deserialize_tools(serializer)

    def dump(self, unused_tools=True, summarize=False, builtin=False):
        if builtin:
             print("-----------------")
             print(" Built-in shapes")
             print("-----------------")
             for shape in self.builtin_shapes.values():
                 shape.dump(summarize=summarize)

        print("--------------")
        print(" Custom shapes")
        print("--------------")
        for shape in self.shapes.values():
            shape.dump(summarize=summarize)

        print("------------")
        print(" Libraries")
        print("------------")
        used_tools = set()
        for library in self.libraries.values():
            library.dump(summarize=summarize)
            used_tools |= set(t.id for t in library.tools)

        if not unused_tools:
            return

        print("------------")
        print("Unused tools")
        print("------------")
        for tool_id, tool in self.tools.items():
            if tool_id not in used_tools:
                tool.dump(summarize=summarize)
        else:
            print("(none)")
