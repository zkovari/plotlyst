"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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
from typing import Iterable, List, Optional

import emoji
from PyQt5 import QtCore
from PyQt5.QtCore import QItemSelection, Qt, pyqtSignal, QSize, QObject, QEvent
from PyQt5.QtGui import QIcon, QPaintEvent, QPainter, QResizeEvent, QBrush, QColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QToolButton, QButtonGroup, QFrame, QMenu, QSizePolicy, QLabel
from fbs_runtime import platform
from overrides import overrides

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Character, Conflict, ConflictType, BackstoryEvent, \
    VERY_HAPPY, HAPPY, UNHAPPY, VERY_UNHAPPY, SceneStructureItem, Scene, NEUTRAL, Document
from src.main.python.plotlyst.event.core import emit_critical
from src.main.python.plotlyst.model.common import DistributionFilterProxyModel
from src.main.python.plotlyst.model.distribution import CharactersScenesDistributionTableModel, \
    ConflictScenesDistributionTableModel, TagScenesDistributionTableModel, GoalScenesDistributionTableModel
from src.main.python.plotlyst.view.common import spacer_widget, ask_confirmation, emoji_font, busy, transparent, \
    OpacityEventFilter, increase_font
from src.main.python.plotlyst.view.dialog.character import BackstoryEditorDialog
from src.main.python.plotlyst.view.generated.character_backstory_card_ui import Ui_CharacterBackstoryCard
from src.main.python.plotlyst.view.generated.character_conflict_widget_ui import Ui_CharacterConflictWidget
from src.main.python.plotlyst.view.generated.journal_widget_ui import Ui_JournalWidget
from src.main.python.plotlyst.view.generated.scene_dstribution_widget_ui import Ui_CharactersScenesDistributionWidget
from src.main.python.plotlyst.view.icons import avatars, IconRegistry, set_avatar
from src.main.python.plotlyst.view.layout import clear_layout, vbox, hbox
from src.main.python.plotlyst.view.widget.cards import JournalCard
from src.main.python.plotlyst.view.widget.input import RichTextEditor
from src.main.python.plotlyst.worker.persistence import RepositoryPersistenceManager


