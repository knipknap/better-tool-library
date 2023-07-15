# -*- coding: utf-8 -*-
import uuid

class Tool(object):
    API_VERSION = 1

    def __init__(self, id, name, label, shape):
        self.id = id or str(uuid.uuid1())
        self.name = name
        self.label = label
        self.shape = shape
        self.params = {}

    def __str__(self):
        return '{} "{}" "{}" "{}"'.format(self.id, self.name, self.label, self.shape)

    def serialize(self, serializer):
        return serializer.serialize_tool(self)
