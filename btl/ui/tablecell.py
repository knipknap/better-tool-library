from PySide import QtGui, QtSvg, QtCore

class TwoLineTableCell(QtGui.QWidget):
    def __init__ (self, parent=None):
        super(TwoLineTableCell, self).__init__(parent)
        self.vbox = QtGui.QVBoxLayout()
        self.label_upper = QtGui.QLabel()
        self.label_upper.setStyleSheet("margin-top: 10px")
        self.label_lower = QtGui.QLabel()
        self.label_lower.setStyleSheet("margin-bottom: 10px")
        self.vbox.addWidget(self.label_upper)
        self.vbox.addWidget(self.label_lower)

        self.hbox = QtGui.QHBoxLayout()
        self.icon_widget = QtGui.QLabel()
        self.hbox.addWidget(self.icon_widget, 0)
        self.hbox.addLayout(self.vbox, 1)
        self.setLayout(self.hbox)

    def set_upper_text(self, text):
        self.label_upper.setText('<big><b>'+text+'</b></big>')

    def set_lower_text(self, text):
        self.label_lower.setText(text)

    def set_icon(self, pixmap):
        self.hbox.removeWidget(self.icon_widget)
        self.icon_widget = QtGui.QLabel()
        self.icon_widget.setPixmap(pixmap)
        self.hbox.insertWidget(0, self.icon_widget, 0)

    def set_icon_from_svg(self, svg):
        ba = QtCore.QByteArray(svg)
        svg_widget = QtSvg.QSvgWidget()
        svg_widget.setFixedSize(50, 60)
        svg_widget.load(ba)
        self.hbox.removeWidget(self.icon_widget)
        self.icon_widget = svg_widget
        self.hbox.insertWidget(0, svg_widget, 0)
