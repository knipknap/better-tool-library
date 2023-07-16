from PySide import QtGui, QtSvg, QtCore

class TwoLineTableCell(QtGui.QWidget):
    def __init__ (self, parent=None):
        super(TwoLineTableCell, self).__init__(parent)
        self.textQVBoxLayout = QtGui.QVBoxLayout()
        self.textUpQLabel    = QtGui.QLabel()
        self.textDownQLabel  = QtGui.QLabel()
        self.textQVBoxLayout.addWidget(self.textUpQLabel)
        self.textQVBoxLayout.addWidget(self.textDownQLabel)
        self.allQHBoxLayout  = QtGui.QHBoxLayout()
        self.icon_widget = QtGui.QLabel()
        self.allQHBoxLayout.addWidget(self.icon_widget, 0)
        self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)
        self.setLayout(self.allQHBoxLayout)
        #self.icon_widget.setGeometry(48, 48, 48, 48)

    def set_upper_text(self, text):
        self.textUpQLabel.setText('<big><b>'+text+'</b></big>')

    def set_lower_text(self, text):
        self.textDownQLabel.setText(text)

    def set_icon(self, pixmap):
        self.allQHBoxLayout.removeWidget(self.icon_widget)
        self.icon_widget = QtGui.QLabel()
        self.icon_widget.setPixmap(pixmap)
        self.allQHBoxLayout.insertWidget(0, self.icon_widget, 0)

    def set_icon_from_svg(self, svg):
        ba = QtCore.QByteArray(svg)
        svg_widget = QtSvg.QSvgWidget()
        svg_widget.setFixedSize(48, 48)
        svg_widget.load(ba)
        self.allQHBoxLayout.removeWidget(self.icon_widget)
        self.icon_widget = svg_widget
        self.allQHBoxLayout.insertWidget(0, svg_widget, 0)
