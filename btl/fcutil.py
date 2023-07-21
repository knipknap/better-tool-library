import re
from . import params
from .params import known_types

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

def type_from_prop(propname, prop):
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

def parse_unit(value):
    return float(value.rstrip(' m').replace(',', '.')) if value else None

def parse_angle(value):
    return float(value.rstrip(' °').replace(',', '.')) if value else None

def int_or_none(value):
    try:
        return int(value) or None
    except TypeError:
        return None

def tool_property_to_param(propname, value, prop=None):
    if propname in fc_property_to_param_type:   # Known type.
        param_type = fc_property_to_param_type[propname]
        param = param_type()
    else:  # Try to find type from prop.
        param_type = params.Base if prop is None else type_from_prop(propname, prop)
        param = param_type()
        param.name = propname
        param.label = re.sub(r'([A-Z])', r' \1', propname).strip()

    if issubclass(param_type, params.DistanceBase):
        value = parse_unit(value)
    elif issubclass(param_type, params.AngleBase):
        value = parse_angle(value)
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

def shape_property_to_param(propname, attrs, prop):
    param_type = type_from_prop(propname, prop)
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

def shape_properties_to_shape(attrs, properties, shape):
    for propname, prop in properties:
        param, value = shape_property_to_param(propname, attrs, prop)
        shape.set_param(param, value)

def load_shape_properties(filename):
    # Load the shape file using FreeCad
    import FreeCAD
    doc = FreeCAD.openDocument(filename, hidden=True)

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

    # Disabled: Somehow, .closeDocument is extremely slow; it takes
    # almost 400ms per document - much longer than opening!
    # Luckily, these files are really small, so hopefully we can get
    # away without it for now :-/
    #FreeCAD.closeDocument(doc.Name)
    del doc
    return attrs, properties
