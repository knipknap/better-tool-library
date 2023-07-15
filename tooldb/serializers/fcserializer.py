import os
import sys
import glob
import shutil
import json
from .dictserializer import DictSerializer
from .. import Library, Tool

TOOL_DIR = 'Bit'
LIBRARY_DIR = 'Library'
SHAPE_DIR = 'Shape'
BUILTIN_SHAPE_DIR = 'resources/shapes'

TOOL_EXT = '.fctb'
LIBRARY_EXT = '.fctl'
SHAPE_EXT = '.fcstd'

class FCSerializer(DictSerializer):
    def __init__(self, path):
        self.path = path
        self.tool_path = os.path.join(path, TOOL_DIR)
        self.lib_path = os.path.join(path, LIBRARY_DIR)
        self.shape_path = os.path.join(path, SHAPE_DIR)
        self._init_tool_dir()

    def _init_tool_dir(self):
        if os.path.exists(self.path) and not os.path.isdir(self.path):
            raise ValueError(repr(self.path) + ' is not a directory')

        # Create subdirs if they do not yet exist.
        subdirs = [self.tool_path, self.lib_path, self.shape_path]
        for subdir in subdirs:
            os.makedirs(subdir, exist_ok=True)

    def _get_library_filenames(self):
        return sorted(glob.glob(os.path.join(self.lib_path, '*'+LIBRARY_EXT)))

    def _library_filename_from_name(self, name):
        return os.path.join(self.lib_path, name+LIBRARY_EXT)

    def _name_from_filename(self, path):
        return os.path.basename(os.path.splitext(path)[0])

    def _get_tool_filenames(self):
        return sorted(glob.glob(os.path.join(self.tool_path, '*'+TOOL_EXT)))

    def _tool_filename_from_name(self, name):
        return os.path.join(self.tool_path, name+TOOL_EXT)

    def _shape_filename_from_name(self, name):
        return name+SHAPE_EXT

    def get_library_names(self):
        return [self._name_from_filename(f)
                for f in self._get_library_filenames()]

    def get_tool_names(self):
        return [self._name_from_filename(f)
                for f in self._get_tool_filenames()]

    def serialize_library(self, library):
        attrs = {}
        attrs["version"] = library.API_VERSION

        tools = []
        for tool in library.tools:
            tool_ref = {
                'nr': tool.id,
                'path': tool.name,
            }
            tools.append(tool_ref)
        attrs["tools"] = tools

        filename = self._library_filename_from_name(library.name)
        with open(filename, "w") as fp:
            json.dump(attrs, fp, sort_keys=True, indent=2)
        return attrs

    def deserialize_library(self, name):
        library = Library(None, name)

        filename = self._library_filename_from_name(name)
        with open(filename, "r") as fp:
            attrs = json.load(fp)

        for tool_obj in attrs['tools']:
            nr = tool_obj['nr']
            path = tool_obj['path']
            name = self._name_from_filename(path)
            try:
                tool = self.deserialize_tool(name)
            except Exception as e:
                sys.stderr.write('WARN: skipping {}: {}\n'.format(path, e))
            else:
                tool = self.deserialize_tool(name)
                tool.id = int(nr)
                library.add_tool(tool)

        return library

    def serialize_tool(self, tool):
        attrs = {}
        attrs["version"] = tool.API_VERSION
        attrs["name"] = tool.label
        attrs["shape"] = tool.shape

        attrs["parameter"] = tool.params
        attrs["attribute"] = {}

        filename = self._tool_filename_from_name(tool.name)
        with open(filename, "w") as fp:
            json.dump(attrs, fp, sort_keys=True, indent=2)

        return attrs

    def deserialize_tool(self, name):
        filename = self._tool_filename_from_name(name)
        with open(filename, "r") as fp:
            attrs = json.load(fp)

        tool = Tool(None,
                    name,
                    attrs['name'],
                    attrs['shape'])
        tool.params = attrs['parameter']
        return tool

    def dump(self):
        for name in self.get_library_names():
            print("--------------- Library:", name, "------------------")
            data = self.deserialize_library(name)
            data = DictSerializer.serialize_library(self, data)
            print(json.dumps(data, sort_keys=True, indent=2))

        for name in self.get_tool_names():
            print("--------------- Tool:", name, "------------------")
            data = self.deserialize_tool(name)
            data = DictSerializer.serialize_tool(self, data)
            print(json.dumps(data, sort_keys=True, indent=2))
