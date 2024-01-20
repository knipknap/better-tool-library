import os
import sys
import glob
import shutil
from . import const
from .params import Param, DistanceParam
from .i18n import translate
from .toolmaterial import ToolMaterial, HSS, Carbide
from .util import file_is_newer, get_abbreviations_from_svg
from .fcutil import load_shape_properties, \
                    shape_property_to_param, \
                    shape_properties_to_shape, \
                    create_thumbnail

builtin_shape_dir = os.path.join(const.resource_dir, 'shapes')
builtin_shape_ext = '.fcstd'
builtin_shape_pattern = os.path.join(builtin_shape_dir, '*.fcstd')
builtin_shape_list = [
    os.path.splitext(os.path.basename(f))[0]
    for f in glob.glob(os.path.join(builtin_shape_pattern))
]
# allow hiding shape files that start with an underscore
# this is useful if a shape file should only be used for import purposes, for example
hidden_builtin_shape_pattern = os.path.join(builtin_shape_dir, '_*.fcstd')
hidden_builtin_shape_list = [
    os.path.splitext(os.path.basename(f))[0]
    for f in glob.glob(os.path.join(hidden_builtin_shape_pattern))
]


def get_builtin_shape_file_from_name(name):
    return os.path.join(builtin_shape_dir, name+builtin_shape_ext)

def get_icon_filename_from_shape_filename(filename, icon_type):
    return os.path.splitext(filename)[0]+'.'+icon_type

# Make some well-known strings that come from shape files translatable.
# We cannot just make the map, as at the time of import the translator
# is not yet initialized, so translate() would not yet do anything.
property_labels = {}
def get_property_label_from_name(name, default=None):
    global property_labels
    if not property_labels:
        property_labels = {
            # Common
            'Diameter': translate('btl', 'Diameter'),
            'ShaftDiameter': translate('btl', 'Shaft diameter'),
            'ShankDiameter': translate('btl', 'Shank diameter'),
            'Flutes': translate('btl', 'Flutes'),
            'Length': translate('btl', 'Length'),
            'CuttingEdgeHeight': translate('btl', 'Cutting edge height'),
            'Material': translate('btl', 'Material'),
            'Chipload': translate('btl', 'Chipload'),
            'SpindleDirection': translate('btl', 'Spindle direction'),
            'Angle': translate('btl', 'Angle'),

            # Probe
            'SpindlePower': translate('btl', 'Spindle power'),

            # Torus
            'TorusRadius': translate('btl', 'Torus radius'),

            # Chamfer
            'Radius': translate('btl', 'Radius'),

            # Slitting saw
            'CapHeight': translate('btl', 'Cap height'),
            'CapDiameter': translate('btl', 'Cap diameter'),
            'BladeThickness': translate('btl', 'Blade thickness'),

            # Dovetail + Threadmill
            'DovetailHeight': translate('btl', 'Dovetail height'),
            'CuttingAngle': translate('btl', 'Cutting angle'),
            'NeckLength': translate('btl', 'Neck length'),
            'NeckDiameter': translate('btl', 'Neck diameter'),
            'Crest': translate('btl', 'Crest'),

            # Drill
            'TipAngle': translate('btl', 'Tip angle'),

            # V-Bit
            'CuttingEdgeAngle': translate('btl', 'Cutting edge angle'),
            'TipDiameter': translate('btl', 'Tip diameter'),
        }
    return property_labels.get(name, default)

