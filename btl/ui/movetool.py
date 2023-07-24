import os
from PySide import QtGui, QtCore
from ..const import icon_dir
from .util import load_ui

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "movetool.ui")

class MoveToolDialog(QtGui.QWidget):
    def __init__(self, tooldb, tool, copy=False, parent=None):
        super(MoveToolDialog, self).__init__(parent)
        self.tooldb = tooldb
        self.form = load_ui(ui_path)
        self.form.buttonBox.clicked.connect(self.form.reject)
        self.form.pushButton.clicked.connect(self._on_accept_clicked)
        self.form.listWidget.itemSelectionChanged.connect(self._update_state)
        self.form.listWidget.itemDoubleClicked.connect(self._on_accept_clicked)

        if copy:
            self.form.pushButton.setText("Copy Tool")

        self.libraries = {l.label: l for l in self.tooldb.get_libraries()}
        self.form.listWidget.addItems(sorted(self.libraries.keys()))

        self._update_state()

    def _update_state(self):
        self.form.pushButton.setEnabled(self.form.listWidget.count())

    def _on_accept_clicked(self, text):
        label = self.form.listWidget.currentItem().text()
        self.library = self.libraries[label]
        self.form.accept()

    def exec(self):
        return self.form.exec()
