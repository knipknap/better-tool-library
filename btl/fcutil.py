import os
import re
from . import params
from .params import known_types
from .util import sha256sum

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

def parse_distance(distance):
    if not distance:
        return None
    try:
        value, unit = distance.split(' ')
    except ValueError:
        value = distance
        unit = 'mm'

    value = value.replace(',', '.')
    try:
        value = float(value)
    except ValueError:
        return None

    if unit == "\u00b5m" or unit == "um": # micrometers
        return value*.001
    elif unit == "mm": # millimeters
        return value*1
    elif unit == "m": # meters
        return value*1000
    raise NotImplemented('unsupported value in file: "{}"'.format(value))

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
        value = parse_distance(value)
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

    # In case of enumerations, collect all allowed values.
    if hasattr(param, 'enum'):
        param.enum = attrs.getEnumerationsOfProperty(propname)

    return param, value

def shape_properties_to_shape(attrs, properties, shape):
    for propname, prop in properties:
        param, value = shape_property_to_param(propname, attrs, prop)
        shape.set_param(param, value)

shape_cache = {}

def load_shape_properties(filename):
    # Loading those is quite slow - well, actually it is CLOSING a FreeCAD
    # file that is slow, see .closeDocument() below.
    # In any case, we cache shapes as a workaround.
    global shape_cache
    filehash = sha256sum(filename)
    cache = shape_cache.get(filename)

    if cache:
        cachehash, attrs, properties = cache
        if cachehash == filehash:
            return attrs, properties

    # Load the shape file using FreeCad. Unfortunately this causes everything
    # in the current document to be unselected, so we need to restore the
    # selection later.
    import FreeCAD
    olddoc = FreeCAD.activeDocument()
    if FreeCAD.GuiUp:
        import FreeCADGui
        oldselection = FreeCADGui.Selection.getSelection()
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

    # Note that .closeDocument() is extremely slow; it takes
    # almost 400ms per document - much longer than opening!
    FreeCAD.closeDocument(doc.Name)
    if olddoc:
        FreeCAD.setActiveDocument(olddoc.Name)
    if FreeCAD.GuiUp:
        for sel in oldselection:
            FreeCADGui.Selection.addSelection(olddoc.Name, sel.Name)

    shape_cache[filename] = filehash, attrs, properties
    return attrs, properties

def get_selected_job():
    try:
        import FreeCADGui
        from Path.Main.Job import ObjectJob
    except ImportError:
        raise RuntimeError('Error: Could not access Path workbench, is it loaded?')

    for sel in FreeCADGui.Selection.getSelection():
        while sel is not None:
            if hasattr(sel, 'Proxy') and isinstance(sel.Proxy, ObjectJob):
                return sel
            sel = sel.getParentGroup()

    return None

def get_active_job():
    try:
        from PathScripts import PathUtilsGui
    except ImportError:
        raise RuntimeError('Error: Could not access Path workbench, is it loaded?')

    # Currently, Job objects have no active/inactive state, so we "simulate"
    # this behavior: If there's only one job, return that one.
    # Otherwise, find the job by searching the object tree, beginning at the
    # current selection.
    jobs = PathUtilsGui.PathUtils.GetJobs()
    if not jobs:
        return None
    elif len(jobs) == 1:
        return jobs[0]
    return get_selected_job()

def add_tool_to_job(job, tool, pocket):
    try:
        import FreeCAD
        import FreeCADGui
        from Path.Tool import Controller, Bit
    except ImportError:
        raise RuntimeError('Error: Could not access Path workbench, is it loaded?')

    label = tool.get_label()
    if not tool.filename:
        err = 'Error: Tool "{}" ({}) has no filename.'.format(label, repr(tool.id))
        raise ValueError(err)

    doc = FreeCAD.activeDocument()
    doc.openTransaction("Add tool {}".format(label))
    try:
        toolbit = Bit.Factory.CreateFrom(tool.filename, label)
        toolbit.ViewObject.Visibility = False
        toolcontroller = Controller.Create("TC: {}".format(label), toolbit, pocket)
        job.Proxy.addToolController(toolcontroller)
    except Exception:
        doc.abortTransaction()
        raise
    else:
        doc.commitTransaction()

    FreeCADGui.Selection.addSelection(doc.Name, toolcontroller.Name)

# Find the body with the given label in the document
def _find_body_from_label(doc, label):
    for obj in doc.Objects:
        if obj.Label == label and obj.isDerivedFrom("Part::Feature"):
            return obj
    return None

def _get_first_body(doc):
    for obj in doc.Objects:
        if obj.isDerivedFrom("PartDesign::Body"):
            return obj
    return None

def create_thumbnail(filename, w=200, h=200):
    import FreeCAD
    if not FreeCAD.GuiUp:
        return None

    try:
        import FreeCADGui
        #import importSVG
    except ImportError:
        raise RuntimeError('Error: Could not load UI - is it up?')

    doc = FreeCAD.openDocument(filename)
    view = FreeCADGui.activeDocument().ActiveView
    out_filename = os.path.splitext(filename)[0]+'.png'
    if not view:
        print("No view active, cannot make thumbnail for {}".format(filename))
        return

    view.viewFront()
    view.fitAll()
    view.setAxisCross(False)
    view.saveImage(out_filename, w, h, 'Transparent')

    FreeCAD.closeDocument(doc.Name)
    return out_filename
