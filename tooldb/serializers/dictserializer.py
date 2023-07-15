from .. import Library, Tool

class DictSerializer():
    def get_library_names(self):
        return ['DummyLibrary']

    def get_tool_names(self):
        return []

    def serialize_library(self, library):
        attrs = {}
        attrs["version"] = library.API_VERSION
        tool_refs = [{'id': t.id} for t in library.tools]
        attrs["tools"] = tool_refs
        return attrs

    def deserialize_library(self, name):
        return Library(None, name)

    def serialize_tool(self, tool):
        attrs = {}
        attrs["version"] = tool.API_VERSION
        attrs["id"] = tool.id
        attrs["name"] = tool.name
        attrs["label"] = tool.label
        attrs["shape"] = tool.shape

        attrs["parameter"] = tool.params
        return attrs

    def deserialize_tool(self, attrs):
        tool = Tool(attrs['label'],
                    attrs['shape'],
                    id=attrs['id'],
                    name=attrs['name'])
        tool.params = attrs['parameter']
        return tool

    def dump(self):
        return
