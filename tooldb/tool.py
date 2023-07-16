# -*- coding: utf-8 -*-
import uuid

class Tool(object):
    API_VERSION = 1
    well_known = ('diameter',
                  'length')

    def __init__(self, label, shape, id=None):
        self.id = id or str(uuid.uuid1())
        self.label = label
        self.shape = shape
        self.pocket = None
        self.diameter = None
        self.length = None
        self.params = {}

    def __str__(self):
        return '{} "{}" "{}"'.format(self.id, self.label, self.shape)

    def set_param(self, name, value):
        lcname = name.lower()
        if lcname in Tool.well_known:
            setattr(self, lcname, value)
        else:
            self.params[name] = value

    def serialize(self, serializer):
        return serializer.serialize_tool(self)

    def dump(self, indent=0):
        indent = ' '*indent
        print('{}Tool "{}" ({})'.format(
            indent,
            self.label,
            self.id
        ))
        print('{}  Shape    = {}'.format(indent, self.shape))
        print('{}  Pocket   = {} mm'.format(indent, self.pocket))

        print('{}  Well-known properties:'.format(indent))
        for name in sorted(Tool.well_known):
            value = getattr(self, name)
            label = name.capitalize()
            print('{}    {: <20} = {}'.format(indent, label, value))

        print('{}  Custom properties:'.format(indent))
        for name, value in sorted(self.params.items()):
            print('{}    {: <20} = {}'.format(indent, name, value))
