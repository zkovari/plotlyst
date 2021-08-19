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
from functools import partial
from typing import Optional, List, Set

import emoji
from PyQt5.QtCore import QObject, pyqtSignal, QSortFilterProxyModel, QModelIndex, QTimer, QItemSelectionModel, \
    QAbstractItemModel, Qt, QSize, QEvent
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QStyledItemDelegate, QStyleOptionViewItem, QTextEdit, QLineEdit, QComboBox, \
    QWidgetAction, QListView
from fbs_runtime import platform
from overrides import overrides

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel, Scene, ACTION_SCENE, REACTION_SCENE, CharacterArc, \
    VERY_UNHAPPY, \
    UNHAPPY, NEUTRAL, HAPPY, VERY_HAPPY, SceneBuilderElement
from src.main.python.plotlyst.model.characters_model import CharactersSceneAssociationTableModel
from src.main.python.plotlyst.model.novel import NovelDramaticQuestionsListModel
from src.main.python.plotlyst.model.scene_builder_model import SceneBuilderInventoryTreeModel, \
    SceneBuilderPaletteTreeModel, CharacterEntryNode, SceneInventoryNode, convert_to_element_type
from src.main.python.plotlyst.model.scenes_model import ScenesTableModel
from src.main.python.plotlyst.view.common import emoji_font
from src.main.python.plotlyst.view.dialog.scene_builder_edition import SceneBuilderPreviewDialog
from src.main.python.plotlyst.view.generated.scene_editor_ui import Ui_SceneEditor
from src.main.python.plotlyst.view.icons import IconRegistry, avatars


