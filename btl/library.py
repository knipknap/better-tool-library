# -*- coding: utf-8 -*-
import uuid

class Library(object):
    API_VERSION = 1

    def __init__(self, label, id=None):
        self.id = id or str(uuid.uuid1())
        self.label = label
        self.tools = []
        self.pockets = {}  # Maps pocket number to tool

    def __str__(self):
        return '{} "{}"'.format(self.id, self.label)

    def __eq__(self, other):
        return self.id == other.id

    def get_next_pocket(self):
        pocketlist = sorted(self.pockets, reverse=True)
        return pocketlist[0]+1 if pocketlist else 1

    def get_pocket_from_tool(self, tool):
        for pocket, thetool in self.pockets.items():
            if tool == thetool:
                return pocket
        return None

    def assign_new_pocket(self, tool, pocket=None):
        if tool not in self.tools:
            return

        # If no specific pocket was requested, assign a new one.
        if pocket is None:
            pocket = self.get_next_pocket()

        # Otherwise, add the tool. Since the requested pocket may already
        # be in use, we need to account for that. In this case, we will
        # add the removed tool into a new pocket.
        old_tool = self.pockets.pop(pocket, None)
        old_pocket = self.get_pocket_from_tool(tool)
        if old_pocket:
            del self.pockets[old_pocket]
        self.pockets[pocket] = tool
        if old_tool:
            self.assign_new_pocket(old_tool)
        return pocket

    def add_tool(self, tool, pocket=None):
        if tool not in self.tools:
            self.tools.append(tool)
        self.assign_new_pocket(tool, pocket)

    def get_tools(self):
        return self.tools

    def has_tool(self, tool):
        for t in self.tools:
            if tool.id == t.id:
                return True
        return False

    def remove_tool(self, tool):
        self.tools = [t for t in self.tools if t.id != tool.id]
        self.pockets = {k: v for (k, v) in self.pockets.items() if v != tool}

    def serialize(self, serializer):
        return serializer.serialize_library(self)

    def dump(self, summarize=False):
        title = 'Library "{}" ({})'.format(self.label, self.id)
        print("-"*len(title))
        print(title)
        print("-"*len(title))
        for tool in self.tools:
            tool.dump(summarize=summarize)
            print()
