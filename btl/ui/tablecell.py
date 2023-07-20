import re
from PySide import QtGui, QtSvg, QtCore

def isub(text, old, repl_pattern):
    pattern = '|'.join(re.escape(o) for o in old)
    return re.sub('('+pattern+')', repl_pattern, text, flags=re.I)

class TwoLineTableCell(QtGui.QWidget):
    def __init__ (self, parent=None):
        super(TwoLineTableCell, self).__init__(parent)
        self.upper_text = ''
        self.lower_text = ''
        self.search_highlight = ''

        self.vbox = QtGui.QVBoxLayout()
        self.label_upper = QtGui.QLabel()
        self.label_upper.setStyleSheet("margin-top: 8px")
        self.label_lower = QtGui.QLabel()
        self.label_lower.setStyleSheet("margin-bottom: 8px")
        self.vbox.addWidget(self.label_upper)
        self.vbox.addWidget(self.label_lower)

        self.hbox = QtGui.QHBoxLayout()
        self.icon_widget = QtGui.QLabel()
        self.hbox.addWidget(self.icon_widget, 0)
        self.hbox.addLayout(self.vbox, 1)
        self.setLayout(self.hbox)

    def _highlight(self, text):
        if not self.search_highlight:
            return text
        highlight_fmt = r'<font style="background: yellow">\1</font>'
        return isub(text, self.search_highlight.split(' '), highlight_fmt)

    def _update(self):
        text = self._highlight(self.upper_text)
        self.label_upper.setText('<big><b>'+text+'</b></big>')

        text = self._highlight(self.lower_text)
        self.label_lower.setText(text)

    def set_upper_text(self, text):
        self.upper_text = text
        self._update()

    def set_lower_text(self, text):
        self.lower_text = text
        self._update()

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

    def contains_text(self, text):
        for term in text.split(' '):
            if term not in self.label_upper.text() \
                and term not in self.label_lower.text():
                return False
        return True

    def highlight(self, text):
        self.search_highlight = text
        self._update()
