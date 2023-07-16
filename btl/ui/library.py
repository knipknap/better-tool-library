# Feed and Speed Calculator
# Provides a basic feeds and speeds calculator for use with FreeCAD Path

import os
import re
import FreeCAD
import FreeCADGui
import Path
from PySide import QtGui

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "library.ui")

class LibraryUI():
    def __init__(self, tooldb, serializer):
        self.tooldb = tooldb
        self.serializer = serializer
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.form.buttonBox.clicked.connect(self.form.close)

        self.load()

    def load(self):
        self.tooldb.deserialize(self.serializer)

        # Update the library list.
        self.form.comboBoxLibrary.clear()
        for library in self.tooldb.get_libraries():
            self.form.comboBoxLibrary.addItem(library.label, library.id)

        # Update the tool list.
        #TODO

    def show(self):
        self.form.show()

    def add_tool_to_job(self, tool):
        jobs = FreeCAD.ActiveDocument.findObjects("Path::FeaturePython", "Job.*")
        for job in jobs:
            for idx, tc in enumerate(job.Tools.Group):
                print(tc.Label) #FIXME
                #tc.HorizFeed = hfeed
                #tc.VertFeed = vfeed
                #tc.SpindleSpeed = float(rpm)
