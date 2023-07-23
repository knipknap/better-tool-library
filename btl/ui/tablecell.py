import re
from PySide import QtGui, QtSvg, QtCore
from .util import qpixmap_from_svg, qpixmap_from_png

def isub(text, old, repl_pattern):
    pattern = '|'.join(re.escape(o) for o in old)
    return re.sub('('+pattern+')', repl_pattern, text, flags=re.I)

class TwoLineTableCell(QtGui.QWidget):
    def __init__ (self, parent=None):
        super(TwoLineTableCell, self).__init__(parent)
        self.right_text = ''
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
        self.label_right = QtGui.QLabel()
        self.label_right.setMinimumWidth(40)
        self.label_right.setTextFormat(QtCore.Qt.RichText)
        self.label_right.setAlignment(QtCore.Qt.AlignCenter)
        self.hbox.addWidget(self.label_right, 0)
        self.setLayout(self.hbox)

    def _highlight(self, text):
        if not self.search_highlight:
            return text
        highlight_fmt = r'<font style="background: yellow">\1</font>'
        return isub(text, self.search_highlight.split(' '), highlight_fmt)

    def _update(self):
        text = self._highlight(self.right_text)
        text = "Pocket\n<h3>{}</h3>".format(text) if text else ''
        self.label_right.setText(text)

        text = self._highlight(self.upper_text)
        self.label_upper.setText('<big><b>'+text+'</b></big>')

        text = self._highlight(self.lower_text)
        self.label_lower.setText(text)
        self.label_lower.setText('<font color="#444">'+text+'</font>')

    def set_label(self, text):
        self.right_text = text
        self._update()

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

    def set_icon_from_shape(self, shape):
        icon_type, icon_bytes = shape.get_icon()
        if not icon_type:
            return
        icon_ba = QtCore.QByteArray(icon_bytes)
        icon_size = QtCore.QSize(50, 60)

        if icon_type == 'svg':
            icon = qpixmap_from_svg(icon_ba, icon_size)
        elif icon_type == 'png':
            icon = qpixmap_from_png(icon_ba, icon_size)

        self.set_icon(icon)

    def contains_text(self, text):
        for term in text.lower().split(' '):
            if term not in self.upper_text.lower() \
                and term not in self.lower_text.lower() \
                and term not in self.right_text.lower():
                return False
        return True

    def highlight(self, text):
        self.search_highlight = text
        self._update()