class CharactersScenesDistributionWidget(QWidget, Ui_CharactersScenesDistributionWidget):
    avg_text: str = 'Average characters per scenes: '
    common_text: str = 'Common scenes: '

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.average = 0

        self.btnCharacters.setIcon(IconRegistry.character_icon())
        self.btnGoals.setIcon(IconRegistry.goal_icon())
        self.btnConflicts.setIcon(IconRegistry.conflict_icon())
        self.btnTags.setIcon(IconRegistry.tags_icon())

        self._model = CharactersScenesDistributionTableModel(self.novel)
        self._scenes_proxy = DistributionFilterProxyModel()
        self._scenes_proxy.setSourceModel(self._model)
        self._scenes_proxy.setSortCaseSensitivity(Qt.CaseInsensitive)
        self._scenes_proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._scenes_proxy.setSortRole(CharactersScenesDistributionTableModel.SortRole)
        self._scenes_proxy.sort(CharactersScenesDistributionTableModel.IndexTags, Qt.DescendingOrder)
        self.tblSceneDistribution.horizontalHeader().setDefaultSectionSize(26)
        self.tblSceneDistribution.setModel(self._scenes_proxy)
        self.tblSceneDistribution.hideColumn(0)
        self.tblSceneDistribution.hideColumn(1)
        self.tblCharacters.setModel(self._scenes_proxy)
        self.tblCharacters.hideColumn(0)
        self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexTags, 70)
        self.tblCharacters.setMaximumWidth(70)

        self.tblCharacters.selectionModel().selectionChanged.connect(self._on_character_selected)
        self.tblSceneDistribution.selectionModel().selectionChanged.connect(self._on_scene_selected)

        self.btnCharacters.toggled.connect(self._toggle_characters)
        self.btnGoals.toggled.connect(self._toggle_goals)
        self.btnConflicts.toggled.connect(self._toggle_conflicts)
        self.btnTags.toggled.connect(self._toggle_tags)

        self.btnCharacters.setChecked(True)

        self.refresh()

    def refresh(self):
        if self.novel.scenes:
            self.average = sum([len(x.characters) + 1 for x in self.novel.scenes]) / len(self.novel.scenes)
        else:
            self.average = 0
        for col in range(self._model.columnCount()):
            if col == CharactersScenesDistributionTableModel.IndexTags:
                continue
            self.tblCharacters.hideColumn(col)
        self.spinAverage.setValue(self.average)
        self.tblSceneDistribution.horizontalHeader().setMaximumSectionSize(15)
        self._model.modelReset.emit()

    def setActsFilter(self, act: int, filter: bool):
        self._scenes_proxy.setActsFilter(act, filter)

    def _toggle_characters(self, toggled: bool):
        if toggled:
            self._model = CharactersScenesDistributionTableModel(self.novel)
            self._scenes_proxy.setSourceModel(self._model)
            self.tblCharacters.hideColumn(0)
            self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexTags, 70)
            self.tblCharacters.setMaximumWidth(70)

            self.spinAverage.setVisible(True)

    def _toggle_goals(self, toggled: bool):
        if toggled:
            self._model = GoalScenesDistributionTableModel(self.novel)
            self._scenes_proxy.setSourceModel(self._model)
            self.tblCharacters.showColumn(0)
            self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexMeta, 34)
            self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexTags, 170)
            self.tblCharacters.setMaximumWidth(204)

            self.spinAverage.setVisible(False)

    def _toggle_conflicts(self, toggled: bool):
        if toggled:
            self._model = ConflictScenesDistributionTableModel(self.novel)
            self._scenes_proxy.setSourceModel(self._model)
            self.tblCharacters.showColumn(0)
            self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexMeta, 34)
            self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexTags, 170)
            self.tblCharacters.setMaximumWidth(204)

            self.spinAverage.setVisible(False)

    def _toggle_tags(self, toggled: bool):
        if toggled:
            self._model = TagScenesDistributionTableModel(self.novel)
            self._scenes_proxy.setSourceModel(self._model)
            self.tblCharacters.hideColumn(0)
            self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexTags, 170)
            self.tblCharacters.setMaximumWidth(170)

            self.spinAverage.setVisible(False)

    def _on_character_selected(self):
        selected = self.tblCharacters.selectionModel().selectedIndexes()
        self._model.highlightTags(
            [self._scenes_proxy.mapToSource(x) for x in selected])

        if selected and len(selected) > 1:
            self.spinAverage.setPrefix(self.common_text)
            self.spinAverage.setValue(self._model.commonScenes())
        else:
            self.spinAverage.setPrefix(self.avg_text)
            self.spinAverage.setValue(self.average)

        self.tblSceneDistribution.clearSelection()

    def _on_scene_selected(self, selection: QItemSelection):
        indexes = selection.indexes()
        if not indexes:
            return
        self._model.highlightScene(self._scenes_proxy.mapToSource(indexes[0]))
        self.tblCharacters.clearSelection()


class CharacterToolButton(QToolButton):
    def __init__(self, character: Character, parent=None):
        super(CharacterToolButton, self).__init__(parent)
        self.character = character
        self.setIcon(QIcon(avatars.pixmap(self.character)))
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)


class CharacterSelectorWidget(QWidget):
    characterToggled = pyqtSignal(Character, bool)

    def __init__(self, parent=None):
        super(CharacterSelectorWidget, self).__init__(parent)
        self._layout = QHBoxLayout()
        self._layout.setSpacing(4)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._btn_group = QButtonGroup()
        self._buttons: List[QToolButton] = []
        self.setLayout(self._layout)
        self.exclusive: bool = True
        self.setExclusive(self.exclusive)

    def setExclusive(self, exclusive: bool):
        self.exclusive = exclusive
        self._btn_group.setExclusive(self.exclusive)

    def characters(self, all: bool = True) -> Iterable[Character]:
        return [x.character for x in self._buttons if all or x.isChecked()]

    def setCharacters(self, characters: Iterable[Character]):
        self.clear()

        self._layout.addWidget(spacer_widget())
        for char in characters:
            self.addCharacter(char, checked=False)
        self._layout.addWidget(spacer_widget())

        if not self._buttons:
            return
        if self.exclusive:
            self._buttons[0].setChecked(True)
        else:
            for btn in self._buttons:
                btn.setChecked(True)

    def clear(self):
        item = self._layout.itemAt(0)
        while item:
            self._layout.removeItem(item)
            item = self._layout.itemAt(0)
        for btn in self._buttons:
            self._btn_group.removeButton(btn)
            btn.deleteLater()
        self._buttons.clear()

    def addCharacter(self, character: Character, checked: bool = True):
        tool_btn = CharacterToolButton(character)
        tool_btn.toggled.connect(partial(self.characterToggled.emit, character))

        self._buttons.append(tool_btn)
        self._btn_group.addButton(tool_btn)
        self._layout.addWidget(tool_btn)

        tool_btn.setChecked(checked)


