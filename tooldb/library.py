# -*- coding: utf-8 -*-
import uuid

class Library(object):
    API_VERSION = 1

    def __init__(self, label, id=None):
        self.id = id or str(uuid.uuid1())
        self.label = label
        self.tools = []

        # The data-structures of tool libraries in FreeCAD are ill-defined; tool IDs are
        # not unique across libraries. This forces us to keep a space to store these
        # library-specific IDs.
        # Maps unique tool ID to FC library-specific-tool ID, and is empty unless it
        # was de-serialized from FreeCAD tool libraries.
        self.fc_tool_ids = dict()

    def __str__(self):
        return '{} "{}"'.format(self.id, self.label)

    def serialize(self, serializer):
        return serializer.serialize_library(self)