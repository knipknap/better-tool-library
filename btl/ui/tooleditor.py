import os
from PySide import QtGui, QtCore
from ..const import icon_dir
from .util import load_ui
from .shapewidget import ShapeWidget
from .toolproperties import ToolProperties

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "tooleditor.ui")

class ToolEditor():
    def __init__(self, tool):
        self.form = load_ui(ui_path)
        self.form.buttonBox.clicked.connect(self.form.close)

        widget = ShapeWidget(tool.shape)
        self.form.vBox.addWidget(widget)
        props = ToolProperties(tool)
        self.form.vBox.addWidget(props)

    def show(self):
        self.form.exec()
