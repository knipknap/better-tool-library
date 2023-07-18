from PySide import QtGui, QtCore, QtUiTools

def load_ui(ui_path):
    loader = QtUiTools.QUiLoader()
    ui_file = QtCore.QFile(ui_path)
    ui_file.open(QtCore.QFile.ReadOnly)
    form = loader.load(ui_file)
    ui_file.close()
    return form
