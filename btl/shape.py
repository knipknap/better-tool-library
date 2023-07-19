import os
import sys
import glob
import shutil
from . import const
from .params import known_types

builtin_shape_dir = os.path.join(const.resource_dir, 'shapes')
builtin_shape_ext = '.fcstd'
builtin_shape_pattern = os.path.join(builtin_shape_dir, '*.fcstd')

def get_builtin_shape_file_from_name(name):
    return os.path.join(builtin_shape_dir, name+builtin_shape_ext)

def get_builtin_shape_svg_filename_from_name(name):
    return os.path.join(builtin_shape_dir, name+'.svg')


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
        self.svg = None # Shape SVG as a binary string
        self.params = {}

        # Load the shape image. Builtin types get preferences.
        if name in Shape.builtin:
            self.filename = get_builtin_shape_file_from_name(name)
            svg_file = get_builtin_shape_svg_filename_from_name(name)
            if os.path.isfile(svg_file):
                self.add_svg_from_file(svg_file)

        if not self.filename or not os.path.isfile(self.filename):
            raise OSError('shape "{}" not found: {}'.format(name, self.filename))

    def __str__(self):
        return self.name

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

    def get_svg(self):
        return self.svg

    def get_svg_len(self):
        return len(self.svg) if self.svg else 0

    def add_svg_from_file(self, filename):
        with open(filename, 'rb') as fp:
            self.svg = fp.read()

    def write_svg_to_file(self, filename):
        if not self.svg:
            return
        with open(filename, 'wb') as fp:
            fp.write(self.svg)

    def dump(self, indent=0, summarize=True):
        indent = ' '*indent
        print('{}Shape "{}"'.format(
            indent,
            self.name
        ))
        print('{}  File  = {}'.format(indent, self.filename))
        print('{}  Bytes = {}'.format(indent, self.get_svg_len()))

        if summarize:
            summary = self.get_param_summary()
            print('{}  Summary = {}'.format(indent, summary))
            return

        print('{}  Parameters:'.format(indent))
        for param, value in self.get_params():
            print('{}    {: <20} = {}'.format(indent, param.label, value))
