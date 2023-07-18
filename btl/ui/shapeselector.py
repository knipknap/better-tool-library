import os
import re
import FreeCAD
import FreeCADGui
import Path
from functools import partial
from itertools import chain
from PySide import QtGui, QtCore
from ..const import icon_dir
from .flowlayout import FlowLayout
from .shapebutton import ShapeButton

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "shapeselector.ui")

class CustomShape:
    name = 'custom'

    def get_label(self):
        return self.name.capitalize()

    def get_svg(self):
        filename = os.path.join(icon_dir, 'plus.svg')
        with open(filename, 'rb') as fp:
            return fp.read()

class ShapeSelector():
    def __init__(self, shapes):
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.flow = FlowLayout(self.form.shapeGrid, orientation=QtGui.Qt.Horizontal)
        self.flow.widthChanged.connect(lambda x: self.form.shapeGrid.setMinimumWidth(x))

        self.form.buttonBox.clicked.connect(self.form.close)

        for shape in chain(shapes, [CustomShape()]):
            button = ShapeButton(shape)
            self.flow.addWidget(button)
            cb = partial(self.on_shape_button_clicked, shape)
            button.clicked.connect(cb)

    def on_shape_button_clicked(self, shape):
        self.form.close()

    def show(self):
        self.form.exec()
