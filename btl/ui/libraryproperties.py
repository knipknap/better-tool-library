import os
from PySide import QtGui, QtCore
from .util import load_ui

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "libraryproperties.ui")

class LibraryProperties(QtGui.QWidget):
    def __init__(self, library, new=False, parent=None):
        super(LibraryProperties, self).__init__(parent)
        self.form = load_ui(ui_path)
        self.form.buttonBox.clicked.connect(self.form.reject)
        self.form.pushButtonSave.clicked.connect(self._on_save_clicked)
        self.form.lineEditLibraryName.setText(library.label)
        self.form.lineEditLibraryName.textChanged.connect(self._on_name_changed)

        if new:
            self.form.pushButtonSave.setText("Create Library")

        self.library = library

    def _on_name_changed(self, text):
        self.library.label = text

    def _on_save_clicked(self, text):
        self.form.accept()

    def exec(self):
        return self.form.exec()
