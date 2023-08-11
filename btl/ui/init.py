import os
import FreeCAD, FreeCADGui
from PySide import QtGui
from .. import ToolDB, serializers
from ..const import icon_dir
from .library import LibraryUI

ICON_FILE = os.path.join(icon_dir, 'tool-library.svg')
prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Path")

def on_library_open_clicked():
    # Ensure that a library dir is defined in the preferences.
    lib_dir = prefs.GetString("LastPathToolLibrary", "~/.btl/Library")
    lib_base_dir = os.path.dirname(lib_dir)
    #FreeCAD.Console.PrintMessage("Library path is {}\n".format(lib_base_dir))

    # Note: Creating the serializer automatically initializes the library
    # directory.
    tool_db = ToolDB()
    lib_base_dir = os.path.expanduser(lib_base_dir)
    serializer = serializers.FCSerializer(lib_base_dir)

    dialog = LibraryUI(tool_db, serializer)
    dialog.show()

def on_workbench_activated(workbench):
    if workbench != 'PathWorkbench':
        return

    # Create a toolbar.
    mw = FreeCADGui.getMainWindow()
    toolbar = QtGui.QToolBar(mw)
    mw.addToolBar(toolbar)

    # Add the library editor button.
    tool_button = QtGui.QToolButton(mw)
    tool_button.setIcon(QtGui.QPixmap(ICON_FILE))
    tool_button.clicked.connect(on_library_open_clicked)
    toolbar.addWidget(tool_button)

    print('Better Tool Library loaded successfully.')

FreeCADGui.getMainWindow().workbenchActivated.connect(on_workbench_activated)
