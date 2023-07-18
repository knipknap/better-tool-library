import os
import re
import FreeCAD
import FreeCADGui
import Path
from PySide import QtGui, QtCore
from .flowlayout import FlowLayout
from .shapebutton import ShapeButton

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "shapeselector.ui")

class ShapeSelector():
    def __init__(self, shapes):
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.flow = FlowLayout(self.form.shapeGrid, orientation=QtGui.Qt.Horizontal)
        self.flow.widthChanged.connect(lambda x: self.form.shapeGrid.setMinimumWidth(x))

        for shape in shapes:
            button = ShapeButton(shape)
            self.flow.addWidget(button)

    def show(self):
        self.form.exec()
