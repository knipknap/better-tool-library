# -*- coding: utf-8 -*-
import uuid

class Tool(object):
    API_VERSION = 1

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

    def serialize(self, serializer):
        return serializer.serialize_tool(self)
