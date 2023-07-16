from PySide import QtGui

class TwoLineTableCell(QtGui.QWidget):
    def __init__ (self, parent=None):
        super(TwoLineTableCell, self).__init__(parent)
        self.textQVBoxLayout = QtGui.QVBoxLayout()
        self.textUpQLabel    = QtGui.QLabel()
        self.textDownQLabel  = QtGui.QLabel()
        self.textQVBoxLayout.addWidget(self.textUpQLabel)
        self.textQVBoxLayout.addWidget(self.textDownQLabel)
        self.allQHBoxLayout  = QtGui.QHBoxLayout()
        self.iconQLabel      = QtGui.QLabel()
        self.allQHBoxLayout.addWidget(self.iconQLabel, 0)
        self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)
        self.setLayout(self.allQHBoxLayout)

        #self.textUpQLabel.setStyleSheet('''color: rgb(0, 0, 255);''')

    def set_upper_text(self, text):
        self.textUpQLabel.setText('<big><b>'+text+'</b></big>')

    def set_lower_text(self, text):
        self.textDownQLabel.setText(text)

    def set_icon(self, image_file):
        self.iconQLabel.setPixmap(QtGui.QPixmap(image_file))

