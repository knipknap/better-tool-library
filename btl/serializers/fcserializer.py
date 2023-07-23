# The format that FreeCAD uses for these tool library files is unfortunately a mess:
# - Numbers are locale-dependend, e.g. decimal separator (ugh)
# - Numbers are represented according to the precision settings of the user interface
# - Numbers are represented as strings in the JSON
# - Numbers are represented with units in the JSON
# - Type interpretations are hardcoded in FreeCAD.
# Here I do my best to represent/hide these behaviors.
import os
import sys
import glob
import json
import shutil
from textwrap import dedent
from .. import Library, Shape, Tool
from ..shape import builtin_shapes
from ..fcutil import *

TOOL_DIR = 'Bit'
LIBRARY_DIR = 'Library'
SHAPE_DIR = 'Shape'
BUILTIN_SHAPE_DIR = 'resources/shapes'

TOOL_EXT = '.fctb'
LIBRARY_EXT = '.fctl'
SHAPE_EXT = '.fcstd'

class FCSerializer():
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

    def _get_shape_filenames(self):
        return sorted(glob.glob(os.path.join(self.shape_path, '*'+SHAPE_EXT)))

    def _name_from_filename(self, path):
        return os.path.basename(os.path.splitext(path)[0])

    def _get_tool_filenames(self):
        return sorted(glob.glob(os.path.join(self.tool_path, '*'+TOOL_EXT)))

    def _tool_filename_from_name(self, name):
        return os.path.join(self.tool_path, name+TOOL_EXT)

    def _shape_filename_from_name(self, name):
        return os.path.join(self.shape_path, name+SHAPE_EXT)

    def _shape_name_from_filename(self, filename):
        return os.path.splitext(filename)[0]

    def import_shape_from_file(self, filename):
        filename = os.path.abspath(filename)
        dbpath = os.path.abspath(self.path)
        parent = os.path.commonpath([dbpath])
        child = os.path.commonpath([dbpath, filename])
        if parent == child:
            return # File is already in our path
        shutil.copy(filename, self.shape_path)

    def _remove_library_by_id(self, id):
        filename = self._library_filename_from_name(id)
        os.remove(filename)

    def _get_library_ids(self):
        return [self._name_from_filename(f)
                for f in self._get_library_filenames()]

    def _get_shape_names(self):
        return [self._name_from_filename(f)
                for f in self._get_shape_filenames()]

    def _get_tool_ids(self):
        return [self._name_from_filename(f)
                for f in self._get_tool_filenames()]

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
        attrs = {}
        attrs["version"] = library.API_VERSION
        attrs["label"] = library.label

        tools = []
        for pocket, tool in library.pockets.items():
            tool_filename = self._tool_filename_from_name(tool.id)
            tool_ref = {
                'nr': pocket,
                'path': os.path.basename(tool_filename),
            }
            tools.append(tool_ref)
            self.serialize_tool(tool)
        attrs["tools"] = tools

        filename = self._library_filename_from_name(library.id)
        with open(filename, "w") as fp:
            json.dump(attrs, fp, sort_keys=True, indent=2)
        return attrs

    def deserialize_library(self, id):
        filename = self._library_filename_from_name(id)
        with open(filename, "r") as fp:
            attrs = json.load(fp)

        label = attrs.get('label', id)
        library = Library(label, id=id)
        for tool_obj in attrs['tools']:
            pocket = tool_obj['nr']
            path = tool_obj['path']
            name = self._name_from_filename(path)
            try:
                tool = self.deserialize_tool(name)
            except OSError as e:
                sys.stderr.write('WARN: skipping {}: {}\n'.format(path, e))
            else:
                pocket = int(pocket) if pocket else library.get_next_pocket()
                library.add_tool(tool, pocket)

        return library

    def deserialize_shapes(self):
        return [self.deserialize_shape(name)
                for name in self._get_shape_names()]

    def serialize_shape(self, shape):
        if shape.is_builtin():
            return
        filename = self._shape_filename_from_name(shape.name)
        shape.write_to_file(filename)

        if shape.icon:
            shape.write_icon_to_file()

    def deserialize_shape(self, name):
        filename = self._shape_filename_from_name(name)
        if name in Shape.reserved:
            if name in self._get_shape_names():
                print(dedent('''
                     Warning: Skipping loading of "{}" because "{}" is a
                     reserved name used by a builtin shape. To remove this warning,
                     delete or rename the file
                ''').format(filename, name).replace("\n", " ").strip())
            name = Shape.aliases.get(name, name)
            return builtin_shapes[name]

        #if name in Shape.reserved:
        #    return Shape(name)

        shape = Shape(name, filename)

        # Collect a list of custom properties from the Attribute object.
        attrs, properties = load_shape_properties(filename)
        shape_properties_to_shape(attrs, properties, shape)

        # Load the shape icon.
        shape.load_or_create_icon()
        return shape

    def serialize_tools(self, tools):
        for tool in tools:
            self.serialize_tool(tool)

        # Flush unused tools.
        tool_names = set(t.id for t in tools)
        for filename in self._get_tool_filenames():
            name = self._name_from_filename(filename)
            if name not in tool_names:
                os.remove(filename)

    def deserialize_tools(self):
        return [self.deserialize_tool(id)
                for id in self._get_tool_ids()]

    def serialize_tool(self, tool):
        # Prepare common parameters.
        attrs = {}
        attrs["version"] = tool.API_VERSION
        attrs["name"] = tool.label
        attrs["shape"] = tool.shape.name+SHAPE_EXT
        attrs["attribute"] = {}
        attrs["parameter"] = {}

        # Get the list of parameters that are supported by the shape. This
        # is used to find the type of each parameter.
        shape_attrs, properties = load_shape_properties(tool.shape.filename)

        # Walk through the supported properties, and copy them from the internal
        # model to the tool file representation.
        for propname, prop in properties:
            param, dvalue = shape_property_to_param(propname, shape_attrs, prop)
            value = tool.shape.get_param(param, dvalue)

            if isinstance(prop, int):
                value = str(value or 0)
            elif isinstance(prop, (float, str)):
                if value is None:
                    continue
            else:
                try:
                    prop.Value = value
                except TypeError:
                    continue
                value = prop.UserString

                # this hack is used because FreeCAD writes these parameters using comma
                # separator when run in the UI, but not when running it here. I couldn't
                # figure out where this (likely locale dependend) setting is made.
                try:
                    float(prop.Value)
                    value = value.replace('.', ',')
                except ValueError:
                    pass

            attrs["parameter"][propname] = value

        # Write everything.
        filename = self._tool_filename_from_name(tool.id)
        with open(filename, "w") as fp:
            json.dump(attrs, fp, sort_keys=True, indent=2)

        return attrs

    def deserialize_tool(self, id):
        filename = self._tool_filename_from_name(id)
        with open(filename, "r") as fp:
            attrs = json.load(fp)

        # Create a tool.
        shapename = self._shape_name_from_filename(attrs['shape'])
        shape = self.deserialize_shape(shapename)
        tool = Tool(attrs['name'], shape, id=id, filename=filename)

        # Get the list of parameters that are supported by the shape. This
        # is used to find the type of each parameter.
        shape_attrs, properties = load_shape_properties(tool.shape.filename)

        # Walk through the supported properties, and copy them from the tool
        # to the internal representation.
        for propname, prop in properties:
            value = attrs['parameter'].pop(propname, None)
            param, value = tool_property_to_param(propname, value, prop)
            shape.set_param(param, value)

        # Extract remaining parameters as strings.
        for name, value in attrs['parameter'].items():
            param, value = tool_property_to_param(name, value)
            shape.set_param(param, value)

        return tool
