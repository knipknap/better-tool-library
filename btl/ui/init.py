import os
import FreeCAD, FreeCADGui
from PySide import QtGui
from .. import ToolDB, serializers
from .library import LibraryUI

__dir__ = os.path.dirname(__file__)
RESOURCE_PATH = os.path.join(os.path.dirname(os.path.dirname(__dir__)), 'resources')
ICON_FILE = os.path.join(RESOURCE_PATH, 'tool-library.svg')
prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Path")

def on_library_open_clicked():
    # Ensure that a library dir is defined in the preferences.
    lib_dir = prefs.GetString("LastPathToolLibrary", "~/.btl/Library")
    lib_base_dir = os.path.dirname(lib_dir)
    #FreeCAD.Console.PrintMessage("Library path is {}\n".format(lib_base_dir))

    # Note: Creating the serializer automatically initializes the library
    # directory.
    tool_db = ToolDB()
    serializer = serializers.FCSerializer(lib_base_dir)

    dialog = LibraryUI(tool_db, serializer)
    dialog.show()

def on_workbench_activated(workbench):
    if workbench != 'PathWorkbench':
        return

    # Find the main path menu
    mw = FreeCADGui.getMainWindow()
    pathMenu = mw.findChild(QtGui.QMenu, "&Path")

    # Find the Path Addons submenu
    submenus = [a.menu() for a in pathMenu.actions() if a.text() == "Path Addons"]
    if not submenus:
        print("Better tool library error: Path Addons menu item not found!")
        return
    addon_menu = submenus[0]

    # Create an action in this menu.
    action = QtGui.QAction(addon_menu)
    action.setText("Better Tool Library")
    action.setIcon(QtGui.QPixmap(ICON_FILE))
    #action.setStatusTip("Open the tool library manager")
    action.triggered.connect(on_library_open_clicked)
    addon_menu.addAction(action)

    # Also create a toolbar.
    toolbar = QtGui.QToolBar(mw) #"ToolLibrary")
    mw.addToolBar(toolbar)

    # Add the library editor button.
    tool_button = QtGui.QToolButton(mw)
    tool_button.setIcon(QtGui.QPixmap(ICON_FILE))
    #tool_button.setCheckable(True)
    tool_button.clicked.connect(on_library_open_clicked)
    toolbar.addWidget(tool_button)

    print('Better Tool Library loaded:', workbench)

FreeCADGui.getMainWindow().workbenchActivated.connect(on_workbench_activated)
