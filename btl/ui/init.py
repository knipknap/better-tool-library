import os
import FreeCAD, FreeCADGui
from PySide import QtGui
from .. import ToolDB, serializers
from ..const import icon_dir
from .library import LibraryUI

ICON_FILE = os.path.join(icon_dir, 'tool-library.svg')
prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Path")


parentWbName = 'Path'
parentWbFullName = parentWbName + 'Workbench'
addonTitle = 'Better Tool Library'
# print('addonTitle', addonTitle)

addon_menuName = parentWbName + ' ' + 'Addons'
addon_menuObjName = parentWbName + '_' + 'Addons'
existingMenu = 'Path Dressup'       # existing wb menu name to insert this addon menu ABOVE
iconFileName = 'tool-library.svg'
statusText = 'Better Tool Library.'


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

    # Create a toolbar.
    mw = FreeCADGui.getMainWindow()
    toolbar = QtGui.QToolBar(mw)
    mw.addToolBar(toolbar)

    # ===========================================================
    mw = FreeCADGui.getMainWindow()
    addon_menu = None

    # Find the Workbench menu
    wb_menu = mw.findChild(QtGui.QMenu, "&" + parentWbName)

    for menu in wb_menu.actions():
        if menu.text() == addon_menuName:
            # Already exists, save it.
            addon_menu = menu.menu()
            break
    if addon_menu is None:
        # create a new addon menu
        addon_menu = QtGui.QMenu(addon_menuName)
        addon_menu.setObjectName(addon_menuObjName)
        existing_menu_entry = mw.findChild(QtGui.QMenu, existingMenu)
        wb_menu.insertMenu(existing_menu_entry.menuAction(), addon_menu)

    action = QtGui.QAction(addon_menu)
    action.setText(addonTitle)
    # action.setIcon(QtGui.QPixmap(getIcon(ICON_FILE)))
    action.setStatusTip(statusText)

    action.triggered.connect(on_library_open_clicked)
    addon_menu.addAction(action)
    # ===========================================================




    # Add the library editor button.
    tool_button = QtGui.QToolButton(mw)
    tool_button.setIcon(QtGui.QPixmap(ICON_FILE))
    tool_button.clicked.connect(on_library_open_clicked)
    toolbar.addWidget(tool_button)

    print('Better Tool Library loaded successfully.')

FreeCADGui.getMainWindow().workbenchActivated.connect(on_workbench_activated)
