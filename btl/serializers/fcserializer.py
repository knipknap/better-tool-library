# The format that FreeCAD uses for these tool library files is unfortunately a mess:
# - Numbers are locale-dependend, e.g. decimal separator (ugh)
# - Numbers are represented according to the precision settings of the user interface
# - Numbers are represented as strings in the JSON
# - Numbers are represented with units in the JSON
# - Tool IDs are not unique across libraries
# Here I do my best to represent all these behaviors.
import os
import re
import sys
import glob
import json
from .. import Library, Shape, Tool, params

TOOL_DIR = 'Bit'
LIBRARY_DIR = 'Library'
SHAPE_DIR = 'Shape'
BUILTIN_SHAPE_DIR = 'resources/shapes'

TOOL_EXT = '.fctb'
LIBRARY_EXT = '.fctl'
SHAPE_EXT = '.fcstd'

# Map FreeCAD shape file parameter names to our internal param representation.
fc_property_to_param_type = {
    'Diameter': params.Diameter,
    'ShankDiameter': params.Shaft,
    'ShaftDiameter': params.Shaft,
    'Length': params.Length,
    'Flutes': params.Flutes,
    'Material': params.Material,
    'SpindleDirection': params.SpindleDirection,
}

fc_property_unit_to_param_type = {
    'Length': params.DistanceBase,
    'Angle': params.AngleBase,
}

def _type_from_prop(propname, prop):
    if isinstance(prop, bool):
        return params.BoolBase
    elif isinstance(prop, int):
        return params.IntBase
    elif isinstance(prop, float):
        return params.FloatBase
    elif isinstance(prop, str):
        return params.Base
    elif hasattr(prop, 'Unit') \
        and prop.Unit.Type in fc_property_unit_to_param_type:
        #print("UNIT", dir(prop.Unit), prop.Unit.Type, prop.Unit.Signature)
        return fc_property_unit_to_param_type[prop.Unit.Type]
    else:
        raise NotImplementedError(
            'error: param {} with type {} is unsupported'.format(
                 propname, prop.Unit.Type))

def _tool_property_to_param(propname, value, prop=None):
    if propname in fc_property_to_param_type:   # Known type.
        param_type = fc_property_to_param_type[propname]
        param = param_type()
    else:  # Try to find type from prop.
        param_type = params.Base if prop is None else _type_from_prop(propname, prop)
        param = param_type()
        param.name = propname
        param.label = re.sub(r'([A-Z])', r' \1', propname).strip()

    if issubclass(param_type, params.DistanceBase):
        value = parse_unit(value)
    elif issubclass(param_type, params.BoolBase):
        value = bool(value or False)
    elif issubclass(param_type, params.IntBase):
        value = int_or_none(value)
    elif issubclass(param_type, params.Material):
        value = str(value)
    elif issubclass(param_type, params.Base):
        value = str(value)
    else:
        raise NotImplementedError(
            'whoops - param {} with type {} is not implemented'.format(
                 propname, param))

    return param, value

def _shape_property_to_param(propname, attrs, prop):
    param_type = _type_from_prop(propname, prop)
    if hasattr(prop, 'Unit'):
        value = prop.Value
    else:
        value = prop

    # Default can be overwritten by more specific known types.
    param_type = fc_property_to_param_type.get(propname, param_type)
    if not param_type:
        raise NotImplemented(
            'bug: param {} with type {} not supported'.format(
                 propname, prop))

    param = param_type()
    if not param.name:
        param.name = propname
        param.label = re.sub(r'([A-Z])', r' \1', propname).strip()

    #print("_shape_property_to_param()", propname, prop, param, value)

    # In case of enumerations, collect all allowed values.
    if hasattr(param, 'enum'):
        param.enum = attrs.getEnumerationsOfProperty(propname)

    return param, value

def parse_unit(value):
    return float(value.rstrip(' m').replace(',', '.')) if value else None

def format_unit(value):
    return str(value).replace('.', ',') if value else None

def int_or_none(value):
    try:
        return int(value) or None
    except TypeError:
        return None

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

    def _svg_filename_from_name(self, name):
        return os.path.join(self.shape_path, name+'.svg')

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
            except OSError as e:
                sys.stderr.write('WARN: skipping {}: {}\n'.format(path, e))
            else:
                library.tools.append(tool)
                library.fc_tool_ids[tool.id] = int(nr)
                tool.pocket = int(nr)

        return library

    def deserialize_shapes(self):
        return [self.deserialize_shape(name)
                for name in self._get_shape_names()]

    def _load_shape_properties(self, filename):
        # Load the shape file using FreeCad
        import FreeCAD
        doc = FreeCAD.open(filename)

        # Find the Attribute object.
        attrs_list = doc.getObjectsByLabel('Attributes')
        try:
            attrs = attrs_list[0]
        except IndexError:
            raise Exception(f'shape file {filename} has no "Attributes" FeaturePython object.\n'\
                          + ' Check the parameter definition in your shape file')

        properties = []
        for propname in attrs.PropertiesList:
            prop = getattr(attrs, propname)
            groupname = attrs.getGroupOfProperty(propname)
            if groupname in ('', 'Base'):
                continue
            properties.append((propname, prop))

        return attrs, properties

    def serialize_shape(self, shape):
        if shape.is_builtin():
            return
        filename = self._shape_filename_from_name(shape.name)
        shape.write_to_file(filename)

        svg_filename = self._svg_filename_from_name(shape.name)
        shape.write_svg_to_file(svg_filename)

    def deserialize_shape(self, name):
        if name in Shape.reserved:
            return Shape(name)

        filename = self._shape_filename_from_name(name)
        shape = Shape(name, filename)

        # Collect a list of custom properties from the Attribute object.
        attrs, properties = self._load_shape_properties(filename)
        for propname, prop in properties:
            param, value = _shape_property_to_param(propname, attrs, prop)
            shape.set_param(param, value)

        # Load the shape image.
        svg_filename = self._svg_filename_from_name(name)
        if os.path.isfile(svg_filename):
            shape.add_svg_from_file(svg_filename)
        return shape

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
        shape_attrs, properties = self._load_shape_properties(tool.shape.filename)

        # Walk through the supported properties, and copy them from the internal
        # model to the tool file representation.
        for propname, prop in properties:
            param, dvalue = _shape_property_to_param(propname, shape_attrs, prop)
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
        tool = Tool(attrs['name'], shape, id=id)

        # Get the list of parameters that are supported by the shape. This
        # is used to find the type of each parameter.
        shape_attrs, properties = self._load_shape_properties(tool.shape.filename)

        # Walk through the supported properties, and copy them from the tool
        # to the internal representation.
        for propname, prop in properties:
            value = attrs['parameter'].pop(propname)
            param, value = _tool_property_to_param(propname, value, prop)
            shape.set_param(param, value)

        # Extract remaining parameters as strings.
        for name, value in attrs['parameter'].items():
            param, value = _tool_property_to_param(name, value)
            shape.set_param(param, value)

        return tool
