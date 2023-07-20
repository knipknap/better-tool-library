import os
import re
import FreeCAD
import FreeCADGui
import Path
from PySide import QtGui, QtCore
from ..tool import Tool
from .util import load_ui
from .tablecell import TwoLineTableCell
from .shapeselector import ShapeSelector
from .tooleditor import ToolEditor

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "library.ui")

class LibraryUI():
    def __init__(self, tooldb, serializer):
        self.tooldb = tooldb
        self.serializer = serializer
        self.form = load_ui(ui_path)

        self.form.buttonBox.clicked.connect(self.form.close)
        self.form.listWidgetTools.itemDoubleClicked.connect(self.on_edit_tool_clicked)
        self.form.comboBoxLibrary.currentIndexChanged.connect(self.library_selected)
        self.form.lineEditSearch.setFocus()
        self.form.lineEditSearch.textChanged.connect(self.update_search)
        self.form.toolButtonAddLibrary.clicked.connect(self.on_create_library_clicked)
        self.form.toolButtonRemoveLibrary.clicked.connect(self.on_delete_library_clicked)
        self.form.pushButtonCreateTool.clicked.connect(self.on_create_tool_clicked)
        self.form.pushButtonEditTool.clicked.connect(self.on_edit_tool_clicked)
        self.form.pushButtonDeleteTool.clicked.connect(self.on_delete_tool_clicked)
        self.form.listWidgetTools.setSelectionMode(
            QtGui.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.load()

    def load(self):
        self.tooldb.deserialize(self.serializer)

        # Update the library dropdown menu.
        combo = self.form.comboBoxLibrary
        index = combo.currentIndex()
        combo.clear()
        combo.addItem('Unused tools')
        combo.insertSeparator(1)
        libraries = self.tooldb.get_libraries()
        for library in libraries:
            combo.addItem(library.label, library.id)

        # This also triggers an update of the tool list.
        combo.setCurrentIndex(index)
        if combo.currentIndex() == -1:
            combo.setCurrentIndex(2)

    def library_selected(self, index):
        self.update_tool_list()

    def get_selected_library(self):
        library_id = self.form.comboBoxLibrary.currentData()
        if not library_id:
            return
        return self.tooldb.get_library_by_id(library_id)

    def update_tool_list(self):
        # Find the selected library.
        library = self.get_selected_library()
        if library:
            tools = library.get_tools()
        else:
            tools = self.tooldb.get_unused_tools()

        # Update the tool list.
        listwidget = self.form.listWidgetTools
        listwidget.setStyleSheet("margin: 1px")
        listwidget.clear()
        for tool in tools:
            cell = TwoLineTableCell()
            cell.set_upper_text(tool.label)
            cell.set_lower_text(tool.shape.get_param_summary())
            cell.set_icon_from_svg(tool.shape.get_svg())

            widget_item = QtGui.QListWidgetItem(listwidget)
            widget_item.setSizeHint(cell.sizeHint())
            widget_item.setData(QtCore.Qt.UserRole, tool)
            listwidget.addItem(widget_item)
            listwidget.setItemWidget(widget_item, cell)

    def update_search(self):
        listwidget = self.form.listWidgetTools
        term = self.form.lineEditSearch.text()
        for i in range(listwidget.count()):
            item = listwidget.item(i)
            cell = listwidget.itemWidget(item)
            cell.highlight(term)
            item.setHidden(not cell.contains_text(term))

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

    def on_create_library_clicked(self):
        print("Create library") #TODO

    def on_delete_library_clicked(self):
        print("Delete library") #TODO

    def on_create_tool_clicked(self):
        selector = ShapeSelector(self.tooldb, self.serializer)
        selector.show()
        shape = selector.shape
        if not shape:
            return

        label = shape.get_label()
        tool = Tool('New {}'.format(label), shape)
        library = self.get_selected_library()
        pocket = library.get_next_pocket()
        editor = ToolEditor(tool, pocket)
        if not editor.show():
            return

        self.tooldb.add_tool(tool, library)
        library.assign_new_pocket(tool, editor.pocket)
        self.tooldb.serialize(self.serializer)
        self.load()

    def on_edit_tool_clicked(self):
        items = self.form.listWidgetTools.selectedItems()
        if not items:
            return

        tool = items[0].data(QtCore.Qt.UserRole)
        library = self.get_selected_library()
        if library:
            pocket = library.get_pocket_from_tool(tool)
            editor = ToolEditor(tool, pocket)
        else:
            editor = ToolEditor(tool)

        if not editor.show():
            # Reload the original values.
            self.load()
            return

        if library:
            library.assign_new_pocket(tool, editor.pocket)
        self.tooldb.serialize(self.serializer)
        self.load()

    def on_delete_tool_clicked(self):
        library = self.get_selected_library()
        items = self.form.listWidgetTools.selectedItems()
        if not items:
            return
        elif len(items) == 1 and library:
            tool = items[0].data(QtCore.Qt.UserRole)
            msg = 'Delete tool <b>{}</b> from library <b>{}</b>?'
            msg = msg.format(tool.get_label(), library.label)
        elif len(items) == 1:
            tool = items[0].data(QtCore.Qt.UserRole)
            msg = 'Delete unused tool <b>{}</b>?'.format(tool.get_label())
        elif len(items) > 1 and library:
            tool = items[0].data(QtCore.Qt.UserRole)
            msg = 'Delete {} selected tools from library <b>{}</b>?'
            msg = msg.format(len(items), library.label)
        else:
            msg = 'Delete {} unused tools from the library?'.format(len(items))

        msgBox = QtGui.QMessageBox()
        msgBox.setWindowTitle('Confirm tool deletion')
        msgBox.setText(msg)
        msgBox.addButton(QtGui.QMessageBox.Cancel)
        msgBox.addButton('Delete', QtGui.QMessageBox.AcceptRole)
        response = msgBox.exec()
        if response != QtGui.QMessageBox.AcceptRole:
            return

        for item in self.form.listWidgetTools.selectedItems():
            tool = item.data(QtCore.Qt.UserRole)
            self.tooldb.remove_tool(tool, library)

        self.tooldb.serialize(self.serializer)
        self.load()
