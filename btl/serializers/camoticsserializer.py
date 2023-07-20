import os
import glob
import json
from .. import Library, Tool

SHAPEMAP = {
    "ballend": "Ballnose",
    "endmill": "Cylindrical",
    "v-bit": "Conical",
    "chamfer": "Snubnose",
}
SHAPEMAP_REVERSE = dict((v, k) for k, v in SHAPEMAP.items())

tooltemplate = {
    "units": "metric",  # Imperial is stupid, so don't use it
    "shape": "Cylindrical",
    "length": 10,
    "diameter": 3.125,
    "description": "",
}

LIBRARY_EXT='.ctbl'

class CamoticsSerializer():
    def __init__(self, path, *args, **kwargs):
        self.path = path
        self._init_tool_dir()

    def _init_tool_dir(self):
        if os.path.exists(self.path) and not os.path.isdir(self.path):
            raise ValueError(repr(self.path) + ' is not a directory')

        # Create subdir if it does not yet exist.
        os.makedirs(self.path, exist_ok=True)

    def _library_filename_from_id(self, id):
        return os.path.join(self.path, id+LIBRARY_EXT)

    def _library_filename_from_library(self, library):
        return self._library_filename_from_id(library.id)

    def _get_library_ids(self):
        files = glob.glob(os.path.join(self.path, '*'+LIBRARY_EXT))
        return sorted(os.path.basename(os.path.splitext(f)[0])
                      for f in files if os.path.isfile(f))

    def _remove_library_by_id(self, id):
        filename = self._library_filename_from_id(id)
        os.remove(filename)

    def serialize_libraries(self, libraries):
        existing = set(self._get_library_ids())
        for library in libraries:
            self.serialize_library(library)
            if library.id in existing:
                existing.remove(library.id)
        for id in existing:
            self._remove_library_by_id(id)

    def deserialize_libraries(self):
        return [self.deserialize_library(id)
                for id in self._get_library_ids()]

    def serialize_library(self, library):
        toollist = {}

        for tool in library.get_tools():
            toolitem = tooltemplate.copy()
            toolitem["diameter"] = tool.shape.get_param('diameter') or 2
            toolitem["description"] = tool.label
            toolitem["length"] = tool.shape.get_param('length') or 10
            toolitem["shape"] = SHAPEMAP.get(tool.shape.name, "Cylindrical")
            toollist[tool.pocket] = toolitem

        lib_filename = self._library_filename_from_library(library)
        with open(lib_filename, 'w') as fp:
            fp.write(json.dumps(toollist, indent=2))

    def deserialize_library(self, id):
        lib_filename = self._library_filename_from_id(id)
        with open(lib_filename, "r") as fp:
            data = json.load(fp)

        library = Library(id, id=id)
        for pocket, toolitem in data.items():
            shape = SHAPEMAP_REVERSE.get(toolitem["shape"], 'endmill')
            tool = Tool(toolitem["description"], shape)
            tool.diameter = float(toolitem["diameter"])
            tool.length = float(toolitem["length"])
            tool.pocket = pocket
            library.add_tool(tool)

        return library

    def deserialize_shapes(self):
        # In Camotics, shapes cannot exist on their own outside a library.
        # So nothing to be done here.
        return []

    def serialize_shape(self, shape):
        # In Camotics, shapes cannot exist on their own outside a library.
        # So nothing to be done here.
        return

    def deserialize_shape(self, attrs):
        # In Camotics, shapes cannot exist on their own outside a library.
        # So nothing to be done here.
        raise NotImplemented

    def serialize_tools(self, tools):
        # In Camotics, tools cannot exist on their own outside a library.
        # So nothing to be done here.
        return

    def deserialize_tools(self):
        # In Camotics, tools cannot exist on their own outside a library.
        # So nothing to be done here.
        return []

    def serialize_tool(self, tool):
        # In Camotics, tools cannot exist on their own outside a library.
        # So nothing to be done here.
        return

    def deserialize_tool(self, attrs):
        # In Camotics, tools cannot exist on their own outside a library.
        # So nothing to be done here.
        raise NotImplemented
