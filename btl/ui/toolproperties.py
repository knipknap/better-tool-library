from functools import partial
from PySide import QtGui, QtSvg, QtCore
from ..params import EnumBase, AngleBase

class FuncValidator(QtGui.QValidator):
    def __init__(self, func, parent=None):
        super(FuncValidator, self).__init__(parent)
        self.func = func

    def validate(self, string, pos):
        if not self.func(string):
            return QtGui.QValidator.Intermediate, string, pos
        return QtGui.QValidator.Acceptable, string, pos

class ToolProperties(QtGui.QWidget):
    pocketChanged = QtCore.Signal(int)

    def __init__ (self, tool, pocket=None, parent=None):
        super(ToolProperties, self).__init__(parent)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignHCenter)

        self.grid = QtGui.QGridLayout()
        self.grid.setColumnStretch(0, 0)
        self.grid.setColumnStretch(1, 1)
        self.layout.addLayout(self.grid)

        self.tool = tool
        self.pocket = pocket
        self._update()

    def _get_widget_from_param(self, param, value):
        validator = FuncValidator(param.validate)
        shape = self.tool.shape
        if isinstance(param, EnumBase):
            widget = QtGui.QComboBox()
            for choice in param.choices:
                widget.addItem(choice)
            widget.setCurrentText(value)
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
            widget.setValue(int(value or 0))
            widget.setSuffix(' '+param.unit if param.unit else '')
            widget.valueChanged.connect(partial(shape.set_param, param))
        elif issubclass(param.type, float):
            widget = QtGui.QDoubleSpinBox()
            widget.setDecimals(3)
            widget.setValue(float(value or 0))
            widget.setSuffix(' '+param.unit if param.unit else '')
            widget.valueChanged.connect(partial(shape.set_param, param))
        else:
            ctype = param.__class__.__name__
            ptype = param.type.__name__
            text = 'unsupported type {} ({})'.format(ctype, ptype)
            return QtGui.QLabel(text)

        return widget

    def _add_property_from_widget(self, widget, name, value, abbreviation=None):
        if abbreviation:
            name = '{} ({}):'.format(name, abbreviation)
        else:
            name += ':'
        row = self.grid.rowCount()
        label = QtGui.QLabel(name)
        self.grid.addWidget(label, row, 0)
        self.grid.addWidget(widget, row, 1)
        return widget

    def _add_entry(self, name, value, validator=None, abbreviation=None):
        entry = QtGui.QLineEdit(value)
        if validator:
            entry.setValidator(validator)
        return self._add_property_from_widget(entry, name, value, abbreviation)

    def _add_property(self, param, value, abbreviation=None):
        widget = self._get_widget_from_param(param, value)
        self._add_property_from_widget(widget, param.label, value, abbreviation)

    def _makespacing(self, height):
        row = self.grid.rowCount()
        label = QtGui.QLabel(" ")
        label.setFixedHeight(height)
        self.grid.addWidget(label, row, 0)

    def _update(self):
        # Remove the current child widgets
        for i in reversed(range(self.grid.count())):
            self.grid.itemAt(i).widget().setParent(None)

        # Add tool location properties.
        if self.pocket is not None:
            row = self.grid.rowCount()
            label = QtGui.QLabel("<h4>Tool location</h4>")
            # Note: Some PyQt versions do not support columnSpan
            self.grid.addWidget(label, row, 0)
            spinner = QtGui.QSpinBox()
            spinner.setValue(self.pocket or 0)
            spinner.valueChanged.connect(self.pocketChanged.emit)
            self._add_property_from_widget(spinner, 'Pocket', self.pocket)
            self._makespacing(6)

        # Add well-known properties under a separate title.
        row = self.grid.rowCount()
        label = QtGui.QLabel("<h4>Well-known properties</h4>")
        # Note: Some PyQt versions do not support columnSpan
        self.grid.addWidget(label, row, 0)

        # Add entry fields per property.
        for param, value in self.tool.shape.get_well_known_params():
            abbr = self.tool.shape.get_abbr(param)
            self._add_property(param, value, abbr)
        self._makespacing(6)

        # Add remaining properties under a separate title.
        row = self.grid.rowCount()
        label = QtGui.QLabel("<h4>Tool-specific properties</h4>")
        # Note: Some PyQt versions do not support columnSpan
        self.grid.addWidget(label, row, 0)

        # Add entry fields per property.
        params = sorted(self.tool.shape.get_non_well_known_params(),
                        key=lambda x: x[0].name)
        for param, value in params:
            abbr = self.tool.shape.get_abbr(param)
            self._add_property(param, value, abbr)
        self._makespacing(6)
