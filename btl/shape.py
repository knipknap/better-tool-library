import os
import sys
import glob
import shutil
from . import const
from .util import file_is_newer
from .params import known_types
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
               'vbit': 'chamfer',
               'v-bit': 'chamfer'}
    builtin = [os.path.splitext(os.path.basename(f))[0]
               for f in glob.glob(os.path.join(builtin_shape_pattern))]
    well_known = tuple(t.name for t in known_types)
    reserved = set(aliases)|set(builtin)

    def __init__(self, name, freecad_filename=None):
        name = Shape.aliases.get(name, name)
        self.name = name
        self.filename = freecad_filename
        self.icon = None # Shape SVG or PNG as a binary string
        self.icon_type = None # Shape PNG as a binary string
        self.params = {}

        # Load the shape files. Builtin types get preference, so they
        # overwrite any values already defined above.
        if name in Shape.builtin:
            self.filename = get_builtin_shape_file_from_name(name)
            attrs, properties = load_shape_properties(self.filename)
            shape_properties_to_shape(attrs, properties, self)
            self.load_or_create_icon()

        if not self.filename or not os.path.isfile(self.filename):
            raise OSError('shape "{}" not found: {}'.format(name, self.filename))

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def set_param(self, param, value):
        self.params[param.name] = param, value

    def get_param(self, param, default=None):
        if not isinstance(param, str):
            param = param.name
        if param not in self.params:
            return default
        return self.params[param][1]

    def get_params(self):
        return [(v[0], v[1]) for (k, v) in sorted(self.params.items())]

    def get_param_summary(self):
        summary = self.get_label()
        for param in known_types:
            value = self.get_param(param)
            if value:
                summary += ' ' + param.format(value)
        return summary.strip()

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

    def get_icon(self):
        return self.icon_type, self.icon

    def get_icon_len(self):
        return len(self.icon) if self.icon else 0

    def add_icon_from_file(self, filename):
        with open(filename, 'rb') as fp:
            self.icon = fp.read()
        self.icon_type = os.path.splitext(filename)[1].lstrip('.')

    def create_icon(self):
        filename = create_thumbnail(self.filename)
        if filename: # success?
            self.add_icon_from_file(filename)
        return filename

    def load_or_create_icon(self):
        # Find existing icons.
        shape_fn = self.filename
        icon_file = get_icon_filename_from_shape_filename(shape_fn, 'svg')
        if not os.path.isfile(icon_file):
            icon_file = get_icon_filename_from_shape_filename(shape_fn, 'png')

        # None found? Then try to create one.
        # Note that this may fail, e.g. when the FreeCAD UI is not up,
        # in which case we give up here.
        if not os.path.isfile(icon_file):
            print("no icon found, trying to create for", self.filename)
            return self.create_icon()

        # If the icon is out of date, try to recreate. Again, keep in
        # mind that this may fail, in which case this time we can use
        # the out-of-date one.
        if self.icon_type != 'svg' and not file_is_newer(self.filename, icon_file):
            print("icon out of date, trying to create", icon_file)
            if self.create_icon():
                print("icon created for", self.filename)
                return
        self.add_icon_from_file(icon_file)

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
        for param, value in self.get_params():
            print('{}    {: <20} = {}'.format(indent, param.label, value))

class DictProxy(dict):
    def __getitem__(self, key):
        if len(self) == 0:
            for shape in Shape.builtin:
                self[shape] = Shape(shape)
        return super().__getitem__(key)

builtin_shapes = DictProxy()