class SceneEditor(QObject):
    commands_sent = pyqtSignal(QWidget, list)

    def __init__(self, novel: Novel, scene: Optional[Scene] = None):
        super().__init__()
        self.widget = QWidget()
        self.ui = Ui_SceneEditor()
        self.ui.setupUi(self.widget)
        self.novel = novel
        self.scene: Optional[Scene] = None
        if platform.is_windows():
            self._emoji_font = emoji_font(14)
        else:
            self._emoji_font = emoji_font(20)

        self.ui.btnVeryUnhappy.setFont(self._emoji_font)
        self.ui.btnVeryUnhappy.setText(emoji.emojize(':fearful_face:'))
        self.ui.btnUnHappy.setFont(self._emoji_font)
        self.ui.btnUnHappy.setText(emoji.emojize(':worried_face:'))
        self.ui.btnNeutral.setFont(self._emoji_font)
        self.ui.btnNeutral.setText(emoji.emojize(':neutral_face:'))
        self.ui.btnHappy.setFont(self._emoji_font)
        self.ui.btnHappy.setText(emoji.emojize(':slightly_smiling_face:'))
        self.ui.btnVeryHappy.setFont(self._emoji_font)
        self.ui.btnVeryHappy.setText(emoji.emojize(':smiling_face_with_smiling_eyes:'))

        self.ui.btnDisaster.setIcon(IconRegistry.disaster_icon(color='grey'))
        self.ui.btnResolution.setIcon(IconRegistry.success_icon(color='grey'))

        self.ui.lblDayEmoji.setFont(self._emoji_font)
        self.ui.lblDayEmoji.setText(emoji.emojize(':spiral_calendar:'))
        self.ui.lblTitleEmoji.setFont(self._emoji_font)
        self.ui.lblTitleEmoji.setText(emoji.emojize(':clapper_board:'))
        self.ui.lblSynopsisEmoji.setFont(self._emoji_font)
        self.ui.lblSynopsisEmoji.setText(emoji.emojize(':scroll:'))
        self.ui.lblBeatEmoji.setFont(self._emoji_font)
        self.ui.lblBeatEmoji.setText(emoji.emojize(':performing_arts:'))

        self.ui.cbPivotal.addItem('Select story beat...', None)
        self.ui.cbPivotal.addItem('', None)
        for beat in self.novel.story_structure.beats:
            self.ui.cbPivotal.addItem(beat.text, beat)
            if beat.ends_act:
                self.ui.cbPivotal.insertSeparator(self.ui.cbPivotal.count())
        self.ui.cbPivotal.view().setRowHidden(0, True)

        self.ui.cbPov.addItem('Select POV...', None)
        self.ui.cbPov.addItem('', None)
        for char in self.novel.characters:
            self.ui.cbPov.addItem(QIcon(avatars.pixmap(char)), char.name, char)
        self.ui.cbPov.view().setRowHidden(0, True)

        self.ui.cbType.setItemIcon(1, IconRegistry.action_scene_icon())
        self.ui.cbType.setItemIcon(2, IconRegistry.reaction_scene_icon())
        self.ui.cbType.currentTextChanged.connect(self._on_type_changed)
        self.ui.cbConflict.clicked.connect(self._on_conflict_toggled)

        self.dq_model = NovelDramaticQuestionsListModel(self.novel)
        self.lstDramaticQuestions = QListView()
        self.lstDramaticQuestions.setModel(self.dq_model)
        self.dq_model.selection_changed.connect(self._dramatic_question_selection_changed)
        self.dq_model.modelReset.connect(self._dramatic_question_selection_changed)
        self.ui.btnEditDramaticQuestions.setIcon(IconRegistry.edit_icon())
        action = QWidgetAction(self.ui.btnEditDramaticQuestions)
        action.setDefaultWidget(self.lstDramaticQuestions)
        self.ui.btnEditDramaticQuestions.addAction(action)

        self.scenes_model = ScenesTableModel(self.novel)
        self.ui.lstScenes.setModel(self.scenes_model)
        self.ui.lstScenes.setModelColumn(ScenesTableModel.ColTitle)
        self.ui.lstScenes.clicked.connect(self._new_scene_selected)

        self.ui.btnClose.setIcon(IconRegistry.return_icon())
        self.ui.btnClose.clicked.connect(self._on_close)
        self.ui.btnPrevious.setIcon(IconRegistry.arrow_left_thick_icon())
        self.ui.btnPrevious.clicked.connect(self._on_previous_scene)
        self.ui.btnNext.setIcon(IconRegistry.arrow_right_thick_icon())
        self.ui.btnNext.clicked.connect(self._on_next_scene)

        self._scene_builder_inventory_model = SceneBuilderInventoryTreeModel()
        self.ui.treeInventory.setModel(self._scene_builder_inventory_model)
        self.ui.treeInventory.doubleClicked.connect(self._on_dclick_scene_builder_inventory)
        self.ui.treeInventory.expandAll()

        self.ui.btnDelete.setIcon(IconRegistry.minus_icon())
        self.ui.btnDelete.clicked.connect(self._on_delete_scene_builder_element)
        self.ui.btnEdit.setIcon(IconRegistry.edit_icon())
        self.ui.btnEdit.clicked.connect(self._on_edit_scene_builder_element)
        self.ui.btnPreview.clicked.connect(self._on_preview_scene_builder)

        self._save_timer = QTimer()
        self._save_timer.setInterval(500)
        self._save_timer.timeout.connect(self._save_scene)

        self._save_enabled = False
        self._update_view(scene)

        self.ui.wdgPov.installEventFilter(self)

        self.ui.cbPov.currentIndexChanged.connect(self._on_pov_changed)
        self.ui.sbDay.valueChanged.connect(self._save_scene)
        self.ui.cbPivotal.currentIndexChanged.connect(self._save_scene)
        self.ui.cbType.currentIndexChanged.connect(self._save_scene)
        self.ui.textEvent1.textChanged.connect(self._pending_save)
        self.ui.textEvent2.textChanged.connect(self._pending_save)
        self.ui.textEvent3.textChanged.connect(self._pending_save)
        self.ui.lineTitle.textEdited.connect(self._pending_save)
        self.ui.textSynopsis.textChanged.connect(self._pending_save)
        self.ui.textNotes.textChanged.connect(self._pending_save)
        self.ui.btnGroupArc.buttonClicked.connect(self._save_scene)
        self.ui.btnDisaster.toggled.connect(self._on_disaster_toggled)
        self.ui.btnResolution.toggled.connect(self._on_resolution_toggled)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Enter:
            self._enabled_pov_arc_widgets(True)
        if event.type() == QEvent.Leave:
            self._enabled_pov_arc_widgets(False)

        return super(SceneEditor, self).eventFilter(watched, event)

    def _update_view(self, scene: Optional[Scene] = None):
        if scene:
            self.scene = scene
            self._new_scene = False
            index = self.scenes_model.index(self.scene.sequence, ScenesTableModel.ColTitle)
            self.ui.lstScenes.selectionModel().select(index, QItemSelectionModel.Select)
        else:
            self.scene = Scene('')
            if len(self.novel.scenes) > 1:
                self.scene.day = self.novel.scenes[-1].day
            self._new_scene = True

        if self.scene.pov:
            self.ui.cbPov.setCurrentText(self.scene.pov.name)
        else:
            self.ui.cbPov.setCurrentIndex(0)
        self._enabled_pov_arc_widgets(False)
        self._update_pov_avatar()
        self.ui.sbDay.setValue(self.scene.day)

        if self.scene.type:
            self.ui.cbType.setCurrentText(self.scene.type)
        elif not self._new_scene:
            self.ui.cbType.setCurrentIndex(0)
        else:
            self.ui.cbType.setCurrentIndex(1)
        self._on_type_changed(self.ui.cbType.currentText())

        self.ui.textEvent1.setText(self.scene.beginning)
        self.ui.textEvent2.setText(self.scene.middle)
        self.ui.textEvent3.setText(self.scene.end)

        self.ui.lineTitle.setText(self.scene.title)
        self.ui.textSynopsis.setText(self.scene.synopsis)

        occupied_beats: Set[str] = set([x.beat.text for x in self.novel.scenes if x.beat])
        for i in range(self.ui.cbPivotal.count()):
            if i < 2:
                continue
            beat = self.ui.cbPivotal.itemData(i)
            item = self.ui.cbPivotal.model().item(i)
            if beat and beat.text in occupied_beats:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            else:
                item.setFlags(item.flags() | Qt.ItemIsEnabled)

        if self.scene.beat:
            self.ui.cbPivotal.setCurrentText(self.scene.beat.text)
        else:
            self.ui.cbPivotal.setCurrentIndex(0)
        self.ui.textNotes.setPlainText(self.scene.notes)

        self._characters_model = CharactersSceneAssociationTableModel(self.novel, self.scene)
        self._characters_model.selection_changed.connect(self._save_scene)
        self._characters_proxy_model = QSortFilterProxyModel()
        self._characters_proxy_model.setSourceModel(self._characters_model)
        self.ui.tblCharacters.setModel(self._characters_proxy_model)

        self.dq_model.selected.clear()
        for dq in self.scene.dramatic_questions:
            self.dq_model.selected.add(dq)
        self.dq_model.modelReset.emit()

        if self._new_scene:
            self.ui.btnPrevious.setDisabled(True)
            self.ui.btnPrevious.setHidden(True)
            self.ui.btnNext.setDisabled(True)
            self.ui.btnNext.setHidden(True)
        else:
            if self.scene.sequence == 0:
                self.ui.btnPrevious.setDisabled(True)
            else:
                self.ui.btnPrevious.setEnabled(True)
            if self.scene.sequence == len(self.novel.scenes) - 1:
                self.ui.btnNext.setDisabled(True)
            else:
                self.ui.btnNext.setEnabled(True)

        for char_arc in self.scene.arcs:
            if scene.pov and char_arc.character == scene.pov:
                if char_arc.arc == VERY_UNHAPPY:
                    self.ui.btnVeryUnhappy.setChecked(True)
                elif char_arc.arc == UNHAPPY:
                    self.ui.btnUnHappy.setChecked(True)
                elif char_arc.arc == NEUTRAL:
                    self.ui.btnNeutral.setChecked(True)
                elif char_arc.arc == HAPPY:
                    self.ui.btnHappy.setChecked(True)
                elif char_arc.arc == VERY_HAPPY:
                    self.ui.btnVeryHappy.setChecked(True)

        self._scene_builder_palette_model = SceneBuilderPaletteTreeModel(self.scene)
        self.ui.treeSceneBuilder.setModel(self._scene_builder_palette_model)
        self.ui.treeSceneBuilder.selectionModel().selectionChanged.connect(self._on_scene_builder_selection_changed)
        self._scene_builder_palette_model.modelReset.connect(self.ui.treeSceneBuilder.expandAll)
        self.ui.treeSceneBuilder.setColumnWidth(0, 400)
        self.ui.treeSceneBuilder.setColumnWidth(1, 40)
        self.ui.treeSceneBuilder.setColumnWidth(2, 40)
        self.ui.treeSceneBuilder.expandAll()
        self.ui.treeSceneBuilder.setItemDelegate(ScenesBuilderDelegate(self, self.scene))
        self._scene_builder_palette_model.setElements(self.scene.builder_elements)

        self._save_enabled = True

    def _on_type_changed(self, text: str):
        if text == ACTION_SCENE:
            self.ui.lblType1.setText('Goal:')
            self.ui.textEvent1.setPlaceholderText('Scene goal')
            self.ui.lblType2.setText('Conflict:')
            if not self.scene.without_action_conflict:
                self.ui.textEvent2.setPlaceholderText('Conflict throughout the scene')
            if self.scene.action_resolution:
                self.ui.btnResolution.setChecked(True)
            else:
                self.ui.btnDisaster.setChecked(True)
            if self.ui.btnDisaster.isChecked():
                self.ui.lblType3.setText('Disaster:')
                self.ui.textEvent3.setPlaceholderText('Disaster in the end')
            elif self.ui.btnResolution.isChecked():
                self.ui.lblType3.setText('Resolution:')
                self.ui.textEvent3.setPlaceholderText('Resolution in the end')
            self.ui.btnDisaster.setVisible(True)
            self.ui.btnResolution.setVisible(True)
            self.ui.cbConflict.setVisible(True)
            self.ui.cbConflict.setChecked(not self.scene.without_action_conflict)
            self._on_conflict_toggled(self.ui.cbConflict.isChecked())

            return
        elif text == REACTION_SCENE:
            self.ui.btnDisaster.setHidden(True)
            self.ui.btnResolution.setHidden(True)
            self.ui.lblType1.setText('Reaction:')
            self.ui.textEvent1.setPlaceholderText('Reaction in the beginning')
            self.ui.lblType2.setText('Dilemma:')
            self.ui.textEvent2.setPlaceholderText('Dilemma throughout the scene')
            self.ui.lblType3.setText('Decision:')
            self.ui.textEvent3.setPlaceholderText('Decision in the end')
        else:
            self.ui.lblType1.setText('Beginning:')
            self.ui.textEvent1.setPlaceholderText('Beginning event of the scene')
            self.ui.lblType2.setText('Middle:')
            self.ui.textEvent2.setPlaceholderText('Middle part of the scene')
            self.ui.lblType3.setText('End:')
            self.ui.textEvent3.setPlaceholderText('Ending of the scene')

        self.ui.textEvent2.setEnabled(True)
        self.ui.lblType2.setVisible(True)
        self.ui.btnDisaster.setHidden(True)
        self.ui.btnResolution.setHidden(True)
        self.ui.cbConflict.setHidden(True)

    def _on_disaster_toggled(self):
        self.ui.lblType3.setText('Disaster:')
        self.ui.textEvent3.setPlaceholderText('Disaster in the end')

    def _on_resolution_toggled(self):
        self.ui.lblType3.setText('Resolution:')
        self.ui.textEvent3.setPlaceholderText('Resolution in the end')

    def _on_conflict_toggled(self, toggled: bool):
        if toggled:
            self.ui.textEvent2.setPlaceholderText('Conflict throughout the scene')
        else:
            self.ui.textEvent2.setText('')
            self.ui.textEvent2.setPlaceholderText('There is no conflict in this scene')
        self.ui.textEvent2.setEnabled(toggled)

    def _pending_save(self):
        if self._save_enabled:
            self._save_timer.start(500)

    def _enabled_pov_arc_widgets(self, edition: bool):
        if self.scene.pov:
            self.ui.btnVeryUnhappy.setVisible(edition)
            self.ui.btnUnHappy.setVisible(edition)
            self.ui.btnNeutral.setVisible(edition)
            self.ui.btnHappy.setVisible(edition)
            self.ui.btnVeryHappy.setVisible(edition)

            if not edition:
                self.ui.cbPov.setStyleSheet('border: 0px;')
                for btn in self.ui.btnGroupArc.buttons():
                    if btn.isChecked():
                        btn.setVisible(True)
        else:
            self.ui.btnVeryUnhappy.setVisible(False)
            self.ui.btnUnHappy.setVisible(False)
            self.ui.btnNeutral.setVisible(False)
            self.ui.btnHappy.setVisible(False)
            self.ui.btnVeryHappy.setVisible(False)

    def _on_pov_changed(self):
        pov = self.ui.cbPov.currentData()
        if pov:
            self.scene.pov = pov
            self._enabled_pov_arc_widgets(True)
        else:
            self.scene.pov = None
            self._enabled_pov_arc_widgets(False)
        self._update_pov_avatar()
        self._characters_model.update()
        self.ui.cbPov.setStyleSheet('''
                        QComboBox {border: 0px black solid;}
                        ''')
        self._save_scene()

    def _update_pov_avatar(self):
        if self.scene.pov:
            if self.scene.pov.avatar:
                pixmap = avatars.pixmap(self.scene.pov)
                self.ui.lblAvatar.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                pixmap = avatars.name_initial_icon(self.scene.pov).pixmap(128, 128)
                self.ui.lblAvatar.setPixmap(pixmap)
        else:
            self.ui.lblAvatar.setPixmap(IconRegistry.portrait_icon().pixmap(QSize(128, 128)))

    def _dramatic_question_selection_changed(self):
        self.ui.wdgDramaticQuestions.clear()
        for dq in self.dq_model.selected:
            self.ui.wdgDramaticQuestions.addText(dq.text, dq.color_hexa)
        self._save_scene()

    def _save_scene(self):
        self._save_timer.stop()
        if not self._save_enabled:
            return

        self.scene.title = self.ui.lineTitle.text()
        self.scene.synopsis = self.ui.textSynopsis.toPlainText()
        self.scene.type = self.ui.cbType.currentText()
        self.scene.beginning = self.ui.textEvent1.toPlainText()
        if self.scene.type == ACTION_SCENE:
            self.scene.without_action_conflict = not self.ui.cbConflict.isChecked()
            self.scene.action_resolution = self.ui.btnResolution.isChecked()
        self.scene.middle = self.ui.textEvent2.toPlainText()
        self.scene.end = self.ui.textEvent3.toPlainText()
        self.scene.day = self.ui.sbDay.value()
        self.scene.notes = self.ui.textNotes.toPlainText()

        if self.ui.cbPivotal.currentIndex() > 0:
            self.scene.beat = self.ui.cbPivotal.currentData()
        self.scene.dramatic_questions.clear()
        for story_line in self.dq_model.selected:
            self.scene.dramatic_questions.append(story_line)

        arc = NEUTRAL
        if self.ui.btnVeryUnhappy.isChecked():
            arc = VERY_UNHAPPY
        elif self.ui.btnUnHappy.isChecked():
            arc = UNHAPPY
        elif self.ui.btnHappy.isChecked():
            arc = HAPPY
        elif self.ui.btnVeryHappy.isChecked():
            arc = VERY_HAPPY

        self.scene.arcs.clear()
        if self.scene.pov:
            self.scene.arcs.append(CharacterArc(arc, self.scene.pov))

        if self._new_scene:
            self.novel.scenes.append(self.scene)
            self.scene.sequence = self.novel.scenes.index(self.scene)
            client.insert_scene(self.novel, self.scene)
        else:
            client.update_scene(self.scene)
        self._new_scene = False

    def _on_close(self):
        self.scene.builder_elements.clear()
        self.scene.builder_elements.extend(self._scene_builder_elements())
        self._save_scene()

    def __get_scene_builder_element(self, scene: Scene, node: SceneInventoryNode, seq: int) -> SceneBuilderElement:
        children = []
        for child_seq, child in enumerate(node.children):
            children.append(self.__get_scene_builder_element(self.scene, child, child_seq))

        return SceneBuilderElement(type=convert_to_element_type(node), text=node.name,
                                   children=children,
                                   character=node.character, has_suspense=node.suspense, has_tension=node.tension,
                                   has_stakes=node.stakes)

    def _on_previous_scene(self):
        row = self.scene.sequence - 1
        self.ui.lstScenes.selectionModel().select(self.scenes_model.index(row, ScenesTableModel.ColTitle),
                                                  QItemSelectionModel.ClearAndSelect)
        self._new_scene_selected(self.scenes_model.index(row, 0))

    def _on_next_scene(self):
        row = self.scene.sequence + 1
        self.ui.lstScenes.selectionModel().select(self.scenes_model.index(row, ScenesTableModel.ColTitle),
                                                  QItemSelectionModel.ClearAndSelect)
        self._new_scene_selected(self.scenes_model.index(row, 0))

    def _new_scene_selected(self, index: QModelIndex):
        self.scene.builder_elements.clear()
        self.scene.builder_elements.extend(self._scene_builder_elements())
        self._save_scene()

        scene = self.scenes_model.data(index, role=ScenesTableModel.SceneRole)
        self._save_enabled = False
        self._update_view(scene)

    def _scene_builder_elements(self) -> List[SceneBuilderElement]:
        elements: List[SceneBuilderElement] = []
        for seq, node in enumerate(self._scene_builder_palette_model.root.children):
            elements.append(self.__get_scene_builder_element(self.scene, node, seq))

        return elements

    def _on_dclick_scene_builder_inventory(self, index: QModelIndex):
        node = index.data(SceneBuilderInventoryTreeModel.NodeRole)
        if isinstance(node, SceneInventoryNode):
            self._scene_builder_palette_model.insertNode(node)

    def _on_scene_builder_selection_changed(self):
        indexes = self.ui.treeSceneBuilder.selectedIndexes()
        self.ui.btnDelete.setEnabled(bool(indexes))
        self.ui.btnEdit.setEnabled(bool(indexes))

    def _on_delete_scene_builder_element(self):
        indexes = self.ui.treeSceneBuilder.selectedIndexes()
        if not indexes:
            return
        self._scene_builder_palette_model.deleteItem(indexes[0])
        self.ui.btnDelete.setDisabled(True)

    def _on_preview_scene_builder(self):
        SceneBuilderPreviewDialog().display(self._scene_builder_elements())

    def _on_edit_scene_builder_element(self):
        indexes = self.ui.treeSceneBuilder.selectedIndexes()
        if not indexes:
            return
        self.ui.treeSceneBuilder.edit(indexes[0])