class Shape():
    aliases = {'bullnose': 'torus',
               'thread-mill': 'threadmill',
               'v-bit': 'vbit'}
    builtin = builtin_shape_list
    hidden_builtin = hidden_builtin_shape_list
    well_known = (
        'Diameter',
        'ShaftDiameter',
        'ShankDiameter',
        'Flutes',
        'Length',
        'CuttingEdgeHeight',
        'Material',
    )
    reserved = set(aliases)|set(builtin)

    def __init__(self, name, freecad_filename=None):
        name = Shape.aliases.get(name, name)
        self.name = name
        self.filename = freecad_filename
        self.icon = None # Shape SVG or PNG as a binary string
        self.icon_type = None # Shape PNG as a binary string
        self.abbr = {} # map param name to an abbreviation, if found in SVG
        self.params = {} # map param name to a param

        # Load the shape files. Builtin types get preference, so they
        # overwrite any values already defined above.
        if name in Shape.builtin:
            self.filename = get_builtin_shape_file_from_name(name)
            properties = load_shape_properties(self.filename)
            shape_properties_to_shape(properties, self)
            self.load_or_create_icon()

        if not self.filename or not os.path.isfile(self.filename):
            raise OSError('shape "{}" not found: {}'.format(name, self.filename))

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def to_dict(self):
        return {
            'name': self.name,
            'filename': self.filename,
            'params': [p.to_dict() for p in self.params.values()],
        }

    def set_param(self, name, value):
        if not isinstance(name, str):
            paramtype = type(name)
            raise AttributeError(f"name argument has invalid type {paramtype}")
        if isinstance(value, Param):
            self.params[name] = value
        else:
            self.params[name].v = value

    def add_param(self, param):
        if not isinstance(param, Param):
            paramtype = type(param)
            raise AttributeError(f"param argument has invalid type {paramtype}")
        self.params[param.name] = param
        return param

    def get_param(self, name, default=None):
        if not isinstance(name, str):
            paramtype = type(name)
            raise AttributeError(f"name argument has invalid type {paramtype}")
        return self.params.get(name, default)

    def get_params(self):
        return sorted(self.params.items())

    def get_param_summary(self):
        summary = self.get_label()

        for name in self.well_known:
            param = self.get_param(name)
            if not param or not param.v:
                continue
            abbr = self.get_abbr(param)

            if abbr:
                summary += ' '+abbr+param.format()
            elif param.choices is not None:
                summary += ' '+param.format()
            else:
                label = get_property_label_from_name(param.name, param.label)
                summary += ' {} {}'.format(label, param.format())

        return summary.strip()

    def get_params_by_group(self, group):
        return [p for p in self.params.values() if param.group == group]

    def get_well_known_params(self):
        for name in self.well_known:
            if name in self.params:
                yield self.params[name]

    def get_non_well_known_params(self):
        for param in self.params.values():
            if param.name not in self.well_known:
                yield param

    def is_builtin(self):
        return self.name in Shape.builtin

    def get_label(self):
        return self.name.capitalize()

    def get_filename(self):
        return self.filename

    def write_to_file(self, filename):
        if filename == self.filename:
            return
        shutil.copy(self.filename, filename)

    def get_shank_diameter(self):
        item = self.params.get('ShankDiameter')
        return item.value('mm') if item else None

    def get_diameter(self):
        item = self.params.get('Diameter')
        return item.value('mm') if item else None

    def set_diameter(self, diameter, unit='mm'):
        param = DistanceParam(name='Diameter', unit=unit, v=diameter)
        self.add_param(param)

    def get_cutting_edge(self):
        item = self.params.get('CuttingEdgeHeight')
        return item.value('mm') if item else None

    def get_length(self):
        item = self.params.get('Length')
        return item.value('mm') if item else None

    def set_length(self, length, unit='mm'):
        param = DistanceParam(name='Length', unit=unit, v=length)
        self.add_param(param)

    def get_flutes(self):
        item = self.params.get('Flutes')
        return item.v if item else None

    def get_chipload(self):
        item = self.params.get('Chipload')
        return item.value('mm') if item else None

    def get_radius(self):
        item = self.params.get('Radius')
        return item.value('mm') if item else 0

    def get_corner_radius(self):
        if self.name == 'ballend':
            return self.get_diameter()/2
        item = self.params.get('TorusRadius')
        return item.value('mm') if item else 0

    def get_cutting_edge_angle(self):
        item = self.params.get('CuttingEdgeAngle')
        return item.v if item else 0

    def get_tip_diameter(self):
        item = self.params.get('TipDiameter')
        return item.value('mm') if item else 0

    def get_tip_angle(self):
        item = self.params.get('TipAngle')
        return item.v if item else 0

    def set_material(self, tool_material):
        assert issubclass(tool_material, ToolMaterial)
        param = Param('Material', v=tool_material.__name__)
        self.set_param(param.name, param)

    def get_material(self):
        material = self.get_param('Material')
        if material.v.lower() == 'hss':
            return HSS
        elif material.v.lower() == 'carbide':
            return Carbide
        return None

    def get_icon(self):
        return self.icon_type, self.icon

    def get_icon_len(self):
        return len(self.icon) if self.icon else 0

    def add_icon_from_file(self, filename):
        with open(filename, 'rb') as fp:
            self.icon = fp.read()
            if filename.endswith('svg'):
                self.abbr = get_abbreviations_from_svg(self.icon)
        self.icon_type = os.path.splitext(filename)[1].lstrip('.')

    def get_abbr(self, param):
        normalized = param.label.lower().replace(' ', '_')
        return self.abbr.get(normalized)

    def create_icon(self):
        filename = create_thumbnail(self.filename)
        if filename: # success?
            self.add_icon_from_file(filename)
        return filename

    def load_or_create_icon(self):
        # Try SVG first.
        shape_fn = self.filename
        icon_file = get_icon_filename_from_shape_filename(shape_fn, 'svg')
        if os.path.isfile(icon_file):
            return self.add_icon_from_file(icon_file)

        # Try PNG next. But make sure it's not out of date.
        icon_file = get_icon_filename_from_shape_filename(shape_fn, 'png')
        if os.path.isfile(icon_file) and file_is_newer(self.filename, icon_file):
            return self.add_icon_from_file(icon_file)

        # Next option: Try to re-generate the PNG.
        if self.create_icon():
            return

        # Last option: return the out-of date PNG.
        if os.path.isfile(icon_file):
            return self.add_icon_from_file(icon_file)

    def write_icon_to_file(self, filename=None):
        if self.icon is None:
            return
        if filename is None:
            filename = get_icon_filename_from_shape_filename(self.filename,
                                                             self.icon_type)
        with open(filename, 'wb') as fp:
            fp.write(self.icon)

    def to_string(self, indent=0, summarize=False):
        result = []
        indent = ' '*indent
        result.append(f'{indent}Shape "{self.name}"')
        result.append(f'{indent}  File       = {self.filename}')
        result.append(f'{indent}  Icon type  = {self.icon_type}')
        result.append(f'{indent}  Icon bytes = {self.get_icon_len()}')

        if summarize:
            summary = self.get_param_summary()
            result.append(f'{indent}  Summary = {summary}')
            return

        result.append(f'{indent}  Parameters:')
        for param in self.params.values():
            result.append(f'{indent}    {param.label: <20} = {param.format()}')

        return '\n'.join(result)

    def dump(self, indent=0, summarize=True):
        print(self.to_string(indent, summarize))

# Loading shapes on import doesn't work; FreeCAD as not finished initializing.
# This proxy delays loading the builtin shapes until they are accessed.
class DictProxy(dict):
    def __init__(self, shapelist):
        self._shapelist = shapelist

    def __getitem__(self, key):
        self.prepare()
        return super().__getitem__(key)

    def values(self):
        self.prepare()
        return super().values()

    def keys(self):
        self.prepare()
        return super().keys()

    def items(self):
        self.prepare()
        return super().items()

    def prepare(self):
        if len(self) == 0:
            for shape in self._shapelist:
                self[shape] = Shape(shape)

builtin_shapes = DictProxy(Shape.builtin)
hidden_builtin_shapes = DictProxy(Shape.hidden_builtin)
