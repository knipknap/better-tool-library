import os
from PySide import QtGui, QtCore
from ..const import icon_dir
from .util import load_ui
from .shapewidget import ShapeWidget
from .toolproperties import ToolProperties, ToolAttributes

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "tooleditor.ui")

class ToolEditor(QtGui.QWidget):
    def __init__(self, tool, pocket=None, parent=None):
        super(ToolEditor, self).__init__(parent)
        self.form = load_ui(ui_path)
        self.form.buttonBox.clicked.connect(self.form.close)

        self.tool = tool
        self.pocket = pocket

        nameWidget = QtGui.QLineEdit(tool.get_label())
        nameWidget.setPlaceholderText("Tool name")
        self.form.vBox.insertWidget(0, nameWidget)
        nameWidget.setFocus()
        nameWidget.textChanged.connect(tool.set_label)

        widget = ShapeWidget(tool.shape)
        self.form.vBox.insertWidget(1, widget)

        props = ToolProperties(tool, pocket, parent=self.form)
        props.pocketChanged.connect(self._on_pocket_changed)
        tool_tab = self.form.tabWidget.insertTab(0, props, "Tool")
        self.form.tabWidget.setCurrentIndex(tool_tab)

        attrs = ToolAttributes(tool, parent=self.form)
        attr_tab = self.form.tabWidget.addTab(attrs, "Unknown attributes")

        self.form.tabWidget.setCurrentIndex(tool_tab)
        self.form.lineEditCoating.setText(tool.get_coating())
        self.form.lineEditCoating.textChanged.connect(tool.set_coating)
        self.form.lineEditHardness.setText(tool.get_hardness())
        self.form.lineEditHardness.textChanged.connect(tool.set_hardness)
        self.form.lineEditMaterials.setText(tool.get_materials())
        self.form.lineEditMaterials.textChanged.connect(tool.set_materials)
        self.form.lineEditSupplier.setText(tool.get_supplier())
        self.form.lineEditSupplier.textChanged.connect(tool.set_supplier)

        self.form.plainTextEditNotes.setPlainText(tool.get_notes())
        self.form.plainTextEditNotes.textChanged.connect(self._on_notes_changed)

    def _on_notes_changed(self):
        self.tool.set_notes(self.form.plainTextEditNotes.toPlainText())

    def _on_pocket_changed(self, value):
        self.pocket = value

    def show(self):
        return self.form.exec()
