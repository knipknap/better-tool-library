import os
import sys
import glob
import shutil
from . import const
from .params import Param
from .toolmaterial import ToolMaterial, HSS, Carbide
from .util import file_is_newer, get_abbreviations_from_svg
from .fcutil import load_shape_properties, \
                    shape_property_to_param, \
                    shape_properties_to_shape, \
                    create_thumbnail

builtin_shape_dir = os.path.join(const.resource_dir, 'shapes')
builtin_shape_ext = '.fcstd'
builtin_shape_pattern = os.path.join(builtin_shape_dir, '*.fcstd')

def get_builtin_shape_file_from_name(name):
    return os.path.join(builtin_shape_dir, name+builtin_shape_ext)

def get_icon_filename_from_shape_filename(filename, icon_type):
    return os.path.splitext(filename)[0]+'.'+icon_type

class Shape():
    aliases = {'bullnose': 'torus',
               'thread-mill': 'threadmill',
               'v-bit': 'vbit'}
    builtin = [os.path.splitext(os.path.basename(f))[0]
               for f in glob.glob(os.path.join(builtin_shape_pattern))]
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

    def set_param(self, name, value):
        if not isinstance(name, str):
            paramtype = type(name)
            raise AttributeError(f"name argument has invalid type {paramtype}")
        if isinstance(value, Param):
            self.params[name] = value
        else:
            self.params[name].v = value

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
            if not param:
                continue
            abbr = self.get_abbr(param)

            if abbr:
                summary += ' '+abbr+param.format()
            elif param.choices is not None:
                summary += ' '+param.format()
            else:
                summary += ' {} {}'.format(param.label, param.format())

        return summary.strip()

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
        return item.v if item else None

    def get_diameter(self):
        item = self.params.get('Diameter')
        return item.v if item else None

    def get_cutting_edge(self):
        item = self.params.get('CuttingEdgeHeight')
        return item.v if item else None

    def get_length(self):
        item = self.params.get('Length')
        return item.v if item else None

    def get_flutes(self):
        item = self.params.get('Flutes')
        return item.v if item else None

    def get_chipload(self):
        item = self.params.get('Chipload')
        return item.v if item else None

    def get_radius(self):
        item = self.params.get('Radius')
        return item.v if item else 0

    def get_corner_radius(self):
        if self.name == 'ballend':
            return self.get_diameter()/2
        item = self.params.get('TorusRadius')
        return item.v if item else 0

    def get_cutting_edge_angle(self):
        item = self.params.get('CuttingEdgeAngle')
        return item.v if item else 0

    def get_tip_diameter(self):
        item = self.params.get('TipDiameter')
        return item.v if item else 0

    def get_tip_angle(self):
        item = self.params.get('TipAngle')
        return item.v if item else 0

    def set_material(self, tool_material):
        assert issubclass(tool_material, ToolMaterial)
        param = Param('Material', v=tool_material.name)
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

    def dump(self, indent=0, summarize=True):
        indent = ' '*indent
        print('{}Shape "{}"'.format(
            indent,
            self.name
        ))
        print('{}  File       = {}'.format(indent, self.filename))
        print('{}  Icon type  = {}'.format(indent, self.icon_type))
        print('{}  Icon bytes = {}'.format(indent, self.get_icon_len()))

        if summarize:
            summary = self.get_param_summary()
            print('{}  Summary = {}'.format(indent, summary))
            return

        print('{}  Parameters:'.format(indent))
        for param in self.params.values():
            print('{}    {: <20} = {}'.format(indent, param.label, param.format()))

# Loading shapes on import doesn't work; FreeCAD as not finished initializing.
# This proxy delays loading the builtin shapes until they are accessed.
class DictProxy(dict):
    def __getitem__(self, key):
        self.prepare()
        return super().__getitem__(key)

    def values(self):
        self.prepare()
        return super().values()

    def prepare(self):
        if len(self) == 0:
            for shape in Shape.builtin:
                self[shape] = Shape(shape)

builtin_shapes = DictProxy()
