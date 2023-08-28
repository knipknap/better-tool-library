import os
import glob
import json
from .. import Library, Tool
from .serializer import Serializer

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

class CamoticsSerializer(Serializer):
    NAME = 'Camotics'
    LIBRARY_EXT='.ctbl'

    def __init__(self, path, *args, **kwargs):
        self.set_tool_dir(path)

    def set_tool_dir(self, path):
        self.path = path
        if os.path.exists(self.path) and not os.path.isdir(self.path):
            raise ValueError(repr(self.path) + ' is not a directory')

        # Create subdir if it does not yet exist.
        os.makedirs(self.path, exist_ok=True)

    def _library_filename_from_id(self, id):
        return os.path.join(self.path, id+self.LIBRARY_EXT)

    def _library_filename_from_library(self, library):
        return self._library_filename_from_id(library.id)

    def _get_library_ids(self):
        files = glob.glob(os.path.join(self.path, '*'+self.LIBRARY_EXT))
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

    def serialize_library(self, library, filename=None):
        toollist = {}

        for pocket, tool in library.pockets.items():
            toolitem = tooltemplate.copy()
            toolitem["diameter"] = tool.shape.get_diameter() or 2
            toolitem["description"] = tool.label
            toolitem["length"] = tool.shape.get_length() or 10
            toolitem["shape"] = SHAPEMAP.get(tool.shape.name, "Cylindrical")
            toollist[pocket] = toolitem

        if not filename:
            filename = self._library_filename_from_library(library)
        with open(filename, 'w') as fp:
            fp.write(json.dumps(toollist, indent=2))

    def deserialize_library(self, id):
        lib_filename = self._library_filename_from_id(id)
        with open(lib_filename, "r") as fp:
            data = json.load(fp)

        library = Library(id, id=id)
        for pocket, toolitem in data.items():
            shape = SHAPEMAP_REVERSE.get(toolitem["shape"], 'endmill')
            tool = Tool(toolitem["description"], shape, filename=lib_filename)
            tool.diameter = float(toolitem["diameter"])
            tool.length = float(toolitem["length"])
            library.add_tool(tool, int(pocket))

        return library
