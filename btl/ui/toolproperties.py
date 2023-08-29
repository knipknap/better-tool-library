from functools import partial
from PySide import QtGui, QtSvg, QtCore
from ..shape import get_property_label_from_name
from ..i18n import translate
from ..params import DistanceParam
from .spinbox import DistanceSpinBox

class FuncValidator(QtGui.QValidator):
    def __init__(self, func, parent=None):
        super(FuncValidator, self).__init__(parent)
        self.func = func

    def validate(self, string, pos):
        if not self.func(string):
            return QtGui.QValidator.Intermediate, string, pos
        return QtGui.QValidator.Acceptable, string, pos

class PropertyWidget(QtGui.QWidget):
    def __init__ (self, parent=None):
        super(PropertyWidget, self).__init__(parent)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignHCenter)

        self.grid = QtGui.QGridLayout()
        self.grid.setColumnStretch(0, 0)
        self.grid.setColumnStretch(1, 1)
        self.layout.addLayout(self.grid)

    def _get_widget_from_param(self, param, setter):
        validator = FuncValidator(param.validate)
        if param.choices is not None:
            widget = QtGui.QComboBox()
            for choice in param.choices:
                widget.addItem(choice)
            widget.setCurrentText(param.format())
            widget.currentTextChanged.connect(setter)
        elif isinstance(param, DistanceParam):
            widget = DistanceSpinBox(unit=param.unit)
            widget.setMaximum(param.max or 99999)
            widget.setDecimals(param.decimals)
            widget.setValue(float(param.v or 0))
            def distance_setter(value):
                param.v = value
                param.unit = widget.unit
                setter(param)
            widget.valueChanged.connect(distance_setter)
        elif issubclass(param.type, str):
            widget = QtGui.QLineEdit(param.format())
            widget.setValidator(validator)
            widget.textChanged.connect(setter)
        elif issubclass(param.type, bool):
            widget = QtGui.QCheckBox()
            widget.setCheckState(QtCore.Qt.Checked if param.v else QtCore.Qt.Unchecked)
            widget.stateChanged.connect(setter)
        elif issubclass(param.type, int):
            widget = QtGui.QSpinBox()
            widget.setValue(int(param.v or 0))
            widget.setSuffix(' '+param.unit if param.unit else '')
            widget.valueChanged.connect(setter)
        elif issubclass(param.type, float):
            widget = QtGui.QDoubleSpinBox()
            widget.setMaximum(param.max or 99999)
            widget.setDecimals(param.decimals)
            widget.setStepType(QtGui.QAbstractSpinBox.AdaptiveDecimalStepType)
            widget.setValue(float(param.v or 0))
            widget.setSuffix(' '+param.unit if param.unit else '')
            widget.valueChanged.connect(setter)
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

    def _makespacing(self, height):
        row = self.grid.rowCount()
        label = QtGui.QLabel(" ")
        label.setFixedHeight(height)
        self.grid.addWidget(label, row, 0)

class ToolProperties(PropertyWidget):
    toolNoChanged = QtCore.Signal(int)

    def __init__ (self, tool, tool_no=None, parent=None):
        super(ToolProperties, self).__init__(parent)
        self.tool = tool
        self.tool_no = tool_no

        # Add tool location properties.
        row = self.grid.rowCount()
        lbl = translate('btl', 'Tool location')
        label = QtGui.QLabel(f"<h4>{lbl}</h4>")
        # Note: Some PyQt versions do not support columnSpan
        self.grid.addWidget(label, row, 0)

        row = self.grid.rowCount()
        lbl = translate('btl', 'Tool ID:')
        label = QtGui.QLabel(lbl)
        self.grid.addWidget(label, row, 0)
        label = QtGui.QLabel(tool.id)
        label.setTextInteractionFlags(QtGui.Qt.TextSelectableByKeyboard \
                                     |QtGui.Qt.TextSelectableByMouse \
                                     |QtGui.Qt.StrongFocus)
        self.grid.addWidget(label, row, 1)

        if self.tool_no is not None:
            spinner = QtGui.QSpinBox()
            spinner.setValue(self.tool_no or 0)
            spinner.setMaximum(99999999)
            spinner.valueChanged.connect(self.toolNoChanged.emit)
            lbl = translate('btl', 'Tool Number')
            self._add_property_from_widget(spinner, lbl, self.tool_no)

        spinner = QtGui.QSpinBox()
        spinner.setValue(tool.pocket or 0)
        spinner.setMaximum(99999999)
        spinner.setSpecialValueText(translate('btl', 'None'))
        spinner.valueChanged.connect(tool.set_pocket)
        lbl = translate('btl', 'Pocket')
        self._add_property_from_widget(spinner, lbl, self.tool.pocket)
        self._makespacing(6)

        # Add well-known properties under a separate title.
        row = self.grid.rowCount()
        lbl = translate('btl', 'Dimensions')
        label = QtGui.QLabel(f"<h4>{lbl}</h4>")
        # Note: Some PyQt versions do not support columnSpan
        self.grid.addWidget(label, row, 0)

        # Add entry fields per property.
        params = sorted(self.tool.shape.params.values(),
                        key=lambda p: get_property_label_from_name(p.name, p.label))
        for param in params:
            if param.group == 'Shape':
                abbr = self.tool.shape.get_abbr(param)
                self._add_property(param, abbr)
        self._makespacing(6)

        # Add remaining properties under a separate title.
        row = self.grid.rowCount()
        lbl = translate('btl', 'Other properties')
        label = QtGui.QLabel(f"<h4>{lbl}</h4>")
        self.grid.addWidget(label, row, 0)

        # Add entry fields per property.
        for param in params:
            if param.group != 'Shape':
                abbr = self.tool.shape.get_abbr(param)
                self._add_property(param, abbr)

        self._makespacing(6)
        row = self.grid.rowCount()
        self.grid.setRowStretch(row, 1)

    def _add_property(self, param, abbreviation=None):
        setter = partial(self.tool.shape.set_param, param.name)
        widget = self._get_widget_from_param(param, setter)
        label = get_property_label_from_name(param.name, param.label)
        self._add_property_from_widget(widget, label, param.v, abbreviation)

class ToolAttributes(PropertyWidget):
    def __init__ (self, tool, parent=None):
        super(ToolAttributes, self).__init__(parent)
        self.tool = tool

        row = self.grid.rowCount()
        lbl = translate('btl', 'Unknown tool attributes')
        label = QtGui.QLabel(f"<h4>{lbl}</h4>")
        self.grid.addWidget(label, row, 0)

        # Add entry fields per property.
        params = sorted(tool.get_non_btl_attribs())
        for name in params:
            param = tool.get_attrib(name)
            self._add_property(param)
        if not params:
            row = self.grid.rowCount()
            lbl = translate('btl', 'No unknown attributes found')
            label = QtGui.QLabel(f"<i>{lbl}</i>")
            self.grid.addWidget(label, row, 0)

        self._makespacing(6)
        row = self.grid.rowCount()
        self.grid.setRowStretch(row, 1)

    def _add_property(self, param):
        setter = partial(self.tool.set_attrib, param.name)
        widget = self._get_widget_from_param(param, setter)
        label = get_property_label_from_name(param.name, param.label)
        self._add_property_from_widget(widget, label, param.v)