class CharacterConflictWidget(QFrame, Ui_CharacterConflictWidget):
    new_conflict_added = pyqtSignal(Conflict)
    conflict_selection_changed = pyqtSignal()

    def __init__(self, novel: Novel, scene: Scene, scene_structure_item: SceneStructureItem, parent=None):
        super(CharacterConflictWidget, self).__init__(parent)
        self.novel = novel
        self.scene = scene
        self.scene_structure_item = scene_structure_item
        self.setupUi(self)
        self.setMaximumWidth(270)

        self.repo = RepositoryPersistenceManager.instance()

        self.btnCharacter.setIcon(IconRegistry.conflict_character_icon())
        self.btnSociety.setIcon(IconRegistry.conflict_society_icon())
        self.btnNature.setIcon(IconRegistry.conflict_nature_icon())
        self.btnTechnology.setIcon(IconRegistry.conflict_technology_icon())
        self.btnSupernatural.setIcon(IconRegistry.conflict_supernatural_icon())
        self.btnSelf.setIcon(IconRegistry.conflict_self_icon())

        self._update_characters()

        self.btnAddNew.setIcon(IconRegistry.ok_icon())
        self.btnAddNew.setDisabled(True)

        self.lineKey.textChanged.connect(self._keyphrase_edited)

        self.btnGroupConflicts.buttonToggled.connect(self._type_toggled)
        self._type = ConflictType.CHARACTER
        self.btnCharacter.setChecked(True)

        self.btnAddNew.clicked.connect(self._add_new)

    def refresh(self):
        self.cbCharacter.clear()
        self._update_characters()
        self.tblConflicts.model().update()
        self.tblConflicts.model().modelReset.emit()

    def _update_characters(self):
        for char in self.novel.characters:
            if self.scene.pov and char.id != self.scene.pov.id:
                self.cbCharacter.addItem(QIcon(avatars.pixmap(char)), char.name, char)

    def _type_toggled(self):
        lbl_prefix = 'Character vs.'
        self.cbCharacter.setVisible(self.btnCharacter.isChecked())
        if self.btnCharacter.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} Character')
            self._type = ConflictType.CHARACTER
        elif self.btnSociety.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} Society')
            self._type = ConflictType.SOCIETY
        elif self.btnNature.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} Nature')
            self._type = ConflictType.NATURE
        elif self.btnTechnology.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} Technology')
            self._type = ConflictType.TECHNOLOGY
        elif self.btnSupernatural.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} Supernatural')
            self._type = ConflictType.SUPERNATURAL
        elif self.btnSelf.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} Self')
            self._type = ConflictType.SELF

    def _keyphrase_edited(self, text: str):
        self.btnAddNew.setEnabled(len(text) > 0)

    def _add_new(self):
        if not self.scene.pov:
            return emit_critical('Select POV character first')
        conflict = Conflict(self.lineKey.text(), self._type, character_id=self.scene.pov.id)
        if self._type == ConflictType.CHARACTER:
            conflict.conflicting_character_id = self.cbCharacter.currentData().id

        self.novel.conflicts.append(conflict)
        self.repo.update_novel(self.novel)
        self.new_conflict_added.emit(conflict)
        self.refresh()
        self.tblConflicts.model().checkItem(conflict)
        self.lineKey.clear()


