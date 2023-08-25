import os
from PySide import QtGui, QtCore
from .util import load_ui
from .spinbox import PowerSpinBox, TorqueSpinBox, FeedSpinBox

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "machineeditor.ui")

class MachineEditor(QtGui.QWidget):
    def __init__(self, db, serializer, machine, parent=None):
        super(MachineEditor, self).__init__(parent)
        self.form = load_ui(ui_path, custom_widgets=(
            PowerSpinBox,
            TorqueSpinBox,
            FeedSpinBox,
        ))
        self.form.buttonBox.clicked.connect(self.form.close)
        self.form.toolButtonDelete.clicked.connect(self._on_delete_clicked)

        self.db = db
        self.serializer = serializer
        self.machine = machine

        self.form.lineEditName.textChanged.connect(machine.set_label)
        self.form.spinBoxMaxPower.valueChanged.connect(self._on_max_power_changed)
        self.form.spinBoxMaxTorque.valueChanged.connect(self._on_max_torque_changed)
        self.form.spinBoxPeakTorqueRpm.valueChanged.connect(self._on_peak_torque_rpm_changed)
        self.form.spinBoxMinRpm.editingFinished.connect(self._on_min_rpm_changed)
        self.form.spinBoxMaxRpm.editingFinished.connect(self._on_max_rpm_changed)
        self.form.spinBoxMinFeed.editingFinished.connect(self._on_min_feed_changed)
        self.form.spinBoxMaxFeed.editingFinished.connect(self._on_max_feed_changed)

        self.update()

    def _on_max_power_changed(self):
        value = self.form.spinBoxMaxPower.value()
        self.machine.set_max_power(value, self.form.spinBoxMaxPower.unit)

    def _on_max_torque_changed(self):
        value = self.form.spinBoxMaxTorque.value()
        self.machine.set_max_torque(value, self.form.spinBoxMaxTorque.unit)

    def _on_peak_torque_rpm_changed(self):
        value = self.form.spinBoxPeakTorqueRpm.value()
        self.machine.set_peak_torque_rpm(value)

    def _on_min_rpm_changed(self):
        value = self.form.spinBoxMinRpm.value()
        self.machine.set_min_rpm(value)
        self.update()

    def _on_max_rpm_changed(self):
        value = self.form.spinBoxMaxRpm.value()
        self.machine.set_max_rpm(value)
        self.update()

    def _on_min_feed_changed(self):
        value = self.form.spinBoxMinFeed.value()
        self.machine.set_min_feed(value, self.form.spinBoxMinFeed.unit)
        self.update()

    def _on_max_feed_changed(self):
        value = self.form.spinBoxMaxFeed.value()
        self.machine.set_max_feed(value, self.form.spinBoxMaxFeed.unit)
        self.update()

    def update(self):
        self.form.lineEditName.setText(self.machine.label)
        self.form.spinBoxMaxPower.setValueFromParam(self.machine.max_power)
        self.form.spinBoxMaxTorque.setValueFromParam(self.machine.max_torque)
        self.form.spinBoxPeakTorqueRpm.setValue(self.machine.peak_torque_rpm.v)
        self.form.spinBoxMinRpm.setValue(self.machine.min_rpm.v)
        self.form.spinBoxMaxRpm.setValue(self.machine.max_rpm.v)
        self.form.spinBoxMinFeed.setValueFromParam(self.machine.min_feed)
        self.form.spinBoxMaxFeed.setValueFromParam(self.machine.max_feed)

    def _on_delete_clicked(self):
        self.db.remove_machine(self.machine)
        self.db.serialize_machines(self.serializer)
        self.update()
        self.form.reject()

    def exec(self):
        return self.form.exec()
