import os
import json
from pathlib import Path
from PySide import QtGui, QtCore
from PySide.QtCore import Qt, QMimeData
from PySide.QtGui import QApplication, QShortcut
from ..i18n import translate
from .. import Library, Tool, serializers
from ..serializers import serializers, FCSerializer, LinuxCNCSerializer
from ..fcutil import add_tool_to_job, get_jobs, get_active_job
from .util import load_ui
from .preferences import PreferencesDialog
from .about import AboutDialog
from .tablecell import TwoLineTableCell
from .shapeselector import ShapeSelector
from .tooleditor import ToolEditor
from .libraryproperties import LibraryProperties
from .jobselector import JobSelector
from .movetool import MoveToolDialog

__dir__ = os.path.dirname(__file__)
ui_path = os.path.join(__dir__, "library.ui")

class LibraryUI():
    def __init__(self, db, serializer, standalone=False, parent=None):
        self.db = db
        self.serializer = serializer
        self.standalone = standalone
        self.form = load_ui(ui_path, parent)

        self.form.buttonBox.clicked.connect(self.form.close)
        self.form.listWidgetTools.itemDoubleClicked.connect(self.on_edit_tool_clicked)
        self.form.listWidgetTools.itemSelectionChanged.connect(self.update_search)
        self.form.listWidgetTools.setSelectionMode(
            QtGui.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.form.listWidgetTools.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.form.listWidgetTools.customContextMenuRequested.connect(self.on_right_click)

        self.form.lineEditSearch.setFocus()
        self.form.lineEditSearch.textChanged.connect(self.update_search)

        # Connect signals for buttons at the bottom.
        self.form.comboBoxLibrary.currentIndexChanged.connect(self.library_selected)
        self.form.pushButtonAddToJob.clicked.connect(self.on_add_to_job_clicked)

        # Automatically connect shortcuts to their respective menu item signals.
        for menu in self.form.menubar.children():
            for action in menu.actions():
                key_sequence = action.shortcut()
                if not key_sequence.isEmpty():
                    context = action.shortcutContext()
                    shortcut = QShortcut(key_sequence, menu)
                    shortcut.setContext(context)
                    shortcut.activated.connect(action.trigger)

        # Connect signals for File menu items.
        self.form.actionAddLibrary.triggered.connect(self.on_create_library_clicked)
        self.form.actionEditLibrary.triggered.connect(self.on_edit_library_clicked)
        self.form.actionDeleteLibrary.triggered.connect(self.on_delete_library_clicked)
        self.form.actionExportLibrary.triggered.connect(self.on_export_library_clicked)
        self.form.actionCreateTool.triggered.connect(self.on_create_tool_clicked)
        self.form.actionImportShape.triggered.connect(self.on_import_shape_clicked)

        # Connect signals for Edit menu items.
        self.form.actionCopy.triggered.connect(self._copy_tool)
        self.form.actionPaste.triggered.connect(self._paste_tool)
        self.form.actionDelete.triggered.connect(self.on_delete_tool_clicked)
        self.form.actionDuplicate.triggered.connect(self._duplicate_tool)
        self.form.actionPreferences.triggered.connect(self.on_preferences_clicked)

        # Connect signals for About menu items.
        self.form.actionAbout.triggered.connect(self.on_action_about_clicked)

        if standalone:
            self.form.pushButtonAddToJob.hide()

        self.load()

        item = self.form.listWidgetTools.item(0)
        if item:
            self.form.listWidgetTools.setCurrentItem(item)

    def _copy_tool(self):
        library = self.get_selected_library()
        items = self.form.listWidgetTools.selectedItems()
        if not items:
            return

        tool_ids = []
        tool_str = []
        for item in self.form.listWidgetTools.selectedItems():
            tool = item.data(QtCore.Qt.UserRole)
            tool_ids.append(tool.id)
            tool_str.append(tool.to_string())

        clipboard = QApplication.instance().clipboard()
        tool_data = bytes(json.dumps(tool_ids).encode('utf-8'))
        mime_data = QMimeData()
        mime_data.setText('\n'.join(tool_str))
        mime_data.setData('application/btl-tool-ids', tool_data)
        clipboard.setMimeData(mime_data)

    def _duplicate_tool(self):
        library = self.get_selected_library()
        items = self.form.listWidgetTools.selectedItems()
        if not items:
            return

        for item in self.form.listWidgetTools.selectedItems():
            tool = item.data(QtCore.Qt.UserRole)
            self.db.add_tool(tool.copy(), library)

        self.db.serialize(self.serializer)
        self.load()

    def _paste_tool(self):
        library = self.get_selected_library()
        if not library:
            return

        clipboard = QApplication.instance().clipboard()
        mime_data = clipboard.mimeData()
        if not mime_data.hasFormat("application/btl-tool-ids"):
            return

        json_data = mime_data.data("application/btl-tool-ids")
        tool_ids = json.loads(bytes(json_data))
        for tool_id in tool_ids:
            tool = self.db.get_tool_by_id(tool_id)
            if tool and not library.has_tool(tool):
                self.db.add_tool(tool, library)

        self.db.serialize(self.serializer)
        self.load()

    def on_right_click(self, pos):
        menu = QtGui.QMenu(self.form.listWidgetTools)
        label = translate("btl", "Move to library...")
        action = QtGui.QAction(label, self.form.listWidgetTools)
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

        dialog = MoveToolDialog(self.db, tools, parent=self.form)
        if dialog.exec() != QtGui.QDialog.Accepted:
            return
        if not dialog.library:
            return

        library = self.get_selected_library()
        for tool in tools:
            self.db.add_tool(tool, dialog.library)
            library.remove_tool(tool)

        self.db.serialize(self.serializer)
        self.load()

    def update_button_state(self):
        # Avoid calling get_jobs() or get_active_job() in standalone mode,
        # it doesn't support that.
        has_job = self.standalone or bool(get_jobs())
        library = self.get_selected_library()
        tool_selected = bool(self.form.listWidgetTools.selectedItems())
        self.form.actionDeleteLibrary.setEnabled(library is not None)
        self.form.actionEditLibrary.setEnabled(library is not None)
        self.form.actionExportLibrary.setEnabled(library is not None)
        self.form.actionCopy.setEnabled(tool_selected)
        self.form.actionDelete.setEnabled(tool_selected)
        self.form.actionDuplicate.setEnabled(tool_selected)
        self.form.pushButtonAddToJob.setEnabled(tool_selected and has_job)
        text = translate('btl', 'No job found in main window')
        tt = '' if has_job else text
        self.form.pushButtonAddToJob.setToolTip(tt)

    def load(self):
        self.db.deserialize(self.serializer)

        # Update the library dropdown menu.
        combo = self.form.comboBoxLibrary
        index = combo.currentIndex()
        combo.clear()
        combo.addItem(translate('btl', 'Unused tools'))
        combo.insertSeparator(1)
        libraries = sorted(self.db.get_libraries(), key=lambda l: l.label)
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
        return self.db.get_library_by_id(library_id)

    def update_tool_list(self):
        # Find the selected library.
        library = self.get_selected_library()
        if library:
            tools = library.get_tools()
        else:
            tools = self.db.get_unused_tools()

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
        library = Library(translate('btl', 'New Library'))
        dialog = LibraryProperties(library, new=True)
        if dialog.exec() != QtGui.QDialog.Accepted:
            return

        self.db.add_library(library)
        self.db.serialize(self.serializer)
        self.load()

    def on_edit_library_clicked(self):
        library = self.get_selected_library()
        if not library:
            return

        dialog = LibraryProperties(library)
        if dialog.exec() != QtGui.QDialog.Accepted:
            return

        self.db.serialize(self.serializer)
        self.load()

    def on_delete_library_clicked(self):
        library = self.get_selected_library()
        if not library:
            return

        libname = f'<b>{library.label}</b>'
        msg = translate('btl',
              'Are you sure you want to delete library {library}?' \
            + ' This action cannot be reversed.').format(library=libname)
        msgBox = QtGui.QMessageBox()
        msgBox.setWindowTitle(translate('btl', 'Confirm library deletion'))
        msgBox.setText(msg)
        msgBox.addButton(QtGui.QMessageBox.Cancel)
        msgBox.addButton(translate('btl', 'Delete'),
                         QtGui.QMessageBox.AcceptRole)
        response = msgBox.exec()
        if response != QtGui.QMessageBox.AcceptRole:
            return

        self.db.remove_library(library)
        self.form.comboBoxLibrary.setCurrentIndex(0)
        self.db.serialize(self.serializer)
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

        filename, format = QtGui.QFileDialog.getSaveFileName(
            self.form,
            translate('btl', "Export the tool library {}").format(library.label),
            dir=str(Path.home()),
            filter=';;'.join(sorted(filters)),
            selectedFilter=selection)
        if not filename:
            return

        dirname = os.path.dirname(filename)
        serializer = filters[format](dirname)

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
        selector = ShapeSelector(self.db, self.serializer)
        selector.show()
        shape = selector.shape
        if not shape:
            return

        label = shape.get_label()
        tool = Tool(translate('btl', 'New {}').format(label), shape)
        library = self.get_selected_library()
        pocket = library.get_next_pocket()
        editor = ToolEditor(self.db, self.serializer, tool, pocket, parent=self.form)
        if not editor.show():
            return

        self.db.add_tool(tool, library)
        if library:
            library.assign_new_pocket(tool, editor.pocket)
        self.db.serialize(self.serializer)
        self.load()
        self.select_tool(tool)

    def on_import_shape_clicked(self):
        label = translate('btl', 'Choose a Shape File')
        filter_label = translate('btl', 'FreeCAD files .fcstd (*.fcstd)')
        filename = QtGui.QFileDialog.getOpenFileName(
             self.form,
             label,
             dir=str(Path.home()),
             filter=filter_label
        )[0]
        if not filename:
            self.form.close()
            return

        try:
            self.serializer.import_shape_from_file(filename)
        except OSError as e:
            print("error opening file: {}".format(e))
        else:
            self.load()

    def on_edit_tool_clicked(self):
        items = self.form.listWidgetTools.selectedItems()
        if not items:
            return

        tool = items[0].data(QtCore.Qt.UserRole)
        library = self.get_selected_library()
        if library:
            pocket = library.get_pocket_from_tool(tool)
            editor = ToolEditor(self.db, self.serializer, tool, pocket)
        else:
            editor = ToolEditor(self.db, self.serializer, tool)

        if not editor.show():
            # Reload the original values.
            self.load()
            self.select_tool(tool)
            return

        self.db.add_tool(tool)
        if library:
            library.assign_new_pocket(tool, editor.pocket)

        self.db.serialize(self.serializer)
        self.load()
        self.select_tool(tool)

    def on_delete_tool_clicked(self):
        library = self.get_selected_library()
        items = self.form.listWidgetTools.selectedItems()
        if not items:
            return
        elif len(items) == 1 and library:
            tool = items[0].data(QtCore.Qt.UserRole)
            tool_lbl = f'<b>{tool.get_label()}</b>'
            lib_lbl = f'<b>{library.label}</b>'
            msg = translate('btl', 'Delete tool {tool} from library {library}?')
            msg = msg.format(tool=tool_lbl, library=lib_lbl)
        elif len(items) == 1:
            tool = items[0].data(QtCore.Qt.UserRole)
            tool_lbl = f'<b>{tool.get_label()}</b>'
            msg = translate('btl', 'Delete unused tool {tool}?')
            msg = msg.format(tool=tool_lbl)
        elif len(items) > 1 and library:
            tool = items[0].data(QtCore.Qt.UserRole)
            lib_lbl = f'<b>{library.label}</b>'
            msg = translate('btl', 'Delete {n} selected tools from library {library}?')
            msg = msg.format(n=len(items), library=lib_lbl)
        else:
            msg = translate('btl', 'Delete {} unused tools from the library?')
            msg = msg.format(len(items))

        msgBox = QtGui.QMessageBox()
        title = translate('btl', 'Confirm tool deletion')
        msgBox.setWindowTitle(title)
        msgBox.setText(msg)
        msgBox.addButton(QtGui.QMessageBox.Cancel)
        label = translate('btl', 'Delete')
        msgBox.addButton(label, QtGui.QMessageBox.AcceptRole)
        response = msgBox.exec()
        if response != QtGui.QMessageBox.AcceptRole:
            return

        for item in self.form.listWidgetTools.selectedItems():
            tool = item.data(QtCore.Qt.UserRole)
            self.db.remove_tool(tool, library)

        self.db.serialize(self.serializer)
        self.load()

    def on_add_to_job_clicked(self):
        library = self.get_selected_library()
        items = self.form.listWidgetTools.selectedItems()
        if not items:
            return

        jobs = [get_active_job()]
        if not jobs[0]:
            jobs = JobSelector(self.form).exec()
        if not jobs:
            return

        for job in jobs:
            for item in items:
                tool = item.data(QtCore.Qt.UserRole)
                pocket = library.get_pocket_from_tool(tool)
                assert pocket is not None
                add_tool_to_job(job, tool, pocket)

    def on_preferences_clicked(self):
        dialog = PreferencesDialog(self.serializer, parent=self.form)
        if not dialog.exec():
            return
        self.load()

    def on_action_about_clicked(self):
        dialog = AboutDialog()
        dialog.exec()
