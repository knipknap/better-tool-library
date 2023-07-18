from PySide import QtGui, QtSvg, QtCore

class ToolProperties(QtGui.QWidget):
    def __init__ (self, tool, parent=None):
        super(ToolProperties, self).__init__(parent)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignHCenter)
        self.grid = QtGui.QGridLayout()
        self.grid.setColumnStretch(0, 0)
        self.grid.setColumnStretch(1, 1)
        self.layout.addLayout(self.grid)

        self.load_properties(tool)

    def load_properties(self, tool):
        # Remove the current child widgets
        for i in reversed(range(self.grid.count())):
            self.grid.itemAt(i).widget().setParent(None)

        # Add entry fields per property
        for prop in sorted(tool.shape.get_properties()):
            self.add_property(*prop)

    def add_property(self, group, name, value, unit, enum):
        row = self.grid.rowCount()
        label = QtGui.QLabel(name)
        self.grid.addWidget(label, row, 0)
        entry = QtGui.QLineEdit(str(value))
        self.grid.addWidget(entry, row, 1)
