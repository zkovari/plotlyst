from PyQt5.QtCore import QItemSelection, QModelIndex, QAbstractItemModel, Qt
from PyQt5.QtWidgets import QWidget, QStyledItemDelegate, QLineEdit
from overrides import overrides

from novel_outliner.core.client import client
from novel_outliner.core.domain import Novel, StoryLine
from novel_outliner.model.novel import EditableNovelStoryLinesListModel
from novel_outliner.view.common import ask_confirmation
from novel_outliner.view.generated.novel_view_ui import Ui_NovelView
from novel_outliner.view.icons import IconRegistry


class NovelView:

    def __init__(self, novel: Novel):
        self.novel = novel
        self.widget = QWidget()
        self.ui = Ui_NovelView()
        self.ui.setupUi(self.widget)

        self.ui.lineTitle.setText(self.novel.title)
        self.ui.cbMultiplePov.setChecked(True)
        self.ui.btnAdd.setIcon(IconRegistry.plus_icon())
        self.ui.btnAdd.clicked.connect(self._on_add_story_line)

        self.ui.btnEdit.clicked.connect(self._on_edit_story_line)
        self.ui.btnEdit.setIcon(IconRegistry.edit_icon())
        self.ui.btnEdit.setDisabled(True)

        self.ui.btnRemove.clicked.connect(self._on_remove_story_line)
        self.ui.btnRemove.setDisabled(True)
        self.ui.btnRemove.setIcon(IconRegistry.minus_icon())

        self.story_lines_model = EditableNovelStoryLinesListModel(self.novel)
        self.ui.lstStoryLines.setModel(self.story_lines_model)
        self.ui.lstStoryLines.setItemDelegate(StoryLineDelegate())
        self.ui.lstStoryLines.selectionModel().selectionChanged.connect(self._on_story_line_selected)

    def _on_add_story_line(self):
        story_line = StoryLine(text='Unknown')
        self.novel.story_lines.append(story_line)
        client.insert_story_line(self.novel, story_line)
        self.story_lines_model.modelReset.emit()

    def _on_edit_story_line(self):
        indexes = self.ui.lstStoryLines.selectedIndexes()
        if not indexes:
            return
        self.ui.lstStoryLines.edit(indexes[0])

    def _on_remove_story_line(self):
        indexes = self.ui.lstStoryLines.selectedIndexes()
        if not indexes:
            return
        story_line: StoryLine = indexes[0].data(EditableNovelStoryLinesListModel.StoryLineRole)
        if not ask_confirmation(f'Are you sure you want to remove story line {story_line.text}'):
            return

        self.novel.story_lines.remove(story_line)
        client.delete_story_line(story_line)
        self.story_lines_model.modelReset.emit()

    def _on_story_line_selected(self, selection: QItemSelection):
        if selection.indexes():
            self.ui.btnEdit.setEnabled(True)
            self.ui.btnRemove.setEnabled(True)


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
