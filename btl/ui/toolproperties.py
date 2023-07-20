from functools import partial
from PySide import QtGui, QtSvg, QtCore
from .shapewidget import ShapeWidget
from ..params import EnumBase

class FuncValidator(QtGui.QValidator):
    def __init__(self, func, parent=None):
        super(FuncValidator, self).__init__(parent)
        self.func = func

    def validate(self, string, pos):
        if not self.func(string):
            return QtGui.QValidator.Intermediate, string, pos
        return QtGui.QValidator.Acceptable, string, pos

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

    def _get_widget_from_param(self, param, value):
        validator = FuncValidator(param.validate)
        shape = self.tool.shape
        if isinstance(param, EnumBase):
            widget = QtGui.QComboBox()
            for choice in param.choices:
                widget.addItem(choice)
            widget.currentTextChanged.connect(partial(shape.set_param, param))
        elif issubclass(param.type, str):
            widget = QtGui.QLineEdit(param.format(value))
            widget.setValidator(validator)
            widget.textChanged.connect(partial(shape.set_param, param))
        elif issubclass(param.type, bool):
            widget = QtGui.QCheckBox()
            widget.setCheckState(QtCore.Qt.Checked if value else QtCore.Qt.Unchecked)
            widget.stateChanged.connect(partial(shape.set_param, param))
        elif issubclass(param.type, int):
            widget = QtGui.QSpinBox()
            widget.setValue(int(value))
            widget.valueChanged.connect(partial(shape.set_param, param))
        elif issubclass(param.type, float):
            widget = QtGui.QDoubleSpinBox()
            widget.setValue(float(value))
            widget.valueChanged.connect(partial(shape.set_param, param))
        else:
            ctype = param.__class__.__name__
            ptype = param.type.__name__
            text = 'unsupported type {} ({})'.format(ctype, ptype)
            return QtGui.QLabel(text)
        return widget

    def _on_pocket_edited(self, text):
        self.tool.pocket = text

    def _add_entry(self, name, value, validator=None):
        row = self.grid.rowCount()
        label = QtGui.QLabel(name)
        self.grid.addWidget(label, row, 0)
        entry = QtGui.QLineEdit(value)
        if validator:
            entry.setValidator(validator)
        self.grid.addWidget(entry, row, 1)
        return entry

    def _add_property(self, param, value):
        row = self.grid.rowCount()
        label = QtGui.QLabel(param.label)
        self.grid.addWidget(label, row, 0)

        widget = self._get_widget_from_param(param, value)
        self.grid.addWidget(widget, row, 1)

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
        entry = self._add_entry('Pocket', self.tool.pocket)
        entry.textChanged.connect(self._on_pocket_edited)

        # Add custom properties under a separate title.
        self._makespacing(6)
        row = self.grid.rowCount()
        label = QtGui.QLabel("<h4>Tool-specific properties</h4>")
        self.grid.addWidget(label, row, 0, columnSpan=2)

        # Add entry fields per property.
        for param, value in self.tool.shape.get_params():
            self._add_property(param, value)
