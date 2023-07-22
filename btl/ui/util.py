import os
from PySide import QtCore, QtGui, QtUiTools, QtSvg

def load_ui(ui_path):
    loader = QtUiTools.QUiLoader()
    loader.setWorkingDirectory(os.path.dirname(__file__))
    ui_file = QtCore.QFile(ui_path)
    ui_file.open(QtCore.QFile.ReadOnly)
    form = loader.load(ui_file)
    ui_file.close()
    return form

def qpixmap_from_png(byte_array, icon_size):
    pixmap = QtGui.QPixmap(icon_size)
    pixmap.fill(QtGui.Qt.transparent)
    pixmap.loadFromData(byte_array)
    return pixmap.scaled(icon_size)

def qpixmap_from_svg(byte_array, icon_size):
    svg_widget = QtSvg.QSvgWidget()
    svg_widget.setFixedSize(icon_size)
    svg_widget.load(byte_array)
    svg_widget.setStyleSheet("background-color: rgba(0,0,0,0)")

    # Convert the QSvgWidget to QPixmap
    pixmap = QtGui.QPixmap(icon_size)
    pixmap.fill(QtGui.Qt.transparent)
    svg_widget.render(pixmap)
    return pixmap
