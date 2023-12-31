import os
import glob
from .. import Library, Tool
from .serializer import Serializer

class LinuxCNCSerializer(Serializer):
    NAME = 'LinuxCNC'
    LIBRARY_EXT='.tbl'

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

    @classmethod
    def can_serialize_library(cls):
        return True

    def serialize_library(self, library, filename=None):
        if not filename:
            filename = self._library_filename_from_id(library.id)
        with open(filename, 'wb') as fp:
            for tool_no, tool in sorted(library.tool_nos.items()):
                fp.write("T{} {} D{} ;{}\n".format(
                    tool_no,
                    'P{}'.format(tool.pocket or ''),
                    tool.shape.get_diameter() or 2,
                    tool.label
                ).encode("ascii","ignore"))
