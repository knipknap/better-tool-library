import os
from PySide import QtGui, QtCore
from .util import load_ui
from .shapewidget import ShapeWidget
from .toolproperties import ToolProperties, ToolAttributes
from .feedsandspeeds import FeedsAndSpeedsWidget

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "tooleditor.ui")

class ToolEditor(QtGui.QWidget):
    def __init__(self, db, serializer, tool, pocket=None, parent=None):
        super(ToolEditor, self).__init__(parent)
        self.form = load_ui(ui_path)
        self.form.buttonBox.clicked.connect(self.form.close)

        self.db = db
        self.serializer = serializer
        self.tool = tool
        self.pocket = pocket

        nameWidget = QtGui.QLineEdit(tool.get_label())
        nameWidget.setPlaceholderText("Tool name")
        self.form.vBox.insertWidget(0, nameWidget)
        nameWidget.setFocus()
        nameWidget.textChanged.connect(tool.set_label)

        tool_tab_layout = self.form.toolTabLayout
        widget = ShapeWidget(tool.shape)
        tool_tab_layout.addWidget(widget)
        props = ToolProperties(tool, pocket, parent=self.form)
        props.pocketChanged.connect(self._on_pocket_changed)
        tool_tab_layout.addWidget(props)

        self.feeds = FeedsAndSpeedsWidget(db, serializer, tool, parent=self)
        self.feeds_tab_idx = self.form.tabWidget.insertTab(1, self.feeds, "Feeds && Speeds")

        attrs = ToolAttributes(tool, parent=self.form)
        attr_tab = self.form.tabWidget.addTab(attrs, "Attributes")

        self.form.tabWidget.setCurrentIndex(0)
        self.form.tabWidget.currentChanged.connect(self._on_tab_switched)
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

    def _on_tab_switched(self, index):
        if index == self.feeds_tab_idx:
            self.feeds.update()

    def _on_notes_changed(self):
        self.tool.set_notes(self.form.plainTextEditNotes.toPlainText())

    def _on_pocket_changed(self, value):
        self.pocket = value

    def show(self):
        return self.form.exec_()
