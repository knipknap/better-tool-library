# -*- coding: utf-8 -*-
import uuid
from .shape import Shape
from .params import known_types, fc_property_to_param_name

class Tool(object):
    API_VERSION = 1

    well_known = tuple(t.name for t in known_types)

    def __init__(self, label, shape, id=None):
        self.id = id or str(uuid.uuid1())
        self.label = label
        self.shape = Shape(shape) if isinstance(shape, str) else shape
        self.pocket = None

        # Common tool parameters.
        self.diameter = None
        self.flutes = None
        self.shaft = None
        self.length = None
        self.material = None
        self.params = {}

        # Init params from shape.
        for group, propname, value, unit, enum in self.shape.get_properties():
            param = fc_property_to_param_name.get(propname, propname)
            self.set_param(param, value)

    def __str__(self):
        return '{} "{}" "{}"'.format(self.id, self.label, self.shape.name)

    def get_label(self):
        return self.label

    def set_param(self, name, value):
        lcname = name.lower()
        if lcname in Tool.well_known:
            setattr(self, lcname, value)
        else:
            self.params[name] = value

    def get_param(self, name):
        lcname = name.lower()
        if lcname in Tool.well_known:
            return getattr(self, lcname)
        return self.params[lcname]

    def get_well_known_params(self):
        return [(n, getattr(self, n.name)) for n in known_types]

    def get_custom_params(self):
        return sorted(self.params.items())

    def get_param_summary(self):
        summary = self.shape.get_label()
        for param in known_types:
            value = getattr(self, param.name)
            if value is not None:
                summary += ' ' + param.format(value)
        return summary.strip()

    def serialize(self, serializer):
        return serializer.serialize_tool(self)

    def dump(self, indent=0, summarize=False):
        indent = ' '*indent
        print('{}Tool "{}" ({})'.format(
            indent,
            self.label,
            self.id
        ))
        if summarize:
            summary = self.get_param_summary()
            print('{}  Summary = {}'.format(indent, summary))
            return

        shape_svg = self.shape.get_svg()
        shape_svg_len = len(shape_svg) if shape_svg else None
        print('{}  Shape          = {}'.format(indent, self.shape.get_label()))
        print('{}  Shape SVG size = {}'.format(indent, shape_svg_len))
        print('{}  Pocket         = {}'.format(indent, self.pocket))

        print('{}  Well-known properties:'.format(indent))
        for param in known_types:
            value = getattr(self, param.name)
            print('{}    {: <20} = {}'.format(indent, param.label, value))

        print('{}  Custom properties:'.format(indent))
        for name, value in sorted(self.params.items()):
            label = name.capitalize()
            print('{}    {: <20} = {}'.format(indent, label, value))
