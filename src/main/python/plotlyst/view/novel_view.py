"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

This file is part of Plotlyst.

Plotlyst is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Plotlyst is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from PyQt5.QtCore import QItemSelection, QModelIndex, QAbstractItemModel, Qt, QItemSelectionModel
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QStyledItemDelegate, QLineEdit, QColorDialog, QHeaderView
from overrides import overrides

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel, StoryLine
from src.main.python.plotlyst.model.novel import EditableNovelStoryLinesListModel
from src.main.python.plotlyst.settings import STORY_LINE_COLOR_CODES
from src.main.python.plotlyst.view.common import ask_confirmation
from src.main.python.plotlyst.view.generated.novel_view_ui import Ui_NovelView
from src.main.python.plotlyst.view.icons import IconRegistry


class NovelView:

    def __init__(self, novel: Novel):
        self.novel = novel
        self.widget = QWidget()
        self.ui = Ui_NovelView()
        self.ui.setupUi(self.widget)

        self.ui.lineTitle.setText(self.novel.title)
        self.ui.btnAdd.setIcon(IconRegistry.plus_icon())
        self.ui.btnAdd.clicked.connect(self._on_add_story_line)

        self.ui.btnEdit.clicked.connect(self._on_edit_story_line)
        self.ui.btnEdit.setIcon(IconRegistry.edit_icon())
        self.ui.btnEdit.setDisabled(True)

        self.ui.btnRemove.clicked.connect(self._on_remove_story_line)
        self.ui.btnRemove.setDisabled(True)
        self.ui.btnRemove.setIcon(IconRegistry.minus_icon())

        self.story_lines_model = EditableNovelStoryLinesListModel(self.novel)
        self.ui.tblStoryLines.horizontalHeader().setDefaultSectionSize(25)
        self.ui.tblStoryLines.setModel(self.story_lines_model)
        self.ui.tblStoryLines.horizontalHeader().setSectionResizeMode(EditableNovelStoryLinesListModel.ColText,
                                                                      QHeaderView.ResizeToContents)
        self.ui.tblStoryLines.setItemDelegate(StoryLineDelegate())
        self.ui.tblStoryLines.selectionModel().selectionChanged.connect(self._on_story_line_selected)
        self.ui.tblStoryLines.clicked.connect(self._on_story_line_clicked)

    def _on_add_story_line(self):
        story_line = StoryLine(text='Unknown')
        self.novel.story_lines.append(story_line)
        story_line.color_hexa = STORY_LINE_COLOR_CODES[(len(self.novel.story_lines) - 1) % len(STORY_LINE_COLOR_CODES)]
        client.insert_story_line(self.novel, story_line)
        self.story_lines_model.modelReset.emit()

        self.ui.tblStoryLines.selectionModel().select(
            self.story_lines_model.index(self.story_lines_model.rowCount() - 1, 0),
            QItemSelectionModel.Select)

        self.ui.tblStoryLines.edit(self.ui.tblStoryLines.selectionModel().selectedIndexes()[0])

    def _on_edit_story_line(self):
        indexes = self.ui.tblStoryLines.selectedIndexes()
        if not indexes:
            return
        self.ui.tblStoryLines.edit(indexes[0])

    def _on_remove_story_line(self):
        indexes = self.ui.tblStoryLines.selectedIndexes()
        if not indexes:
            return
        story_line: StoryLine = indexes[0].data(EditableNovelStoryLinesListModel.StoryLineRole)
        if not ask_confirmation(f'Are you sure you want to remove story line "{story_line.text}"?'):
            return

        self.novel.story_lines.remove(story_line)
        client.delete_story_line(story_line)
        self.novel = client.fetch_novel(self.novel.id)
        self.story_lines_model.modelReset.emit()

    def _on_story_line_selected(self, selection: QItemSelection):
        if selection.indexes():
            self.ui.btnEdit.setEnabled(True)
            self.ui.btnRemove.setEnabled(True)

    def _on_story_line_clicked(self, index: QModelIndex):
        if index.column() == EditableNovelStoryLinesListModel.ColColor:
            storyline: StoryLine = index.data(EditableNovelStoryLinesListModel.StoryLineRole)
            color: QColor = QColorDialog.getColor(QColor(storyline.color_hexa),
                                                  options=QColorDialog.DontUseNativeDialog)
            if color.isValid():
                storyline.color_hexa = color.name()
                client.update_story_line(storyline)


class StoryLineDelegate(QStyledItemDelegate):

    @overrides
    def setEditorData(self, editor: QWidget, index: QModelIndex):
        if isinstance(editor, QLineEdit):
            editor.deselect()
            editor.setText(index.data())

    @overrides
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
        updated = model.setData(index, editor.text(), role=Qt.EditRole)
        if updated:
            client.update_story_line(index.data(EditableNovelStoryLinesListModel.StoryLineRole))
