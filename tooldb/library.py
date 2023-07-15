# -*- coding: utf-8 -*-
import uuid

class Library(object):
    API_VERSION = 1

    def __init__(self, id, name, label=None):
        self.id = id or str(uuid.uuid1())
        self.name = name
        self.label = label or name
        self.tools = []

    def __str__(self):
        return '{} "{}" "{}"'.format(self.id, self.name, self.label)

    def serialize(self, serializer):
        return serializer.serialize_library(self)
