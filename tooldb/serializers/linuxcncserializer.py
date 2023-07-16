from .. import Library, Tool

class LinuxCNCSerializer():
    def __init__(self, path, *args, **kwargs):
        self.path = path

    def get_library_ids(self):
        return []  # Not implemented

    def get_tool_ids(self):
        return []  # Not implemented

    def deserialize_libraries(self):
        return [] # Not implemented

    def serialize_library(self, library):
        with open(self.path, 'w') as fp:
            for tool in library.tools:
                fp.write("T{} P{} D{} ;{}\n".format(
                    tool.pocket,
                    tool.pocket,
                    tool.diameter,
                    tool.label
                ))

    def deserialize_library(self, id):
        raise NotImplemented()

    def deserialize_tools(self):
        # In LinuxCNC, tools cannot exist on their own outside a library.
        # So nothing to be done here.
        return []

    def serialize_tool(self, tool):
        # In LinuxCNC, tools cannot exist on their own outside a library.
        # So nothing to be done here.
        return

    def deserialize_tool(self, attrs):
        # In LinuxCNC, tools cannot exist on their own outside a library.
        # So nothing to be done here.
        return

    def dump(self):
        return # Not implemented
