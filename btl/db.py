# -*- coding: utf-8 -*-
import os
import shutil
import uuid as UUID
from itertools import chain
from .shape import Shape, builtin_shapes, hidden_builtin_shapes


class ToolDB(object):
    def __init__(self):
        self.libraries = dict() # maps library ID to Library
        self.tools = dict()  # maps tool ID to Tool
        self.shapes = dict()  # maps shape name to Shape
        self.machines = dict()  # maps machine ID to Machine

    def add_library(self, library):
        self.libraries[library.id] = library

    def get_library_by_id(self, id):
        return self.libraries[id]

    def get_libraries(self):
        return list(self.libraries.values())

    def remove_library(self, library):
        self.libraries.pop(library.id, None)

    def add_machine(self, machine):
        self.machines[machine.id] = machine

    def get_machine_by_id(self, id):
        return self.machines[id]

    def get_machines(self):
        return list(self.machines.values())

    def remove_machine(self, machine):
        self.machines.pop(machine.id, None)

    def add_shape(self, shape):
        if shape.name in Shape.reserved:
            return
        self.shapes[shape.name] = shape

    def get_shapes(self, builtin=True):
        if builtin:
            return chain(builtin_shapes.values(),
                         self.shapes.values())
        return self.shapes.values()

    def get_builtin_shapes(self, show_hidden=False):
        if show_hidden:
            return builtin_shapes.values()
        else:
            return {k: v for k, v in builtin_shapes.items()
                    if k not in hidden_builtin_shapes.keys()}.values()

    def get_custom_shapes(self):
        return self.shapes.values()

    def get_shape_by_name(self, name):
        shape = builtin_shapes.get(name)
        if shape:
            return shape
        return self.shapes.get(name)

    def get_tool_by_id(self, id):
        return self.tools[id]

    def get_tools(self):
        return list(self.tools.values())

    def tool_is_used(self, tool):
        for library in self.libraries.values():
            if library.has_tool(tool):
                return True
        return False

    def get_unused_tools(self):
        return list(t for t in self.tools.values()
                    if not self.tool_is_used(t))

    def add_tool(self, tool, library=None):
        self.tools[tool.id] = tool
        if library:
           library.add_tool(tool)

    def remove_tool(self, tool, library=None):
        if library:
           library.remove_tool(tool)
           return
        for library in self.libraries.values():
           library.remove_tool(tool)
        self.tools.pop(tool.id, None)

    def serialize_machines(self, serializer):
        serializer.serialize_machines(self.machines.values())

    def deserialize_machines(self, serializer):
        self.machines = dict()
        for machine in serializer.deserialize_machines():
            self.machines[machine.id] = machine

    def serialize_libraries(self, serializer):
        serializer.serialize_libraries(self.libraries.values())

    def deserialize_libraries(self, serializer):
        self.libraries = dict()
        for library in serializer.deserialize_libraries():
            self.libraries[library.id] = library
            for tool in library.get_tools():
                if tool.id not in self.tools:
                    self.tools[tool.id] = tool

    def serialize_shapes(self, serializer):
        for shape in self.shapes.values():
            serializer.serialize_shape(shape)

    def deserialize_shapes(self, serializer):
        for shape in serializer.deserialize_shapes():
            if shape:
                self.add_shape(shape)

    def serialize_tools(self, serializer):
        tools = self.tools.values()
        serializer.serialize_tools(tools)

    def deserialize_tools(self, serializer):
        for tool in serializer.deserialize_tools():
            if tool:
                self.add_tool(tool)

    def serialize(self, serializer):
        self.serialize_machines(serializer)
        self.serialize_libraries(serializer)
        self.serialize_shapes(serializer)
        self.serialize_tools(serializer)

    def deserialize(self, serializer):
        self.deserialize_machines(serializer)
        self.deserialize_libraries(serializer)
        self.deserialize_shapes(serializer)
        self.deserialize_tools(serializer)

    def dump(self, unused_tools=True, summarize=False, builtin=False):
        if builtin:
             print("-----------------")
             print(" Built-in shapes")
             print("-----------------")
             for shape in builtin_shapes.values():
                 shape.dump(summarize=summarize)

        print("--------------")
        print(" Custom shapes")
        print("--------------")
        for shape in self.shapes.values():
            shape.dump(summarize=summarize)

        print("------------")
        print(" Libraries")
        print("------------")
        for library in self.libraries.values():
            library.dump(summarize=summarize)

        if not unused_tools:
            return

        print("------------")
        print("Unused tools")
        print("------------")
        for tool in self.get_unused_tools():
            tool.dump(summarize=summarize)
        if not self.get_unused_tools():
            print("(none)")
