import os
import sys
import glob
from . import const

sys.path.append(const.freecad_path)

builtin_shapes = [os.path.splitext(os.path.basename(f))[0]
                  for f in glob.glob(os.path.join(const.builtin_shape_pattern))]

def get_shape_file_from_shape(shape):
    if os.path.isfile(shape):
        return shape
    shape_file = os.path.join(const.builtin_shape_dir, shape+const.builtin_shape_ext)
    if os.path.isfile(shape_file):
        return shape_file
    raise Exception('shape not found: {}\nSupported built-in types: {}'.format(shape, builtin_shapes))

def get_properties_from_shape(shape_file):
    """
    Opens the FreeCAD file to look for all defined custom propoerties.
    It returns a list of tuples:

        (group, propname, value, unit, enum)

    where value is the current value, and enum is a list of allowed values.
    """
    # Load the shape file using FreeCad
    import FreeCAD
    doc = FreeCAD.open(shape_file)

    # Find the Attribute object.
    attrs_list = doc.getObjectsByLabel('Attributes')
    try:
        attrs = attrs_list[0]
    except IndexError:
        raise Exception('shape file has no "Attributes" FeaturePyton object. Check your shape file')

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
