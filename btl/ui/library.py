import os
import re
import FreeCAD
import FreeCADGui
import Path
from PySide import QtGui, QtCore
from .tablecell import TwoLineTableCell

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "library.ui")

def pixmap_from_svg_string(string):
    ba = QtCore.QByteArray(string)
    pixmap = QtGui.QPixmap()
    pixmap.loadFromData(ba, "SVG")
    return pixmap

def pixmap_from_tool(tool):
    svg = tool.get_shape_svg()
    if svg:
        return pixmap_from_svg_string(svg)
    return None

class LibraryUI():
    def __init__(self, tooldb, serializer):
        self.tooldb = tooldb
        self.serializer = serializer
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.form.buttonBox.clicked.connect(self.form.close)
        self.form.comboBoxLibrary.currentIndexChanged.connect(self.library_selected)

        self.load()

    def load(self):
        self.tooldb.deserialize(self.serializer)

        # Update the library dropdown menu.
        combo = self.form.comboBoxLibrary
        combo.clear()
        libraries = self.tooldb.get_libraries()
        for library in libraries:
            combo.addItem(library.label, library.id)

        # This also triggers an update of the tool list.
        if combo.currentIndex() == -1:
            combo.setCurrentIndex(0)

    def library_selected(self, index):
        self.update_tool_list()

    def update_tool_list(self):
        # Find the selected library.
        library_id = self.form.comboBoxLibrary.currentData()
        if not library_id:
            return
        library = self.tooldb.get_library_by_id(library_id)

        # Update the tool list.
        listwidget = self.form.listWidgetTools
        listwidget.clear()
        for tool in library.tools:
            cell = TwoLineTableCell()
            cell.set_upper_text(tool.label)
            cell.set_lower_text(tool.get_param_summary())
            cell.set_icon_from_svg(tool.get_shape_svg())

            widget_item = QtGui.QListWidgetItem(listwidget)
            widget_item.setSizeHint(cell.sizeHint())
            listwidget.addItem(widget_item)
            listwidget.setItemWidget(widget_item, cell)

    def show(self):
        self.form.exec()

    def add_tool_to_job(self, tool):
        jobs = FreeCAD.ActiveDocument.findObjects("Path::FeaturePython", "Job.*")
        for job in jobs:
            for idx, tc in enumerate(job.Tools.Group):
                print(tc.Label) #FIXME
                #tc.HorizFeed = hfeed
                #tc.VertFeed = vfeed
                #tc.SpindleSpeed = float(rpm)
