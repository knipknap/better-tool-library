from .. import Library, Tool

class DictSerializer():
    def __init__(self, *args, **kwargs):
        pass

    def deserialize_libraries(self):
        return [] # Not implemented

    def serialize_library(self, library):
        attrs = {}
        attrs["version"] = library.API_VERSION
        tool_refs = [{'id': t.id} for t in library.tools]
        attrs["tools"] = tool_refs
        return attrs

    def deserialize_library(self, id):
        raise NotImplemented()

    def deserialize_tools(self):
        return []

    def serialize_tool(self, tool):
        attrs = {}
        attrs["version"] = tool.API_VERSION
        attrs["id"] = tool.id
        attrs["label"] = tool.label
        attrs["shape"] = tool.shape

        attrs["parameter"] = tool.params
        return attrs

    def deserialize_tool(self, attrs):
        tool = Tool(attrs['label'],
                    attrs['shape'],
                    id=attrs['id'])
        tool.params = attrs['parameter']
        return tool
