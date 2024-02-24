#!/usr/bin/python
import os
import sys
import argparse
from PySide import QtCore, QtGui
from btl import ToolDB, serializers
from btl.const import resource_dir
from btl.i18n import install_translator
from btl.ui.library import LibraryUI

try:
    import FreeCAD
except ImportError:
    sys.stderr.write('error: FreeCAD not found. Make sure to include it in your PYTHONPATH')
    sys.exit(1)

parser = argparse.ArgumentParser(
    prog=__file__,
    description='Qt GUI to manage a tool library'
)

# Common arguments
parser.add_argument('-f', '--format',
                    help='the type (format) of the library',
                    choices=sorted(serializers.serializers.keys()),
                    default='freecad')
parser.add_argument('name',
                    help='the DB name. In case of a file based DB, this is the path to the DB')

def run():
    args = parser.parse_args()

    tool_db = ToolDB()
    serializer_cls = serializers.serializers[args.format]
    serializer = serializer_cls(args.name)

    QtGui.QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts, True)
    QtGui.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtGui.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QtGui.QApplication([])
    install_translator(app)
    window = LibraryUI(tool_db, serializer, standalone=True, parent=app)
    window.show()

if __name__ == '__main__':
    run()
