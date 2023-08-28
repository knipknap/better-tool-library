import os
import re
from . import params
from .util import sha256sum

def parse_float_with_unit(distance, default_unit='mm'):
    if not distance:
        return None, default_unit
    try:
        value, unit = distance.split(' ')
    except ValueError:
        value = distance
        unit = default_unit

    value = value.replace(',', '.')
    return float(value), unit

def parse_angle(value):
    return float(value.rstrip(' °').replace(',', '.')) if value else None

def int_or_none(value):
    try:
        return int(value) or None
    except TypeError:
        return None

def float_or_none(value):
    try:
        return float(value) or None
    except TypeError:
        return None

def type_from_prop(propname, prop):
    if isinstance(prop, bool):
        return params.BoolParam
    elif isinstance(prop, int):
        return params.IntParam
    elif isinstance(prop, float):
        return params.FloatParam
    elif isinstance(prop, str):
        return params.Param
    elif hasattr(prop, 'Unit') and prop.Unit.Type == 'Length':
        return params.DistanceParam
    elif hasattr(prop, 'Unit') and prop.Unit.Type == 'Angle':
        return params.AngleParam
    else:
        raise NotImplementedError(
            'error: param {} with type {} is unsupported'.format(
                 propname, prop.Unit.Type))

def shape_property_to_param(groupname, propname, prop, enums):
    # Default can be overwritten by more specific known types.
    param_type = type_from_prop(propname, prop)
    if not param_type:
        raise NotImplementedError(
            'param {} with type {} not supported'.format(
                 propname, prop))

    param = param_type(name=propname)
    param.group = groupname
    if hasattr(prop, 'Unit'):
        param.v = prop.Value
        param.unit = prop.getUserPreferred()[2]
    else:
        param.v = prop

    # In case of enumerations, collect all allowed values.
    #choices = attrs.getEnumerationsOfProperty(prop.Name)
    if enums is not None:
        param.choices = enums

    return param

def shape_properties_to_shape(properties, shape):
    for groupname, propname, prop, enums in properties:
        param = shape_property_to_param(groupname, propname, prop, enums)
        shape.set_param(param.name, param)

def tool_property_to_param(groupname, propname, prop, enums, value):
    """
    Using the given prop (=a property coming from a FreeCAD shape file) as
    a type hint, this function converts the given value to our internal
    parameter type (as defined in the params module).
    """
    param = shape_property_to_param(groupname, propname, prop, enums)
    value = value if value is not None else prop.Value
    if issubclass(param.type, bool):
        param.v = bool(value or False)
    elif issubclass(param.type, int):
        param.v = int_or_none(value)
    elif issubclass(param.type, float) and param.unit and isinstance(value, str):
        param.v, param.unit = parse_float_with_unit(value, param.unit)
    elif issubclass(param.type, float):
        param.v = float_or_none(value)
    elif issubclass(param.type, str):
        param.v = value
    else:
        raise NotImplementedError(
          f'whoops - param {propname} with type {param.type} not implemented')
    return param

shape_cache = {}

def load_shape_properties(filename):
    # Loading those is quite slow - well, actually it is CLOSING a FreeCAD
    # file that is slow, see .closeDocument() below.
    # In any case, we cache shapes as a workaround.
    global shape_cache
    filehash = sha256sum(filename)
    cache = shape_cache.get(filename)

    if cache:
        cachehash, properties = cache
        if cachehash == filehash:
            return properties

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
        enums = attrs.getEnumerationsOfProperty(propname)
        properties.append((groupname, propname, prop, enums))

    # Note that .closeDocument() is extremely slow; it takes
    # almost 400ms per document - much longer than opening!
    FreeCAD.closeDocument(doc.Name)
    if olddoc:
        FreeCAD.setActiveDocument(olddoc.Name)
    if FreeCAD.GuiUp:
        for sel in oldselection:
            FreeCADGui.Selection.addSelection(olddoc.Name, sel.Name)

    shape_cache[filename] = filehash, properties
    return properties

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

def get_jobs():
    try:
        from PathScripts import PathUtilsGui
    except ImportError:
        raise RuntimeError('Error: Could not access Path workbench, is it loaded?')
    return PathUtilsGui.PathUtils.GetJobs()

def get_active_job():
    # Currently, Job objects have no active/inactive state, so we "simulate"
    # this behavior: If there's only one job, return that one.
    # Otherwise, find the job by searching the object tree, beginning at the
    # current selection.
    jobs = get_jobs()
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
