import os
from pathlib import Path
from PySide import QtGui, QtCore
import FreeCAD
from .util import load_ui

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "preferences.ui")
prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Path")

def tool_dir_from_lib_dir(lib_dir):
    base_dir = os.path.dirname(lib_dir)
    return os.path.expanduser(base_dir)

class PreferencesDialog(QtGui.QWidget):
    def __init__(self, serializer, parent=None):
        super(PreferencesDialog, self).__init__(parent)
        self.form = load_ui(ui_path)
        self.form.buttonBox.clicked.connect(self.form.close)
        self.form.pushButtonToolPath.clicked.connect(
            self.on_lib_path_select_clicked)
        self.serializer = serializer

        lib_path = prefs.GetString("LastPathToolLibrary", "~/.btl/tools")
        lib_dir = os.path.dirname(lib_path)
        self.form.lineEditToolPath.setText(lib_dir)

    def on_lib_path_select_clicked(self):
        filename = QtGui.QFileDialog.getOpenFileName(
             self.form,
             "Choose a Library file",
             dir=str(Path.home()),
             filter='FreeCAD library files .fctl (*.fctl)'
        )[0]
        if not filename:
            self.form.close()
            return

        lib_dir = os.path.dirname(filename)
        self.form.lineEditToolPath.setText(lib_dir)

    def exec(self):
        if not self.form.exec_():
            return
        lib_dir = self.form.lineEditToolPath.text()
        if not lib_dir:
            return

        tool_dir = tool_dir_from_lib_dir(lib_dir)
        self.serializer.set_tool_dir(tool_dir)
        prefs.SetString("LastPathToolLibrary", lib_dir)
        return True
