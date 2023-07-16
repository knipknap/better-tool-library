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

def parse_unit(value):
    return float(value.rstrip(' m').replace(',', '.')) if value else None

def format_unit(value):
    return str(value).replace('.', ',') if value else None

def int_or_none(value):
    try:
        return int(value) or None
    except TypeError:
        return None

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

    def _shape_name_from_filename(self, filename):
        return os.path.splitext(filename)[0]

    def _get_library_ids(self):
        return [self._name_from_filename(f)
                for f in self._get_library_filenames()]

    def _get_tool_ids(self):
        return [self._name_from_filename(f)
                for f in self._get_tool_filenames()]

    def _read_shape_svg_from_name(self, name):
        svg_path = os.path.join(self.shape_path, name+'.svg')
        try:
            with open(svg_path, 'rb') as fp:
                return fp.read()
        except OSError:
            return None

    def _write_shape_svg_from_name(self, name, shape_svg):
        svg_path = os.path.join(self.shape_path, name+'.svg')
        try:
            with open(svg_path, 'wb') as fp:
                return fp.write(shape_svg)
        except OSError:
            return None

    def deserialize_libraries(self):
        return [self.deserialize_library(id)
                for id in self._get_library_ids()]

    def serialize_library(self, library):
        attrs = {}
        attrs["version"] = library.API_VERSION

        # The convoluted "next_tool_id" is required due to ill-defined data structures in
        # FreeCAD tool library: Tool IDs are not unique across libraries. See also the
        # docstring for Library.fc_tool_ids.
        tools = []
        next_tool_id = 1
        if library.fc_tool_ids:
            next_tool_id = max(int(i or 0) for i in library.fc_tool_ids.values())+1
        for n, tool in enumerate(library.tools):
            fc_tool_id = library.fc_tool_ids.get(tool.id)
            if not fc_tool_id:
                fc_tool_id = next_tool_id
                next_tool_id += 1

            tool_filename = self._tool_filename_from_name(tool.id)
            tool_ref = {
                'nr': fc_tool_id,
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
        library = Library(id, id=id)
        filename = self._library_filename_from_name(id)

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
                library.tools.append(tool)
                library.fc_tool_ids[tool.id] = int(nr)
                tool.pocket = int(nr)

        return library

    def deserialize_tools(self):
        return [self.deserialize_tool(id)
                for id in self._get_tool_ids()]

    def serialize_tool(self, tool):
        attrs = {}
        attrs["version"] = tool.API_VERSION
        attrs["name"] = tool.label
        attrs["shape"] = self._shape_filename_from_name(tool.shape)
        attrs["parameter"] = tool.params.copy()
        attrs["attribute"] = {}
        if tool.shape_svg:
            self._write_shape_svg_from_name(tool.shape, tool.shape_svg)

        # Update parameters from well-known parameters.
        params = attrs['parameter']
        params['Diameter'] = '{} mm'.format(format_unit(tool.diameter))
        params['ShankDiameter'] = '{} mm'.format(format_unit(tool.shaft))
        params['Length'] = '{} mm'.format(format_unit(tool.length))
        params['Flutes'] = '{}'.format(tool.flutes or 0)
        params['Material'] = '{}'.format(tool.material or 'HSS')

        filename = self._tool_filename_from_name(tool.id)
        with open(filename, "w") as fp:
            json.dump(attrs, fp, sort_keys=True, indent=2)

        return attrs

    def deserialize_tool(self, id):
        filename = self._tool_filename_from_name(id)
        with open(filename, "r") as fp:
            attrs = json.load(fp)

        shape = self._shape_name_from_filename(attrs['shape'])
        tool = Tool(attrs['name'], shape, id=id)
        tool.shape_svg = self._read_shape_svg_from_name(shape)

        # Extract well-known parameters.
        params = attrs['parameter']
        params['diameter'] = parse_unit(params.pop('Diameter', None))
        shank = params.pop('ShankDiameter', None)
        params['shaft'] = parse_unit(params.pop('ShaftDiameter', shank))
        params['length'] = parse_unit(params.pop('Length', None))
        params['flutes'] = int_or_none(params.pop('Flutes', None))
        params['material'] = params.pop('Material', None)
        for name, value in params.items():
            tool.set_param(name, value)

        return tool
