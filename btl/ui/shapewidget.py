from PySide import QtGui, QtSvg, QtCore
from .util import qpixmap_from_svg, qpixmap_from_png

class ShapeWidget(QtGui.QWidget):
    def __init__ (self, shape, parent=None):
        super(ShapeWidget, self).__init__(parent)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignHCenter)

        self.shape = shape
        self.icon_size = QtCore.QSize(200, 235)
        self.icon_widget = QtGui.QLabel()
        self.layout.addWidget(self.icon_widget)

        self._update_icon()

    def _update_icon(self):
        icon_type, icon_bytes = self.shape.get_icon()
        if not icon_type:
            return
        icon_ba = QtCore.QByteArray(icon_bytes)

        if icon_type == 'svg':
            icon = qpixmap_from_svg(icon_ba, self.icon_size, self.devicePixelRatio())
        elif icon_type == 'png':
            icon = qpixmap_from_png(icon_ba, self.icon_size)

        self.icon_widget.setPixmap(icon)
