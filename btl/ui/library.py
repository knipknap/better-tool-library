import os
import re
import FreeCAD
import FreeCADGui
from pathlib import Path
from PySide import QtGui, QtCore
from .. import Library, Tool
from ..serializers import serializers, FCSerializer, LinuxCNCSerializer
from ..fcutil import add_tool_to_job, get_active_job
from .util import load_ui
from .tablecell import TwoLineTableCell
from .shapeselector import ShapeSelector
from .tooleditor import ToolEditor
from .libraryproperties import LibraryProperties
from .movetool import MoveToolDialog

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "library.ui")

class LibraryUI():
    def __init__(self, tooldb, serializer, standalone=False):
        self.tooldb = tooldb
        self.serializer = serializer
        self.standalone = standalone
        self.form = load_ui(ui_path)

        self.form.buttonBox.clicked.connect(self.form.close)
        self.form.listWidgetTools.itemDoubleClicked.connect(self.on_edit_tool_clicked)
        self.form.listWidgetTools.itemSelectionChanged.connect(self.update_search)
        self.form.listWidgetTools.setSelectionMode(
            QtGui.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.form.listWidgetTools.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.form.listWidgetTools.customContextMenuRequested.connect(self.on_right_click)

        self.form.lineEditSearch.setFocus()
        self.form.lineEditSearch.textChanged.connect(self.update_search)

        self.form.comboBoxLibrary.currentIndexChanged.connect(self.library_selected)
        self.form.toolButtonAddLibrary.clicked.connect(self.on_create_library_clicked)
        self.form.toolButtonRemoveLibrary.clicked.connect(self.on_delete_library_clicked)
        self.form.toolButtonEditLibrary.clicked.connect(self.on_edit_library_clicked)
        self.form.toolButtonExportLibrary.clicked.connect(self.on_export_library_clicked)

        self.form.pushButtonCreateTool.clicked.connect(self.on_create_tool_clicked)
        self.form.pushButtonDeleteTool.clicked.connect(self.on_delete_tool_clicked)
        self.form.pushButtonAddToJob.clicked.connect(self.on_add_to_job_clicked)

        if standalone:
            self.form.pushButtonAddToJob.hide()

        self.load()

        item = self.form.listWidgetTools.item(0)
        if item:
            self.form.listWidgetTools.setCurrentItem(item)

    def on_right_click(self, pos):
        menu = QtGui.QMenu(self.form.listWidgetTools)
        action = QtGui.QAction("Move to library...", self.form.listWidgetTools)
        action.triggered.connect(self.on_move_tool_clicked)
        menu.addAction(action)
        menu.exec_(self.form.listWidgetTools.mapToGlobal(pos))

    def get_selected_tools(self):
        return [i.data(QtCore.Qt.UserRole)
                for i in self.form.listWidgetTools.selectedItems()]

    def on_move_tool_clicked(self):
        tools = self.get_selected_tools()
        if not tools:
            return

        dialog = MoveToolDialog(self.tooldb, tools, parent=self.form)
        if dialog.exec() != QtGui.QDialog.Accepted:
            return
        if not dialog.library:
            return

        library = self.get_selected_library()
        for tool in tools:
            self.tooldb.add_tool(tool, dialog.library)
            library.remove_tool(tool)

        self.tooldb.serialize(self.serializer)
        self.load()

    def update_button_state(self):
        # Avoid calling get_active_job() in standalone mode - it doesn't support that
        has_job = self.standalone or bool(get_active_job())
        library = self.get_selected_library()
        tool_selected = bool(self.form.listWidgetTools.selectedItems())
        self.form.toolButtonRemoveLibrary.setEnabled(library is not None)
        self.form.toolButtonEditLibrary.setEnabled(library is not None)
        self.form.toolButtonExportLibrary.setEnabled(library is not None)
        self.form.pushButtonDeleteTool.setEnabled(tool_selected)
        self.form.pushButtonAddToJob.setEnabled(tool_selected and has_job)
        tt = '' if has_job else 'No job is selected in main window'
        self.form.pushButtonAddToJob.setToolTip(tt)

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
        self.update_button_state()

    def library_selected(self, index):
        self.update_tool_list()
        self.update_button_state()

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
        for tool in sorted(tools, key=lambda x: x.label, reverse=True):
            cell = TwoLineTableCell()
            cell.set_upper_text(tool.label)
            cell.set_lower_text(tool.shape.get_param_summary())
            cell.set_icon_from_shape(tool.shape)

            if library:
                pocket = library.get_pocket_from_tool(tool)
                cell.set_label(str(pocket))

            widget_item = QtGui.QListWidgetItem(listwidget)
            widget_item.setSizeHint(cell.sizeHint())
            widget_item.setData(QtCore.Qt.UserRole, tool)
            listwidget.addItem(widget_item)
            listwidget.setItemWidget(widget_item, cell)

        self.update_search()

    def update_search(self):
        listwidget = self.form.listWidgetTools
        term = self.form.lineEditSearch.text()
        for i in range(listwidget.count()):
            item = listwidget.item(i)
            cell = listwidget.itemWidget(item)
            if cell:
                cell.highlight(term)
                item.setHidden(not cell.contains_text(term))
        self.update_button_state()

    def show(self):
        self.form.exec()

    def on_create_library_clicked(self):
        library = Library('New Library')
        dialog = LibraryProperties(library, new=True)
        if dialog.exec() != QtGui.QDialog.Accepted:
            return

        self.tooldb.add_library(library)
        self.tooldb.serialize(self.serializer)
        self.load()

    def on_edit_library_clicked(self):
        library = self.get_selected_library()
        if not library:
            return

        dialog = LibraryProperties(library)
        if dialog.exec() != QtGui.QDialog.Accepted:
            return

        self.tooldb.serialize(self.serializer)
        self.load()

    def on_delete_library_clicked(self):
        library = self.get_selected_library()
        if not library:
            return

        msg = f'Are you sure you want to delete library <b>{library.label}</b>?' \
            + ' This action cannot be reversed.'
        msgBox = QtGui.QMessageBox()
        msgBox.setWindowTitle('Confirm library deletion')
        msgBox.setText(msg)
        msgBox.addButton(QtGui.QMessageBox.Cancel)
        msgBox.addButton('Delete', QtGui.QMessageBox.AcceptRole)
        response = msgBox.exec()
        if response != QtGui.QMessageBox.AcceptRole:
            return

        self.tooldb.remove_library(library)
        self.form.comboBoxLibrary.setCurrentIndex(0)
        self.tooldb.serialize(self.serializer)
        self.load()

    def _get_pattern_for_serializer(self, serializer):
        return '{} (*{})'.format(serializer.NAME, serializer.LIBRARY_EXT)

    def on_export_library_clicked(self):
        library = self.get_selected_library()
        if not library:
            return

        filters = {self._get_pattern_for_serializer(s): s
                   for s in serializers.values() if s != FCSerializer}
        selection = self._get_pattern_for_serializer(LinuxCNCSerializer)

        filename = QtGui.QFileDialog.getSaveFileName(
            self.form,
            "Export the tool library {}".format(library.label),
            dir=str(Path.home()),
            filter=';;'.join(sorted(filters)),
            selectedFilter=selection)
        if not filename:
            return

        filename, format = filename
        dirname = os.path.dirname(filename)
        serializer = filters[format](dirname)

        print("Selected", filename, serializer)
        library.serialize(serializer, filename)

    def get_tool_list_item(self, tool):
        listwidget = self.form.listWidgetTools
        for row in range(listwidget.count()):
            item = listwidget.item(row)
            current_tool = item.data(QtCore.Qt.UserRole)
            if current_tool == tool:
                return item
        return None

    def select_tool(self, tool):
        item = self.get_tool_list_item(tool)
        listwidget = self.form.listWidgetTools
        listwidget.setCurrentItem(item)
        listwidget.scrollToItem(item, QtGui.QAbstractItemView.EnsureVisible)

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
        if library:
            library.assign_new_pocket(tool, editor.pocket)
        self.tooldb.serialize(self.serializer)
        self.load()
        self.select_tool(tool)

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
            self.select_tool(tool)
            return

        self.tooldb.add_tool(tool)
        if library:
            library.assign_new_pocket(tool, editor.pocket)

        self.tooldb.serialize(self.serializer)
        self.load()
        self.select_tool(tool)

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

    def on_add_to_job_clicked(self):
        library = self.get_selected_library()
        items = self.form.listWidgetTools.selectedItems()
        if not items:
            return

        job = get_active_job()
        if not job:
            return

        for item in items:
            tool = item.data(QtCore.Qt.UserRole)
            pocket = library.get_pocket_from_tool(tool)
            assert pocket is not None
            add_tool_to_job(job, tool, pocket)
