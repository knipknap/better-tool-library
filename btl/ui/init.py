import os
import FreeCAD, FreeCADGui
from PySide import QtGui
from PySide.QtCore import QT_TRANSLATE_NOOP
from .. import ToolDB, serializers, __version__
from ..const import icon_dir, translations_dir
from .library import LibraryUI
from .util import get_library_path_list, set_library_path

FreeCADGui.addLanguagePath(translations_dir)
ICON_FILE = os.path.join(icon_dir, 'tool-library.svg')
HAS_CAM = 'CAMWorkbench' in FreeCADGui.listWorkbenches()

class OpenBTL:
    """Opens the Better Tool Library dialog."""

    def GetResources(self):
        wb = 'CAM' if HAS_CAM else 'Path'
        return {
            'Pixmap': f'{wb}_ToolTable',
            'Accel': "P, T",
            "MenuText": QT_TRANSLATE_NOOP(
                "btl", "ToolBit Library editor"
            ),
            "ToolTip": QT_TRANSLATE_NOOP(
                "btl", "Open an editor to manage ToolBit libraries"
            ),
            "CmdType": "ForEdit",
        }

    def IsActive(self):
        return True

    def Activated(self):
        on_library_open_clicked()

class BitLibraryReplacer(object): # See hack below
    def open(self):
        on_library_open_clicked()

def on_library_open_clicked():
    tool_db = ToolDB()

    # Ensure that a library dir is defined in the preferences.
    serializer = None
    for lib_dir in get_library_path_list():
        lib_base_dir = os.path.dirname(lib_dir)
        lib_base_dir = os.path.expanduser(lib_base_dir)
        #FreeCAD.Console.PrintMessage("Trying to use library path {}\n".format(lib_base_dir))

        # Note: Creating the serializer automatically initializes the library
        # directory.
        try:
            serializer = serializers.FCSerializer(lib_base_dir)
            break
        except OSError as err:
            msg = f'Error writing to tool directory {lib_base_dir}: {err}.\n'
            FreeCAD.Console.PrintUserError(msg)

    if serializer is None:
        FreeCAD.Console.PrintUserError(
            "Unable to open Better Tool Library, because no writable tool directory was found.")
        return

    dialog = LibraryUI(tool_db, serializer, parent=FreeCADGui.getMainWindow())
    dialog.show()

def on_workbench_activated(workbench):
    if workbench not in ('PathWorkbench', 'CAMWorkbench'):
        return

    # Create a toolbar if it does not yet exist.
    tb_name = "btl_toolbar"
    mw = FreeCADGui.getMainWindow()
    toolbar = mw.findChild(QtGui.QToolBar, tb_name)
    if toolbar:
        return
    toolbar = QtGui.QToolBar(mw)
    toolbar.setObjectName(tb_name)
    mw.addToolBar(toolbar)

    # Add the library editor button.
    tool_button = QtGui.QToolButton(mw)
    tool_button.setIcon(QtGui.QPixmap(ICON_FILE))
    tool_button.clicked.connect(on_library_open_clicked)
    toolbar.addWidget(tool_button)

    # Hack: Replace FreeCAD tool library by BTL by monkey-patching
    # the path workbench.
    from Path.Tool.Gui import BitLibrary
    BitLibrary.ToolBitLibrary = BitLibraryReplacer

    print(f'Better Tool Library {__version__} loaded successfully.')

FreeCADGui.addCommand("Path_ToolBitLibraryOpen", OpenBTL())
FreeCADGui.addCommand("CAM_ToolBitLibraryOpen", OpenBTL())
FreeCADGui.getMainWindow().workbenchActivated.connect(on_workbench_activated)
