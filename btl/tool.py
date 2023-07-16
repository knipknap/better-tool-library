# -*- coding: utf-8 -*-
import uuid

class Tool(object):
    API_VERSION = 1

    # The parameters need to be ordered by "importance"; this order is
    # used the generate a summary description of the tool, showing the
    # important parameters first. See get_param_summary().
    well_known_format = (('shape', '{}', str.capitalize),
                         ('diameter', 'D{}mm', float),
                         ('flutes', '{}-flute', int),
                         ('shaft', 'Shaft {}mm', float),
                         ('length', 'L{}mm', float),
                         ('material', '{}', str))
    well_known = tuple(p[0] for p in well_known_format)

    def __init__(self, label, shape, id=None):
        self.id = id or str(uuid.uuid1())
        self.label = label
        self.shape = shape
        self.shape_svg = None
        self.pocket = None
        self.diameter = None
        self.flutes = None
        self.shaft = None
        self.length = None
        self.material = None
        self.params = {}

    def __str__(self):
        return '{} "{}" "{}"'.format(self.id, self.label, self.shape)

    def set_param(self, name, value):
        lcname = name.lower()
        if lcname in Tool.well_known:
            setattr(self, lcname, value)
        else:
            self.params[name] = value

    def get_param_summary(self):
        summary = ''
        for name, fmt, formatter in Tool.well_known_format:
            value = getattr(self, name)
            if value is not None:
                summary += ' ' + fmt.format(formatter(value))
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

        shape_svg_len = len(self.shape_svg) if self.shape_svg else None
        print('{}  Shape SVG size = {}'.format(indent, shape_svg_len))
        print('{}  Pocket         = {} mm'.format(indent, self.pocket))

        print('{}  Well-known properties:'.format(indent))
        for name in Tool.well_known:
            value = getattr(self, name)
            label = name.capitalize()
            print('{}    {: <20} = {}'.format(indent, label, value))

        print('{}  Custom properties:'.format(indent))
        for name, value in sorted(self.params.items()):
            print('{}    {: <20} = {}'.format(indent, name, value))
