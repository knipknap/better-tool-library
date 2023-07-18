from PySide import QtGui, QtSvg, QtCore

class ShapeWidget(QtGui.QWidget):
    def __init__ (self, shape, parent=None):
        super(ShapeWidget, self).__init__(parent)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignHCenter)

        self.shape = shape
        self.icon_size = QtCore.QSize(200, 235)

        self.set_icon_from_svg(shape.get_svg())

    def replace_widget(self, child):
        # Remove the current child widgets
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)

        # Add the new child widget (in this case, a different label)
        self.layout.addWidget(child)

    def set_icon_from_svg(self, svg):
        if not svg:
            return

        # Render the SVG bytestring.
        ba = QtCore.QByteArray(svg)
        svg_widget = QtSvg.QSvgWidget()
        svg_widget.setFixedSize(self.icon_size)
        svg_widget.load(ba)
        svg_widget.setStyleSheet("background-color: rgba(0,0,0,0)")

        self.replace_widget(svg_widget)
