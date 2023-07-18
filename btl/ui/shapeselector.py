import os
from functools import partial
from pathlib import Path
from PySide import QtGui, QtCore
from ..tool import Tool
from .util import load_ui
from .flowlayout import FlowLayout
from .shapebutton import ShapeButton
from .tooleditor import ToolEditor

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "shapeselector.ui")

class ShapeSelector():
    def __init__(self, tooldb):
        self.tooldb = tooldb
        self.form = load_ui(ui_path)

        self.flow = FlowLayout(self.form.shapeGrid, orientation=QtGui.Qt.Horizontal)
        self.flow.widthChanged.connect(lambda x: self.form.shapeGrid.setMinimumWidth(x))

        self.form.buttonBox.clicked.connect(self.form.close)
        self.form.pushButtonImport.clicked.connect(self.on_import_clicked)

        self.update_shapes()

    def update_shapes(self):
        for shape in self.tooldb.shapes.values():
            button = ShapeButton(shape)
            self.flow.addWidget(button)
            cb = partial(self.on_shape_button_clicked, shape)
            button.clicked.connect(cb)


    def on_shape_button_clicked(self, shape):
        self.form.close()
        tool = Tool('New tool', shape)
        editor = ToolEditor(tool)
        editor.show()

    def on_import_clicked(self):
        filename = QtGui.QFileDialog.getOpenFileName(
             self.form,
             "Choose a Shape File",
             dir=str(Path.home()),
             filter='FreeCAD files .fcstd (*.fcstd)'
        )[0]
        if not filename:
            self.form.close()
            return

        print("selected shape:", filename) # TODO

    def show(self):
        self.form.exec()
