import os
from functools import partial
from pathlib import Path
from PySide import QtGui, QtCore
from .util import load_ui
from .flowlayout import FlowLayout
from .shapebutton import ShapeButton

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "shapeselector.ui")

class ShapeSelector():
    def __init__(self, tooldb, serializer):
        self.tooldb = tooldb
        self.serializer = serializer
        self.shape = None
        self.form = load_ui(ui_path)

        self.form.buttonBox.clicked.connect(self.form.close)
        self.form.pushButtonImport.clicked.connect(self.on_import_clicked)

        self.flows = {}

        self.update_shapes()
        self.form.toolBox.setCurrentIndex(0)

    def _add_shape_group(self, toolbox):
        if toolbox in self.flows:
            return self.flows[toolbox]
        flow = FlowLayout(toolbox, orientation=QtGui.Qt.Horizontal)
        flow.widthChanged.connect(lambda x: toolbox.setMinimumWidth(x))
        self.flows[toolbox] = flow
        return flow

    def _add_shapes(self, toolbox, shapes):
        flow = self._add_shape_group(toolbox)

        for i in reversed(range(flow.count())):
            flow.itemAt(i).widget().setParent(None)

        for shape in shapes:
            button = ShapeButton(shape)
            flow.addWidget(button)
            cb = partial(self.on_shape_button_clicked, shape)
            button.clicked.connect(cb)

    def update_shapes(self):
        self._add_shapes(self.form.standardTools, self.tooldb.get_builtin_shapes())
        self._add_shapes(self.form.customTools, self.tooldb.get_custom_shapes())

    def on_shape_button_clicked(self, shape):
        self.shape = shape
        self.form.close()

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

        try:
            self.serializer.import_shape_from_file(filename)
        except OSError as e:
            print("error opening file: {}".format(e))
        else:
            self.tooldb.deserialize(self.serializer)
            self.update_shapes()

    def show(self):
        return self.form.exec()
