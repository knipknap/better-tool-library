import os
from PySide import QtGui, QtCore
from ..const import icon_dir
from .util import load_ui
from .toolproperties import ToolProperties

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "tooleditor.ui")

class ToolEditor(QtGui.QWidget):
    def __init__(self, tool, pocket=None, parent=None):
        super(ToolEditor, self).__init__(parent)
        self.form = load_ui(ui_path)
        self.form.buttonBox.clicked.connect(self.form.close)

        self.tool = tool
        self.pocket = pocket

        props = ToolProperties(tool, pocket, parent=self.form)
        props.pocketChanged.connect(self._on_pocket_changed)
        self.form.vBox.addWidget(props)

    def _on_pocket_changed(self, value):
        self.pocket = value

    def show(self):
        return self.form.exec()
