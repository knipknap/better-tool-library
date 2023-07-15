# -*- coding: utf-8 -*-
import uuid

class Tool(object):
    API_VERSION = 1

    def __init__(self, label, shape, id=None, name=None):
        self.id = int(id) if id else None
        self.name = name or str(uuid.uuid1())
        self.label = label
        self.shape = shape
        self.params = {}

    def __str__(self):
        return '{} "{}" "{}" "{}"'.format(self.id, self.name, self.label, self.shape)

    def serialize(self, serializer):
        return serializer.serialize_tool(self)
