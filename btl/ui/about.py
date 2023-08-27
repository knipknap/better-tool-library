import os
from PySide import QtGui, QtCore
from btl import __version__
from .util import load_ui

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "about.ui")

class AboutDialog(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.form = load_ui(ui_path)
        self.form.buttonBox.clicked.connect(self.form.reject)
        self.form.labelVersion.setText(__version__)

    def exec(self):
        return self.form.exec()
