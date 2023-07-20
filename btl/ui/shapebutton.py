import re
from PySide import QtGui, QtSvg, QtCore

class ShapeButton(QtGui.QToolButton):
    def __init__ (self, shape, parent=None):
        super(ShapeButton, self).__init__(parent)
        self.shape = shape

        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.setText(shape.get_label())

        self.setFixedSize(128, 128)
        self.setBaseSize(128, 128)
        size = QtCore.QSize(71, 100)
        self.setIconSize(size)

        self.set_icon_from_svg(shape.get_svg())

    def set_text(self, text):
        self.label.setText(text)

    def set_icon_from_svg(self, svg):
        if not svg:
            return

        # Render the SVG bytestring.
        ba = QtCore.QByteArray(svg)
        svg_widget = QtSvg.QSvgWidget()
        svg_widget.setFixedSize(self.iconSize())
        svg_widget.load(ba)
        svg_widget.setStyleSheet("background-color: rgba(0,0,0,0)")

        # Convert the QSvgWidget to QPixmap
        pixmap = QtGui.QPixmap(self.iconSize())
        pixmap.fill(QtGui.Qt.transparent)
        svg_widget.render(pixmap)

        self.setIcon(QtGui.QIcon(pixmap))