class CharacterBackstoryCard(QFrame, Ui_CharacterBackstoryCard):
    deleteRequested = pyqtSignal(object)

    def __init__(self, backstory: BackstoryEvent, parent=None):
        super(CharacterBackstoryCard, self).__init__(parent)
        self.setupUi(self)
        self.backstory = backstory

        self.btnEdit.setVisible(False)
        self.btnEdit.setIcon(IconRegistry.edit_icon())
        self.btnEdit.clicked.connect(self._edit)
        self.btnEdit.installEventFilter(OpacityEventFilter(parent=self.btnEdit))
        self.btnRemove.setVisible(False)
        self.btnRemove.setIcon(IconRegistry.wrong_icon(color='black'))
        self.btnRemove.installEventFilter(OpacityEventFilter(parent=self.btnRemove))
        self.textSummary.textChanged.connect(self._synopsis_changed)
        self.btnRemove.clicked.connect(self._remove)

        self.btnType = QToolButton(self)
        self.btnType.setIconSize(QSize(24, 24))

        increase_font(self.lblKeyphrase, 2)

        self.setMinimumWidth(30)
        self.refresh()

    @overrides
    def enterEvent(self, event: QtCore.QEvent) -> None:
        self._enableActionButtons(True)

    @overrides
    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self._enableActionButtons(False)

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.btnType.setGeometry(self.width() // 2 - 18, 2, 36, 38)

    def refresh(self):
        bg_color: str = 'rgb(171, 171, 171)'
        if self.backstory.emotion == VERY_HAPPY:
            bg_color = 'rgb(0, 202, 148)'
        elif self.backstory.emotion == HAPPY:
            bg_color = '#93e5ab'
        elif self.backstory.emotion == UNHAPPY:
            bg_color = 'rgb(255, 142, 43)'
        elif self.backstory.emotion == VERY_UNHAPPY:
            bg_color = '#df2935'
        self.cardFrame.setStyleSheet(f'''
                    #cardFrame {{
                        border-top: 8px solid {bg_color};
                        border-bottom-left-radius: 12px;
                        border-bottom-right-radius: 12px;
                        background-color: #ffe8d6;
                        }}
                    ''')
        self.btnType.setStyleSheet(
            f'''QToolButton {{
                        background-color: white; border: 3px solid {bg_color};
                        border-radius: 18px; padding: 4px;
                    }}''')

        self.btnType.setIcon(IconRegistry.from_name(self.backstory.type_icon, self.backstory.type_color))
        self.lblKeyphrase.setText(self.backstory.keyphrase)
        self.textSummary.setPlainText(self.backstory.synopsis)

    def _enableActionButtons(self, enabled: bool):
        self.btnEdit.setVisible(enabled)
        self.btnRemove.setVisible(enabled)

    def _synopsis_changed(self):
        self.backstory.synopsis = self.textSummary.toPlainText()

    def _edit(self):
        backstory = BackstoryEditorDialog(self.backstory).display()
        if backstory:
            self.backstory.keyphrase = backstory.keyphrase
            self.backstory.emotion = backstory.emotion
            self.backstory.type = backstory.type
            self.backstory.type_icon = backstory.type_icon
            self.backstory.type_color = backstory.type_color
            self.refresh()

    def _remove(self):
        if ask_confirmation(f'Remove event "{self.backstory.keyphrase}"?'):
            self.deleteRequested.emit(self)


class CharacterBackstoryEvent(QWidget):
    def __init__(self, backstory: BackstoryEvent, aligment: int = Qt.AlignRight, parent=None):
        super(CharacterBackstoryEvent, self).__init__(parent)
        self.aligment = aligment
        self.card = CharacterBackstoryCard(backstory)

        self._layout = hbox(self, 0, 3)
        self.spacer = spacer_widget()
        self.spacer.setFixedWidth(self.width() // 2 + 3)
        if aligment == Qt.AlignRight:
            self.layout().addWidget(self.spacer)
            self.layout().addWidget(self.card)
        elif aligment == Qt.AlignLeft:
            self.layout().addWidget(self.card)
            self.layout().addWidget(self.spacer)
        else:
            self.layout().addWidget(self.card)

    def toggleAlignment(self):
        if self.aligment == Qt.AlignLeft:
            self.aligment = Qt.AlignRight
            self._layout.takeAt(0)
            self._layout.addWidget(self.spacer)
        else:
            self.aligment = Qt.AlignLeft
            self._layout.takeAt(1)
            self._layout.insertWidget(0, self.spacer)


class _ControlButtons(QWidget):

    def __init__(self, parent=None):
        super(_ControlButtons, self).__init__(parent)
        vbox(self)

        self.btnPlaceholderCircle = QToolButton(self)

        self.btnPlus = QToolButton(self)
        self.btnPlus.setIcon(IconRegistry.plus_icon('white'))
        self.btnSeparator = QToolButton(self)
        self.btnSeparator.setIcon(IconRegistry.from_name('ri.separator', 'white'))
        self.btnSeparator.setToolTip('Insert separator')

        self.layout().addWidget(self.btnPlaceholderCircle)
        self.layout().addWidget(self.btnPlus)
        self.layout().addWidget(self.btnSeparator)

        self.btnPlus.setHidden(True)
        self.btnSeparator.setHidden(True)

        bg_color = '#1d3557'
        for btn in [self.btnPlaceholderCircle, self.btnPlus, self.btnSeparator]:
            btn.setStyleSheet(f'''
                QToolButton {{ background-color: {bg_color}; border: 1px;
                        border-radius: 13px; padding: 2px;}}
                QToolButton:pressed {{background-color: grey;}}
            ''')
            btn.setCursor(Qt.PointingHandCursor)

        self.installEventFilter(self)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Enter:
            self.btnPlaceholderCircle.setHidden(True)
            self.btnPlus.setVisible(True)
            self.btnSeparator.setVisible(True)
        elif event.type() == QEvent.Leave:
            self.btnPlaceholderCircle.setVisible(True)
            self.btnPlus.setHidden(True)
            self.btnSeparator.setHidden(True)

        return super().eventFilter(watched, event)


class CharacterTimelineWidget(QWidget):
    def __init__(self, parent=None):
        super(CharacterTimelineWidget, self).__init__(parent)
        self.character: Optional[Character] = None
        self._layout = vbox(self, spacing=0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._spacers: List[QWidget] = []

    def setCharacter(self, character: Character):
        self.character = character
        self.refresh()

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        for sp in self._spacers:
            sp.setFixedWidth(self.width() // 2 + 3)

    def refresh(self):
        if self.character is None:
            return
        self._spacers.clear()
        clear_layout(self.layout())

        lblCharacter = QLabel(self)
        lblCharacter.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        transparent(lblCharacter)
        set_avatar(lblCharacter, self.character, 64)

        self._layout.addWidget(lblCharacter, alignment=Qt.AlignHCenter | Qt.AlignTop)

        for i, backstory in enumerate(self.character.backstory):
            orientation = Qt.AlignRight if i % 2 == 0 else Qt.AlignLeft
            event = CharacterBackstoryEvent(backstory, orientation, self)
            event.card.deleteRequested.connect(self._remove)

            self._spacers.append(event.spacer)
            event.spacer.setFixedWidth(self.width() // 2 + 3)

            self._addControlButtons(i)
            self._layout.addWidget(event)

        self._addControlButtons(-1)
        self.layout().addWidget(spacer_widget(vertical=True))

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor('#1d3557')))
        painter.drawRect(self.width() / 2 - 3, 64, 6, self.height() - 64)

        painter.end()

    def add(self, pos: int = -1):
        backstory: Optional[BackstoryEvent] = BackstoryEditorDialog().display()
        if backstory:
            card = CharacterBackstoryCard(backstory)
            card.deleteRequested.connect(self._remove)

            if pos > 0:
                self.character.backstory.insert(pos, backstory)
            else:
                self.character.backstory.append(backstory)
            self.refresh()

    def _remove(self, card: CharacterBackstoryCard):
        if card.backstory in self.character.backstory:
            self.character.backstory.remove(card.backstory)

        self.refresh()

    def _addControlButtons(self, pos: int):
        control = _ControlButtons(self)
        control.btnPlus.clicked.connect(partial(self.add, pos))
        self._layout.addWidget(control, alignment=Qt.AlignHCenter)


class CharacterEmotionButton(QToolButton):
    NEUTRAL_COLOR: str = 'rgb(171, 171, 171)'
    emotionChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(CharacterEmotionButton, self).__init__(parent)
        self._value = NEUTRAL
        self._color = self.NEUTRAL_COLOR
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(32, 32)
        menu = QMenu(self)
        self.setMenu(menu)
        menu.setMaximumWidth(64)
        self.setPopupMode(QToolButton.InstantPopup)
        if platform.is_windows():
            self._emoji_font = emoji_font(14)
        else:
            self._emoji_font = emoji_font(20)
        self.setFont(self._emoji_font)
        menu.setFont(self._emoji_font)
        menu.addAction(emoji.emojize(':smiling_face_with_smiling_eyes:'), lambda: self.setValue(VERY_HAPPY))
        menu.addAction(emoji.emojize(':slightly_smiling_face:'), lambda: self.setValue(HAPPY))
        menu.addAction(emoji.emojize(':neutral_face:'), lambda: self.setValue(NEUTRAL))
        menu.addAction(emoji.emojize(':worried_face:'), lambda: self.setValue(UNHAPPY))
        menu.addAction(emoji.emojize(':fearful_face:'), lambda: self.setValue(VERY_UNHAPPY))

    def value(self) -> int:
        return self._value

    def setValue(self, value: int):
        if value == VERY_UNHAPPY:
            self.setText(emoji.emojize(":fearful_face:"))
            self._color = 'rgb(239, 0, 0)'

        elif value == UNHAPPY:
            self.setText(emoji.emojize(":worried_face:"))
            self._color = 'rgb(255, 142, 43)'
        elif value == NEUTRAL:
            self.setText(emoji.emojize(":neutral_face:"))
            self._color = self.NEUTRAL_COLOR
        elif value == HAPPY:
            self.setText(emoji.emojize(":slightly_smiling_face:"))
            self._color = '#93e5ab'
        elif value == VERY_HAPPY:
            self.setText(emoji.emojize(":smiling_face_with_smiling_eyes:"))
            self._color = 'rgb(0, 202, 148)'

        self._value = value
        self.setStyleSheet(f'''QToolButton {{
            background-color: {self._color};
            border-radius: 10px;
        }}''')
        self.emotionChanged.emit()

    def color(self) -> str:
        return self._color


class JournalTextEdit(RichTextEditor):
    def __init__(self, parent=None):
        super(JournalTextEdit, self).__init__(parent)

        self.setToolbarVisible(False)


class JournalWidget(QWidget, Ui_JournalWidget):

    def __init__(self, parent=None):
        super(JournalWidget, self).__init__(parent)
        self.setupUi(self)
        self.novel: Optional[Novel] = None
        self.character: Optional[Character] = None
        self.textEditor: Optional[JournalTextEdit] = None

        self.selected_card: Optional[JournalCard] = None

        self.btnNew.setIcon(IconRegistry.document_edition_icon())
        self.btnNew.clicked.connect(self._new)

        self.btnBack.setIcon(IconRegistry.return_icon())
        self.btnBack.clicked.connect(self._closeEditor)

        self.stackedWidget.setCurrentWidget(self.pageCards)

        self.repo = RepositoryPersistenceManager.instance()

    def setCharacter(self, novel: Novel, character: Character):
        self.novel = novel
        self.character = character
        self._update_cards()

    def _new(self):
        journal = Document(title='New Journal entry')
        journal.loaded = True
        self.character.journals.insert(0, journal)
        self._update_cards()
        card = self.cardsJournal.cardAt(0)
        if card:
            card.select()
            self._edit(card)

    def _update_cards(self):
        self.selected_card = None
        self.cardsJournal.clear()

        for journal in self.character.journals:
            card = JournalCard(journal)
            self.cardsJournal.addCard(card)
            card.selected.connect(self._card_selected)
            card.doubleClicked.connect(self._edit)

    def _card_selected(self, card: JournalCard):
        if self.selected_card and self.selected_card is not card:
            self.selected_card.clearSelection()
        self.selected_card = card

    @busy
    def _edit(self, card: JournalCard):
        if not card.journal.loaded:
            json_client.load_document(self.novel, card.journal)

        self.stackedWidget.setCurrentWidget(self.pageEditor)
        clear_layout(self.wdgEditor.layout())

        self.textEditor = JournalTextEdit(self.wdgEditor)
        self.textEditor.setText(card.journal.content, card.journal.title)
        self.wdgEditor.layout().addWidget(self.textEditor)
        self.textEditor.textEditor.textChanged.connect(partial(self._textChanged, card.journal))
        self.textEditor.textTitle.textChanged.connect(partial(self._titleChanged, card.journal))

    def _closeEditor(self):
        self.stackedWidget.setCurrentWidget(self.pageCards)
        self.selected_card.refresh()

    def _textChanged(self, journal: Document):
        journal.content = self.textEditor.textEditor.toHtml()
        json_client.save_document(self.novel, journal)

    def _titleChanged(self, journal: Document):
        journal.title = self.textEditor.textTitle.toPlainText()
