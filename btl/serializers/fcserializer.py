# The format that FreeCAD uses for these tool library files is unfortunately a mess:
# - Numbers are represented according to the precision settings of the user interface
# - Numbers are represented as strings in the JSON
# - Numbers are represented with units in the JSON in a single attribute instead of separately
# - Type interpretations are hardcoded in FreeCAD
# Here I do my best to represent/hide these behaviors.
import os
import sys
import glob
import json
import shutil
import copy
from textwrap import dedent
from .. import Machine, Library, Shape, Tool
from ..shape import builtin_shapes
from ..params import Param, IntParam, FloatParam
from ..fcutil import *

TOOL_DIR = 'Bit'
LIBRARY_DIR = 'Library'
SHAPE_DIR = 'Shape'
MACHINE_DIR = 'Machine'
BUILTIN_SHAPE_DIR = 'resources/shapes'

class FCSerializer():
    NAME = 'FreeCAD'
    TOOL_EXT = '.fctb'
    LIBRARY_EXT = '.fctl'
    SHAPE_EXT = '.fcstd'
    MACHINE_EXT = '.json'

    def __init__(self, path):
        self.set_tool_dir(path)

    def set_tool_dir(self, path):
        self.path = path
        self.tool_path = os.path.join(path, TOOL_DIR)
        self.lib_path = os.path.join(path, LIBRARY_DIR)
        self.shape_path = os.path.join(path, SHAPE_DIR)
        self.machine_path = os.path.join(path, MACHINE_DIR)
        if os.path.exists(self.path) and not os.path.isdir(self.path):
            raise ValueError(repr(self.path) + ' is not a directory')

        # Create subdirs if they do not yet exist.
        subdirs = [self.tool_path, self.lib_path, self.shape_path, self.machine_path]
        for subdir in subdirs:
            os.makedirs(subdir, exist_ok=True)

    def _get_machine_filenames(self):
        return sorted(glob.glob(os.path.join(self.machine_path, '*'+self.MACHINE_EXT)))

    def _machine_filename_from_name(self, name):
        return os.path.join(self.machine_path, name+self.MACHINE_EXT)

    def _get_library_filenames(self):
        return sorted(glob.glob(os.path.join(self.lib_path, '*'+self.LIBRARY_EXT)))

    def _library_filename_from_name(self, name):
        return os.path.join(self.lib_path, name+self.LIBRARY_EXT)

    def _get_shape_filenames(self):
        return sorted(glob.glob(os.path.join(self.shape_path, '*'+self.SHAPE_EXT)))

    def _name_from_filename(self, path):
        return os.path.basename(os.path.splitext(path)[0])

    def _get_tool_filenames(self):
        return sorted(glob.glob(os.path.join(self.tool_path, '*'+self.TOOL_EXT)))

    def _tool_filename_from_name(self, name):
        return os.path.join(self.tool_path, name+self.TOOL_EXT)

    def _shape_filename_from_name(self, name):
        return os.path.join(self.shape_path, name+self.SHAPE_EXT)

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

    def _remove_machine_by_id(self, id):
        filename = self._machine_filename_from_name(id)
        os.remove(filename)

    def _get_machine_ids(self):
        return [self._name_from_filename(f)
                for f in self._get_machine_filenames()]

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

    def serialize_machines(self, machines):
        existing = set(self._get_machine_ids())
        for machine in machines:
            self.serialize_machine(machine)
            if machine.id in existing:
                existing.remove(machine.id)
        for id in existing:
            self._remove_machine_by_id(id)

    def deserialize_machines(self):
        return [self.deserialize_machine(id)
                for id in self._get_machine_ids()]

    def serialize_machine(self, machine, filename=None):
        attrs = {}
        attrs["label"] = machine.label
        attrs["max-power"] = machine.max_power.format()
        attrs["max-torque"] = machine.max_torque.format()
        attrs["peak-torque-rpm"] = machine.peak_torque_rpm.format()
        attrs["min-rpm"] = machine.min_rpm.format()
        attrs["max-rpm"] = machine.max_rpm.format()
        attrs["min-feed"] = machine.min_feed.format()
        attrs["max-feed"] = machine.max_feed.format()

        if not filename:
            filename = self._machine_filename_from_name(machine.id)
        with open(filename, "w") as fp:
            json.dump(attrs, fp, sort_keys=True, indent=2)
        return attrs

    def deserialize_machine(self, id):
        filename = self._machine_filename_from_name(id)
        with open(filename, "r") as fp:
            attrs = json.load(fp)

        max_power = FloatParam.from_value('max-power', attrs['max-power'], 'kW')
        max_torque = FloatParam.from_value('max-torque', attrs['max-torque'], 'Nm')
        peak_torque_rpm = IntParam.from_value('peak-torque-rpm', attrs['peak-torque-rpm'])
        min_rpm = IntParam.from_value('min-rpm', attrs['min-rpm'])
        max_rpm = IntParam.from_value('max-rpm', attrs['max-rpm'])
        min_feed = FloatParam.from_value('min-feed', attrs['min-feed'], 'mm/min')
        max_feed = FloatParam.from_value('max-feed', attrs['max-feed'], 'mm/min')

        label = attrs.get('label', id)
        machine = Machine(label,
                          id=id,
                          max_power=max_power.value('kW'),
                          max_torque=max_torque.value('Nm'),
                          peak_torque_rpm=peak_torque_rpm.v,
                          min_rpm=min_rpm.v,
                          max_rpm=max_rpm.v,
                          min_feed=min_feed.value('mm/min'),
                          max_feed=max_feed.value('mm/min'))

        return machine

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
        attrs["tools"] = tools

        if not filename:
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
        filename = self._shape_filename_from_name(shape.name)
        shape.write_to_file(filename)

        if shape.icon:
            shape.write_icon_to_file()

    def deserialize_shape(self, name):
        filename = self._shape_filename_from_name(name)
        if name in Shape.reserved and not os.path.exists(filename):
            print("Copying required but non-existent shape:", filename)
            name = Shape.aliases.get(name, name)
            shape = copy.deepcopy(builtin_shapes[name])
            self.serialize_shape(shape)
            return shape

        shape = Shape(name, filename)

        # Collect a list of custom properties from the Attribute object.
        properties = load_shape_properties(filename)
        shape_properties_to_shape(properties, shape)

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
        attrs["shape"] = tool.shape.name+self.SHAPE_EXT
        attrs["attribute"] = {k: v for k, v in tool.attrs.items() if v}
        attrs["parameter"] = {}

        # Get the list of parameters that are supported by the shape. This
        # is used to find the type of each parameter.
        properties = load_shape_properties(tool.shape.filename)

        # Walk through the supported properties, and copy them from the internal
        # model to the tool file representation.
        for propname, prop, enums in properties:
            param = tool.shape.get_param(propname)

            if isinstance(prop, bool):
                value = 1 if param.v else 0
            elif isinstance(prop, int):
                value = str(param.v or 0)
            elif isinstance(prop, (float, str)):
                if param.v is None:
                    continue
                value = param.v
            else:
                # FIXME: this hack is used because FreeCAD writes these parameters using comma
                # separator when run in the UI, but not when running it here. I couldn't yet
                # figure out where this (likely locale dependent) setting is made.
                value = str(param.v).replace('.', ',')
                value = value+' '+param.unit

            attrs["parameter"][propname] = value

        # Write everything.
        filename = self._tool_filename_from_name(tool.id)
        with open(filename, "w") as fp:
            json.dump(attrs, fp, sort_keys=True, indent=2)

        return attrs

    def deserialize_tool(self, id):
        filename = self._tool_filename_from_name(id)
        try:
            with open(filename, "r") as fp:
                attrs = json.load(fp)
        except json.decoder.JSONDecodeError:
            sys.stderr.write('Error: skipping invalid json file {}\n'.format(filename))
            return

        # Create a tool.
        shapename = self._shape_name_from_filename(attrs['shape'])
        shape = self.deserialize_shape(shapename)
        tool = Tool(attrs['name'], shape, id=id, filename=filename)
        tool.attrs.update(attrs.get("attribute", {}))

        # Get the list of parameters that are supported by the shape. This
        # is used to find the type of each parameter.
        properties = load_shape_properties(tool.shape.filename)

        # Walk through the supported properties, and copy them from the tool
        # to the internal representation.
        for propname, prop, enums in properties:
            value = attrs['parameter'].pop(propname, None)
            try:
                param = tool_property_to_param(propname, prop, enums, value)
            except (AttributeError, ValueError) as e:
                print(f"Ouch! Unsupported attribute '{propname}' with value '{value}' in {filename}")
                continue
            tool.shape.set_param(param.name, param)

        return tool
