import sys
from PySide.QtGui import QApplication, QDoubleSpinBox
from PySide.QtGui import QValidator, QAbstractSpinBox
from ..units import distance_units, unit_normalize

class DistanceSpinBox(QDoubleSpinBox):
    def __init__(self, unit='mm', parent=None):
        self.unit = unit
        super().__init__(parent)
        self.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        #self.setKeyboardTracking(False)

    def textFromValue(self, value):
        decimals = self.decimals()
        fmt = f"{{:.{decimals}f}} {self.unit}"
        return fmt.format(value)

    def valueFromText(self, text):
        parts = text.split()
        if not parts:
            return 0.0

        try:
            value = float(parts[0])
        except ValueError:
            value = 0.0

        if len(parts) > 1:
            unit = unit_normalize(parts[1])
            if unit in distance_units:
                self.unit = unit
                self.valueChanged.emit(value)

        return value

    def fixup(self, text):
        value = self.valueFromText(text)
        return self.textFromValue(value)

    def validate(self, text, pos):
        return QValidator.Acceptable, text, pos

if __name__ == '__main__':
    app = QApplication(sys.argv)
    spin_box = DistanceSpinBox()
    spin_box.show()
    sys.exit(app.exec_())
