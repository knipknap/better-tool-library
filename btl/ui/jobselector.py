import os
from PySide import QtGui, QtCore
from ..fcutil import get_jobs
from .util import load_ui

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "jobselector.ui")

class JobSelector(QtGui.QWidget):
    def __init__(self, parent=None):
        super(JobSelector, self).__init__(parent)
        self.form = load_ui(ui_path)
        self.form.buttonBox.clicked.connect(self.form.reject)
        self.form.pushButtonAdd.clicked.connect(self._on_add_clicked)

        self.form.listWidget.itemDoubleClicked.connect(self.form.accept)
        self.form.listWidget.itemSelectionChanged.connect(self.update)
        self.form.listWidget.setSelectionMode(
            QtGui.QAbstractItemView.SelectionMode.ExtendedSelection)

        listwidget = self.form.listWidget
        for job in get_jobs():
            item = QtGui.QListWidgetItem(job.Label, listwidget)
            item.setData(QtCore.Qt.UserRole, job)
            listwidget.addItem(item)

        item = listwidget.item(0)
        if item:
            listwidget.setCurrentItem(item)

    def get_selected_jobs(self):
        return [i.data(QtCore.Qt.UserRole)
                for i in self.form.listWidget.selectedItems()]

    def update(self):
        job_selected = bool(self.form.listWidget.selectedItems())
        self.form.pushButtonAdd.setEnabled(job_selected)

    def _on_add_clicked(self, text):
        self.form.accept()

    def exec(self):
        if not self.form.exec():
            return
        return self.get_selected_jobs()
