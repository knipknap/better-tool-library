import sys
from PySide.QtGui import QApplication, QDoubleSpinBox
from PySide.QtGui import QValidator, QAbstractSpinBox
from ..units import parse_value, \
                    distance_units, \
                    torque_units, \
                    power_units

class UnitSpinBox(QDoubleSpinBox):
    def __init__(self,
                 unit,
                 allowed_units,
                 parent=None):
        self.unit = unit
        self.allowed_units = allowed_units
        super().__init__(parent)
        self.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        #self.setKeyboardTracking(False)

    def setValue(self, value, unit=None):
        if unit:
            self.unit = unit
        super().setValue(value)

    def setValueFromParam(self, param):
        self.setValue(param.v, param.unit)

    def textFromValue(self, value):
        decimals = self.decimals()
        fmt = f"{{:.{decimals}f}} {self.unit}"
        return fmt.format(value)

    def valueFromText(self, text):
        try:
            value, unit = parse_value(text)
        except AttributeError:
            return .0

        if unit in self.allowed_units:
            self.unit = unit
            self.valueChanged.emit(value)

        return value

    def validate(self, text, pos):
        return QValidator.Acceptable, text, pos

class DistanceSpinBox(UnitSpinBox):
    def __init__(self,
                 parent=None,
                 unit='mm'):
        super().__init__(unit=unit,
                         allowed_units=distance_units,
                         parent=parent)

class TorqueSpinBox(UnitSpinBox):
    def __init__(self,
                 parent=None,
                 unit='Nm'):
        super().__init__(unit=unit,
                         allowed_units=torque_units,
                         parent=parent)

class PowerSpinBox(UnitSpinBox):
    def __init__(self,
                 parent=None,
                 unit='kW'):
        super().__init__(unit=unit,
                         allowed_units=power_units,
                         parent=parent)

class FeedSpinBox(UnitSpinBox):
    def __init__(self,
                 parent=None,
                 unit='mm/min'):
        super().__init__(unit=unit,
                         allowed_units=('mm/min', 'ft/min'),
                         parent=parent)
        self.setDecimals(0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    spin_box = DistanceSpinBox()
    spin_box.show()
    sys.exit(app.exec_())
