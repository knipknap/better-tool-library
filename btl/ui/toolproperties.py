import re
from PySide import QtGui, QtSvg, QtCore
from .shapewidget import ShapeWidget

class ToolProperties(QtGui.QWidget):
    def __init__ (self, tool, parent=None):
        super(ToolProperties, self).__init__(parent)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignHCenter)

        self.nameWidget = QtGui.QLineEdit(tool.get_label())
        self.nameWidget.setPlaceholderText("Tool name")
        self.layout.addWidget(self.nameWidget)
        self.nameWidget.setFocus()

        widget = ShapeWidget(tool.shape)
        self.layout.addWidget(widget)

        self.grid = QtGui.QGridLayout()
        self.grid.setColumnStretch(0, 0)
        self.grid.setColumnStretch(1, 1)
        self.layout.addLayout(self.grid)

        self.tool = tool
        self._update()

    def _makespacing(self, height):
        row = self.grid.rowCount()
        label = QtGui.QLabel(" ")
        label.setFixedHeight(height)
        self.grid.addWidget(label, row, 0, columnSpan=2)

    def _update(self):
        self.nameWidget.setText(self.tool.get_label())

        # Remove the current child widgets
        for i in reversed(range(self.grid.count())):
            self.grid.itemAt(i).widget().setParent(None)

        # Add tool location properties.
        row = self.grid.rowCount()
        label = QtGui.QLabel("<h4>Tool location</h4>")
        self.grid.addWidget(label, row, 0, columnSpan=2)
        self._add_property('Pocket', self.tool.pocket)

        # Add well-known properties first.
        self._makespacing(6)
        row = self.grid.rowCount()
        label = QtGui.QLabel("<h4>Common properties</h4>")
        self.grid.addWidget(label, row, 0, columnSpan=2)
        for param, value in self.tool.get_well_known_params():
            self._add_property(param.label, value)

        # Add custom properties under a separate title.
        self._makespacing(6)
        row = self.grid.rowCount()
        label = QtGui.QLabel("<h4>Tool-specific properties</h4>")
        self.grid.addWidget(label, row, 0, columnSpan=2)

        # Add entry fields per property
        for name, value in self.tool.get_custom_params():
            label = re.sub(r'([A-Z])', r' \1', name).strip()
            self._add_property(label, value)

    def _add_property(self, name, value):
        row = self.grid.rowCount()
        label = QtGui.QLabel(name)
        self.grid.addWidget(label, row, 0)
        entry = QtGui.QLineEdit(str(value))
        self.grid.addWidget(entry, row, 1)
