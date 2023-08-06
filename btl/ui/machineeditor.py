import os
from PySide import QtGui, QtCore
from .util import load_ui

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "machineeditor.ui")

class MachineEditor(QtGui.QWidget):
    def __init__(self, db, serializer, machine, parent=None):
        super(MachineEditor, self).__init__(parent)
        self.form = load_ui(ui_path)
        self.form.buttonBox.clicked.connect(self.form.close)
        self.form.toolButtonDelete.clicked.connect(self._on_delete_clicked)

        self.db = db
        self.serializer = serializer
        self.machine = machine

        self.form.lineEditName.textChanged.connect(machine.set_label)
        self.form.doubleSpinBoxMaxPower.valueChanged.connect(machine.set_max_power)
        self.form.doubleSpinBoxMaxTorque.valueChanged.connect(machine.set_max_torque)
        self.form.spinBoxMaxTorqueRpm.valueChanged.connect(machine.set_peak_torque_rpm)
        self.form.spinBoxMinRpm.editingFinished.connect(self._on_min_rpm_changed)
        self.form.spinBoxMaxRpm.editingFinished.connect(self._on_max_rpm_changed)
        self.form.spinBoxMinFeed.editingFinished.connect(self._on_min_feed_changed)
        self.form.spinBoxMaxFeed.editingFinished.connect(self._on_max_feed_changed)

        self.update()

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
        self.machine.set_min_feed(value)
        self.update()

    def _on_max_feed_changed(self):
        value = self.form.spinBoxMaxFeed.value()
        self.machine.set_max_feed(value)
        self.update()

    def update(self):
        self.form.lineEditName.setText(self.machine.label)
        self.form.doubleSpinBoxMaxPower.setValue(self.machine.max_power)
        self.form.doubleSpinBoxMaxTorque.setValue(self.machine.max_torque)
        self.form.spinBoxMaxTorqueRpm.setValue(self.machine.peak_torque_rpm)
        self.form.spinBoxMinRpm.setValue(self.machine.min_rpm)
        self.form.spinBoxMaxRpm.setValue(self.machine.max_rpm)
        self.form.spinBoxMinFeed.setValue(self.machine.min_feed)
        self.form.spinBoxMaxFeed.setValue(self.machine.max_feed)

    def _on_delete_clicked(self):
        self.db.remove_machine(self.machine)
        self.db.serialize_machines(self.serializer)
        self.update()
        self.form.reject()

    def exec(self):
        return self.form.exec()
