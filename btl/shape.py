import os
import sys
import glob
import shutil
from . import const

builtin_shape_dir = os.path.join(const.resource_dir, 'shapes')
builtin_shape_ext = '.fcstd'
builtin_shape_pattern = os.path.join(builtin_shape_dir, '*.fcstd')

def get_builtin_shape_file_from_name(name):
    return os.path.join(builtin_shape_dir, name+builtin_shape_ext)

def get_builtin_shape_svg_filename_from_name(name):
    return os.path.join(builtin_shape_dir, name+'.svg')


class Shape():
    aliases = {'bullnose': 'torus'}
    builtin = [os.path.splitext(os.path.basename(f))[0]
               for f in glob.glob(os.path.join(builtin_shape_pattern))] \
            + list(aliases.keys())

    def __init__(self, name, freecad_filename=None):
        name = Shape.aliases.get(name, name)
        self.name = name
        self.filename = freecad_filename
        self.svg = None # Shape SVG as a binary string

        # Builtin types get preferences.
        if name in Shape.builtin:
            self.filename = get_builtin_shape_file_from_name(name)
            svg_file = get_builtin_shape_svg_filename_from_name(name)
            if os.path.isfile(svg_file):
                self.add_svg_from_file(svg_file)

        if not self.filename or not os.path.isfile(self.filename):
            raise OSError('shape "{}" not found: {}'.format(name, self.filename))

    def __str__(self):
        return self.name

    def is_builtin(self):
        return self.name in Shape.builtin

    def get_filename(self):
        return self.filename

    def write_to_file(self, filename):
        if filename == self.filename:
            return
        shutil.copy(self.filename, filename)

    def get_svg(self):
        return self.svg

    def add_svg_from_file(self, filename):
        with open(filename, 'rb') as fp:
            self.svg = fp.read()

    def write_svg_to_file(self, filename):
        if not self.svg:
            return
        with open(filename, 'wb') as fp:
            fp.write(self.svg)

    def get_properties(self):
        """
        Opens the FreeCAD file to look for all defined custom propoerties.
        It returns a list of tuples:

            (group, propname, value, unit, enum)

        where value is the current value, and enum is a list of allowed values.
        """
        # Load the shape file using FreeCad
        import FreeCAD
        doc = FreeCAD.open(self.filename)

        # Find the Attribute object.
        attrs_list = doc.getObjectsByLabel('Attributes')
        try:
            attrs = attrs_list[0]
        except IndexError:
            raise Exception(f'shape file {self.filename} has no "Attributes" FeaturePython object.\n'\
                          + ' Check the parameter definition in your shape file')

        # Collect a list of custom properties from the Attribute object.
        properties = []
        for propname in attrs.PropertiesList:
            prop = getattr(attrs, propname)
            group = attrs.getGroupOfProperty(propname)
            if group in ('', 'Base'):
                continue

            # Special case: built-in types like int don't have Unit or Value fields.
            if hasattr(prop, 'Unit'):
                unit = prop.Unit
                value = prop.Value
                #print("Prop", group, propname, prop.Format, prop.UserString)
            else:
                unit = prop.__class__.__name__
                value = prop

            # In case of enumerations, collect all allowed values.
            enum = attrs.getEnumerationsOfProperty(propname)

            #print("GRP", group, propname, value, unit, enum)
            properties.append((group, propname, value, unit, enum))

        return sorted(properties)

    def dump(self, indent=0):
        indent = ' '*indent
        print('{}Shape "{}" ({})'.format(
            indent,
            self.name,
            self.filename
        ))