class ScenesBuilderDelegate(QStyledItemDelegate):

    def __init__(self, view: SceneEditor, scene: Scene, parent=None):
        super(ScenesBuilderDelegate, self).__init__(parent)
        self.scene = scene
        self.view = view
        self._close_shortcut = self.view.ui.btnClose.shortcut()

    @overrides
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        node = index.internalPointer()
        if isinstance(node, CharacterEntryNode):
            return QComboBox(parent)
        lineedit = QLineEdit(parent)
        lineedit.textEdited.connect(partial(self._on_text_edit, lineedit))
        self.view.ui.btnClose.setShortcut('')
        lineedit.destroyed.connect(lambda: self.view.ui.btnClose.setShortcut(self._close_shortcut))
        return lineedit

    @overrides
    def setEditorData(self, editor: QWidget, index: QModelIndex):
        if isinstance(editor, QTextEdit) or isinstance(editor, QLineEdit):
            node = index.internalPointer()
            editor.setText(node.name)
        elif isinstance(editor, QComboBox):
            for char in self.scene.characters:
                editor.addItem(QIcon(avatars.pixmap(char)), char.name, char)
            editor.activated.connect(lambda: self._commit_and_close(editor))
            editor.showPopup()

    @overrides
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentData(Qt.UserRole))
        elif isinstance(editor, QLineEdit):
            model.setData(index, editor.text())

    def _on_text_edit(self, editor: QLineEdit, text: str):
        if len(text) == 1:
            editor.setText(text.upper())

    def _commit_and_close(self, editor):
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)
