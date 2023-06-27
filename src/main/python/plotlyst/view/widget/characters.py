"""
Plotlyst
Copyright (C) 2021-2023  Zsolt Kovari

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
import copy
import uuid
from dataclasses import dataclass
from functools import partial
from typing import Iterable, List, Optional, Dict, Union

import emoji
import qtanim
from PyQt6 import QtCore
from PyQt6.QtCore import QItemSelection, Qt, pyqtSignal, QSize, QObject, QEvent, QByteArray, QBuffer, QIODevice
from PyQt6.QtGui import QIcon, QPaintEvent, QPainter, QResizeEvent, QBrush, QColor, QImageReader, QImage, QPixmap, \
    QMouseEvent, QCursor, QAction, QShowEvent
from PyQt6.QtWidgets import QWidget, QToolButton, QButtonGroup, QFrame, QMenu, QSizePolicy, QLabel, QPushButton, \
    QHeaderView, QFileDialog, QMessageBox, QGridLayout, QWidgetAction
from overrides import overrides
from qthandy import vspacer, ask_confirmation, transparent, gc, line, btn_popup, incr_font, \
    spacer, clear_layout, vbox, hbox, flow, translucent, margins, bold
from qthandy.filter import InstantTooltipEventFilter, DisabledClickEventFilter, OpacityEventFilter
from qtmenu import MenuWidget, ScrollableMenuWidget

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR, NEUTRAL_EMOTION_COLOR, emotion_color, \
    CHARACTER_MAJOR_COLOR, CHARACTER_SECONDARY_COLOR
from src.main.python.plotlyst.core.domain import Novel, Character, Conflict, ConflictType, BackstoryEvent, \
    VERY_HAPPY, HAPPY, UNHAPPY, VERY_UNHAPPY, Scene, NEUTRAL, SceneStructureAgenda, ConflictReference, \
    Topic, TemplateValue
from src.main.python.plotlyst.core.template import secondary_role, guide_role, love_interest_role, sidekick_role, \
    contagonist_role, confidant_role, foil_role, supporter_role, adversary_role, antagonist_role, henchmen_role, \
    tertiary_role, SelectionItem, Role, TemplateFieldType, TemplateField, protagonist_role, RoleImportance, \
    promote_role, demote_role
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import emit_critical, EventListener, Event
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import CharacterSummaryChangedEvent
from src.main.python.plotlyst.model.common import DistributionFilterProxyModel
from src.main.python.plotlyst.model.distribution import CharactersScenesDistributionTableModel, \
    ConflictScenesDistributionTableModel, TagScenesDistributionTableModel, GoalScenesDistributionTableModel
from src.main.python.plotlyst.model.scenes_model import SceneConflictsModel
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import emoji_font, \
    link_buttons_to_pages, pointy, action, ButtonPressResizeEventFilter
from src.main.python.plotlyst.view.dialog.character import BackstoryEditorDialog
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog, ArtbreederDialog, ImageCropDialog
from src.main.python.plotlyst.view.generated.avatar_selectors_ui import Ui_AvatarSelectors
from src.main.python.plotlyst.view.generated.character_avatar_ui import Ui_CharacterAvatar
from src.main.python.plotlyst.view.generated.character_backstory_card_ui import Ui_CharacterBackstoryCard
from src.main.python.plotlyst.view.generated.character_conflict_widget_ui import Ui_CharacterConflictWidget
from src.main.python.plotlyst.view.generated.character_role_selector_ui import Ui_CharacterRoleSelector
from src.main.python.plotlyst.view.generated.character_topic_editor_ui import Ui_CharacterTopicEditor
from src.main.python.plotlyst.view.generated.characters_progress_widget_ui import Ui_CharactersProgressWidget
from src.main.python.plotlyst.view.generated.scene_conflict_intensity_ui import Ui_ConflictReferenceEditor
from src.main.python.plotlyst.view.generated.scene_dstribution_widget_ui import Ui_CharactersScenesDistributionWidget
from src.main.python.plotlyst.view.icons import avatars, IconRegistry, set_avatar
from src.main.python.plotlyst.view.style.base import apply_bg_image
from src.main.python.plotlyst.view.widget.button import SelectionItemPushButton
from src.main.python.plotlyst.view.widget.display import IconText, Icon
from src.main.python.plotlyst.view.widget.labels import ConflictLabel, CharacterLabel
from src.main.python.plotlyst.view.widget.progress import CircularProgressBar, ProgressTooltipMode, \
    CharacterRoleProgressChart
from src.main.python.plotlyst.view.widget.topic import TopicsEditor


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
        self._scenes_proxy.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._scenes_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._scenes_proxy.setSortRole(CharactersScenesDistributionTableModel.SortRole)
        self._scenes_proxy.sort(CharactersScenesDistributionTableModel.IndexTags, Qt.SortOrder.DescendingOrder)
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

        transparent(self.spinAverage)

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
            self.tblCharacters.hideColumn(0)
            self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexTags, 170)
            self.tblCharacters.setMaximumWidth(170)

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
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        pointy(self)
        self.refresh()

    def refresh(self):
        self.setToolTip(self.character.name)
        self.setIcon(avatars.avatar(self.character))


class CharacterSelectorButtons(QWidget):
    characterToggled = pyqtSignal(Character, bool)
    characterClicked = pyqtSignal(Character)

    def __init__(self, parent=None, exclusive: bool = True):
        super(CharacterSelectorButtons, self).__init__(parent)
        hbox(self)
        self.container = QWidget()
        self.container.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)

        self._layout = flow(self.container)

        self.layout().addWidget(self.container)

        self._btn_group = QButtonGroup()
        self._buttons: List[CharacterToolButton] = []
        self._buttonsPerCharacters: Dict[Character, CharacterToolButton] = {}
        self.setExclusive(exclusive)

    def exclusive(self) -> bool:
        return self._btn_group.exclusive()

    def setExclusive(self, exclusive: bool):
        self._btn_group.setExclusive(exclusive)

    def characters(self, all: bool = True) -> Iterable[Character]:
        return [x.character for x in self._buttons if all or x.isChecked()]

    def setCharacters(self, characters: Iterable[Character], checkAll: bool = True):
        self.clear()

        for char in characters:
            self.addCharacter(char, checked=checkAll)

        if not self._buttons:
            return
        if self._btn_group.exclusive():
            self._buttons[0].setChecked(True)

    def updateCharacters(self, characters: Iterable[Character], checkAll: bool = True):
        if not self._buttons:
            return self.setCharacters(characters, checkAll)

        current_characters = set(x for x in self._buttonsPerCharacters.keys())

        for c in characters:
            if c in self._buttonsPerCharacters.keys():
                current_characters.remove(c)
            else:
                self.addCharacter(c, checkAll)

        for c in current_characters:
            self.removeCharacter(c)

        for btn in self._buttons:
            btn.refresh()

    def addCharacter(self, character: Character, checked: bool = True):
        tool_btn = CharacterToolButton(character)

        self._buttons.append(tool_btn)
        self._buttonsPerCharacters[character] = tool_btn
        self._btn_group.addButton(tool_btn)
        self._layout.addWidget(tool_btn)

        tool_btn.setChecked(checked)

        tool_btn.toggled.connect(partial(self.characterToggled.emit, character))
        tool_btn.clicked.connect(partial(self.characterClicked.emit, character))
        tool_btn.installEventFilter(OpacityEventFilter(parent=tool_btn, ignoreCheckedButton=True))

    def removeCharacter(self, character: Character):
        if character not in self._buttonsPerCharacters:
            return

        btn = self._buttonsPerCharacters.pop(character)
        if btn.isChecked():
            btn.setChecked(False)

        self._btn_group.removeButton(btn)
        self._buttons.remove(btn)
        self._layout.removeWidget(btn)
        gc(btn)

    def clear(self):
        clear_layout(self._layout)

        for btn in self._buttons:
            self._btn_group.removeButton(btn)
            self._layout.removeWidget(btn)
            gc(btn)

        self._buttons.clear()
        self._buttonsPerCharacters.clear()


class CharacterConflictWidget(QFrame, Ui_CharacterConflictWidget):
    conflictSelectionChanged = pyqtSignal()

    def __init__(self, novel: Novel, scene: Scene, agenda: SceneStructureAgenda, parent=None):
        super(CharacterConflictWidget, self).__init__(parent)
        self.novel = novel
        self.scene = scene
        self.agenda = agenda
        self.setupUi(self)

        self.repo = RepositoryPersistenceManager.instance()

        self.btnCharacter.setIcon(IconRegistry.conflict_character_icon())
        self.btnCharacter.setToolTip('<b style="color:#c1666b">Character</b>')
        self.btnCharacter.installEventFilter(InstantTooltipEventFilter(parent=self.btnCharacter))
        self.btnSociety.setIcon(IconRegistry.conflict_society_icon())
        self.btnSociety.setToolTip('<b style="color:#69306d">Society</b>')
        self.btnSociety.installEventFilter(InstantTooltipEventFilter(parent=self.btnSociety))
        self.btnNature.setIcon(IconRegistry.conflict_nature_icon())
        self.btnNature.setToolTip('<b style="color:#157a6e">Nature</b>')
        self.btnNature.installEventFilter(InstantTooltipEventFilter(parent=self.btnNature))
        self.btnTechnology.setIcon(IconRegistry.conflict_technology_icon())
        self.btnTechnology.setToolTip('<b style="color:#4a5859">Technology</b>')
        self.btnTechnology.installEventFilter(InstantTooltipEventFilter(parent=self.btnTechnology))
        self.btnSupernatural.setIcon(IconRegistry.conflict_supernatural_icon())
        self.btnSupernatural.setToolTip('<b style="color:#ac7b84">Supernatural</b>')
        self.btnSupernatural.installEventFilter(InstantTooltipEventFilter(parent=self.btnSupernatural))
        self.btnSelf.setIcon(IconRegistry.conflict_self_icon())
        self.btnSelf.setToolTip('<b style="color:#94b0da">Self</b>')
        self.btnSelf.installEventFilter(InstantTooltipEventFilter(parent=self.btnSelf))

        self._model = SceneConflictsModel(self.novel, self.scene, self.agenda)
        self._model.setCheckable(True, SceneConflictsModel.ColName)
        self._model.selection_changed.connect(self._previousConflictSelected)
        self.tblConflicts.setModel(self._model)
        self.tblConflicts.horizontalHeader().hideSection(SceneConflictsModel.ColBgColor)
        self.tblConflicts.horizontalHeader().setSectionResizeMode(SceneConflictsModel.ColIcon,
                                                                  QHeaderView.ResizeMode.ResizeToContents)
        self.tblConflicts.horizontalHeader().setSectionResizeMode(SceneConflictsModel.ColName,
                                                                  QHeaderView.ResizeMode.Stretch)
        self._update_characters()
        self.btnAddNew.setIcon(IconRegistry.ok_icon())
        self.btnAddNew.installEventFilter(DisabledClickEventFilter(self, lambda: qtanim.shake(self.lineKey)))
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

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        pass

    def _update_characters(self):
        for char in self.novel.characters:
            if self.agenda.character_id and char.id != self.agenda.character_id:
                self.cbCharacter.addItem(avatars.avatar(char), char.name, char)

    def _type_toggled(self):
        lbl_prefix = 'Character vs.'
        self.cbCharacter.setVisible(self.btnCharacter.isChecked())
        if self.btnCharacter.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} <b style="color:#c1666b">Character</b>')
            self._type = ConflictType.CHARACTER
        elif self.btnSociety.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} <b style="color:#69306d">Society</b>')
            self._type = ConflictType.SOCIETY
        elif self.btnNature.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} <b style="color:#157a6e">Nature</b>')
            self._type = ConflictType.NATURE
        elif self.btnTechnology.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} <b style="color:#4a5859">Technology</b>')
            self._type = ConflictType.TECHNOLOGY
        elif self.btnSupernatural.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} <b style="color:#ac7b84">Supernatural</b>')
            self._type = ConflictType.SUPERNATURAL
        elif self.btnSelf.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} <b style="color:#94b0da">Self</b>')
            self._type = ConflictType.SELF

    def _keyphrase_edited(self, text: str):
        self.btnAddNew.setEnabled(len(text) > 0)

    def _add_new(self):
        if not self.agenda.character_id:
            return emit_critical('Select agenda or POV character first')
        conflict = Conflict(self.lineKey.text(), self._type, character_id=self.agenda.character_id)
        if self._type == ConflictType.CHARACTER:
            conflict.conflicting_character_id = self.cbCharacter.currentData().id

        self.novel.conflicts.append(conflict)
        self.agenda.conflict_references.append(ConflictReference(conflict.id))
        self.repo.update_novel(self.novel)
        self.conflictSelectionChanged.emit()
        self.refresh()
        self.lineKey.clear()

    def _previousConflictSelected(self):
        conflicts = self._model.selections()
        conflict: Conflict = conflicts.pop()
        self.agenda.conflict_references.append(ConflictReference(conflict.id))
        self.conflictSelectionChanged.emit()


class ConflictIntensityEditor(QWidget, Ui_ConflictReferenceEditor):
    def __init__(self, conflict_ref: ConflictReference, parent=None):
        super(ConflictIntensityEditor, self).__init__(parent)
        self.conflict_ref = conflict_ref
        self.setupUi(self)
        self.sliderIntensity.setValue(self.conflict_ref.intensity)
        self.sliderIntensity.valueChanged.connect(self._valueChanged)

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        pass

    def _valueChanged(self, value: int):
        if value == 0:
            self.sliderIntensity.setValue(1)
            return
        self.conflict_ref.intensity = value


class CharacterConflictSelector(QWidget):
    conflictSelected = pyqtSignal()

    def __init__(self, novel: Novel, scene: Scene, simplified: bool = False, parent=None):
        super(CharacterConflictSelector, self).__init__(parent)
        self.novel = novel
        self.scene = scene
        self.conflict: Optional[Conflict] = None
        self.conflict_ref: Optional[ConflictReference] = None
        hbox(self)

        self.label: Optional[ConflictLabel] = None

        self.btnLinkConflict = QPushButton(self)
        if not simplified:
            self.btnLinkConflict.setText('Track conflict')
        self.layout().addWidget(self.btnLinkConflict)
        self.btnLinkConflict.setIcon(IconRegistry.conflict_icon())
        self.btnLinkConflict.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnLinkConflict.setStyleSheet('''
                        QPushButton {
                            border: 2px dotted grey;
                            border-radius: 6px;
                            font: italic;
                        }
                        QPushButton:hover {
                            border: 2px dotted orange;
                            color: orange;
                            font: normal;
                        }
                        QPushButton:pressed {
                            border: 2px solid white;
                        }
                    ''')

        self.btnLinkConflict.installEventFilter(OpacityEventFilter(parent=self.btnLinkConflict))
        self.selectorWidget = CharacterConflictWidget(self.novel, self.scene, self.scene.agendas[0],
                                                      self.btnLinkConflict)
        btn_popup(self.btnLinkConflict, self.selectorWidget)

        self.selectorWidget.conflictSelectionChanged.connect(self._conflictSelected)

    def setConflict(self, conflict: Conflict, conflict_ref: ConflictReference):
        self.conflict = conflict
        self.conflict_ref = conflict_ref
        self.label = ConflictLabel(self.novel, self.conflict)
        pointy(self.label)
        self.label.removalRequested.connect(self._remove)
        self.label.clicked.connect(self._conflictRefClicked)
        self.layout().addWidget(self.label)
        self.btnLinkConflict.setHidden(True)

    def _conflictSelected(self):
        new_conflict = self.scene.agendas[0].conflicts(self.novel)[-1]
        new_conflict_ref = self.scene.agendas[0].conflict_references[-1]
        # self.btnLinkConflict.menu().hide()
        self.setConflict(new_conflict, new_conflict_ref)

        self.conflictSelected.emit()

    def _conflictRefClicked(self):
        menu = QMenu(self.label)
        action = QWidgetAction(menu)
        action.setDefaultWidget(ConflictIntensityEditor(self.conflict_ref))
        menu.addAction(action)
        menu.popup(QCursor.pos())

    def _remove(self):
        if self.parent():
            anim = qtanim.fade_out(self, duration=150)
            anim.finished.connect(self.__destroy)

    def __destroy(self):
        self.scene.agendas[0].remove_conflict(self.conflict)
        self.parent().layout().removeWidget(self)
        gc(self)


class CharacterSelectorButton(QToolButton):
    characterSelected = pyqtSignal(Character)

    def __init__(self, novel: Novel, parent=None, opacityEffectEnabled: bool = True, iconSize: int = 32):
        super().__init__(parent)
        self._novel = novel
        self._iconSize = iconSize
        self._setIconSize = self._iconSize + 4
        pointy(self)
        self._opacityEffectEnabled = opacityEffectEnabled
        if self._opacityEffectEnabled:
            self._opacityFilter = OpacityEventFilter(self)
        else:
            self._opacityFilter = None
        self._menu = MenuWidget(self)
        self._menu.aboutToShow.connect(self._fillUpMenu)
        self.clear()

    def setCharacter(self, character: Character):
        self.setIcon(avatars.avatar(character))
        transparent(self)
        if self._opacityEffectEnabled:
            self.removeEventFilter(self._opacityFilter)
            translucent(self, 1.0)
        self.setIconSize(QSize(self._setIconSize, self._setIconSize))

    def clear(self):
        self.setStyleSheet('''
                QToolButton {
                    border: 2px dotted grey;
                    border-radius: 6px;
                }
                QToolButton:hover {
                    border: 2px dotted black;
                }
        ''')
        self.setIcon(IconRegistry.character_icon('grey'))
        self.setIconSize(QSize(self._iconSize, self._iconSize))
        if self._opacityEffectEnabled:
            self.installEventFilter(self._opacityFilter)

    def _selected(self, character: Character):
        self.setCharacter(character)
        self.characterSelected.emit(character)

    def _fillUpMenu(self):
        self._menu.clear()

        for char in self._novel.characters:
            self._menu.addAction(
                action(char.name, avatars.avatar(char), slot=partial(self._selected, char), parent=self._menu))


class CharacterLinkWidget(QWidget):
    characterSelected = pyqtSignal(Character)

    def __init__(self, parent=None):
        super(CharacterLinkWidget, self).__init__(parent)
        hbox(self)
        self.novel = app_env.novel
        self.character: Optional[Character] = None
        self.label: Optional[CharacterLabel] = None

        self.btnLinkCharacter = QPushButton(self)
        self.layout().addWidget(self.btnLinkCharacter)
        self.btnLinkCharacter.setIcon(IconRegistry.character_icon())
        self.btnLinkCharacter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnLinkCharacter.setStyleSheet('''
                QPushButton {
                    border: 2px dotted grey;
                    border-radius: 6px;
                    font: italic;
                }
                QPushButton:hover {
                    border: 2px dotted darkBlue;
                }
            ''')

        self._menu = ScrollableMenuWidget(self.btnLinkCharacter)

    def setDefaultText(self, value: str):
        self.btnLinkCharacter.setText(value)

    def setCharacter(self, character: Character):
        if self.character and character.id == self.character.id:
            return
        self.character = character

        self._clearLabel()
        self.label = CharacterLabel(self.character)
        self.label.setToolTip(f'<html>Agenda character: <b>{character.name}</b>')
        self.label.installEventFilter(OpacityEventFilter(self.label, enterOpacity=0.7, leaveOpacity=1.0))
        pointy(self.label)
        self.label.clicked.connect(lambda: self._menu.exec())
        self.layout().addWidget(self.label)
        self.btnLinkCharacter.setHidden(True)

    def reset(self):
        self._clearLabel()
        self.btnLinkCharacter.setVisible(True)

    def setAvailableCharacters(self, characters: List[Character]):
        self._menu.clear()
        for character in characters:
            self._menu.addAction(
                action(character.name, avatars.avatar(character), partial(self._characterClicked, character)))

    def _clearLabel(self):
        if self.label is not None:
            self.layout().removeWidget(self.label)
            gc(self.label)
            self.label = None

    def _characterClicked(self, character: Character):
        self.btnLinkCharacter.menu().hide()
        self.setCharacter(character)
        self.characterSelected.emit(character)


class CharacterBackstoryCard(QFrame, Ui_CharacterBackstoryCard):
    edited = pyqtSignal()
    deleteRequested = pyqtSignal(object)
    relationChanged = pyqtSignal()

    def __init__(self, backstory: BackstoryEvent, first: bool = False, parent=None):
        super(CharacterBackstoryCard, self).__init__(parent)
        self.setupUi(self)
        self.backstory = backstory
        self.first = first

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

        incr_font(self.lblKeyphrase, 2)
        bold(self.lblKeyphrase)

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
                        background-color: {RELAXED_WHITE_COLOR}; border: 3px solid {bg_color};
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
        self.edited.emit()

    def _edit(self):
        backstory = BackstoryEditorDialog(self.backstory, showRelationOption=not self.first).display()
        if backstory:
            relation_changed = False
            if self.backstory.follow_up != backstory.follow_up:
                relation_changed = True
            self.backstory.keyphrase = backstory.keyphrase
            self.backstory.emotion = backstory.emotion
            self.backstory.type = backstory.type
            self.backstory.type_icon = backstory.type_icon
            self.backstory.type_color = backstory.type_color
            self.backstory.follow_up = backstory.follow_up
            self.refresh()
            self.edited.emit()
            if relation_changed:
                self.relationChanged.emit()

    def _remove(self):
        if self.backstory.synopsis and not ask_confirmation(f'Remove event "{self.backstory.keyphrase}"?'):
            return
        self.deleteRequested.emit(self)


class CharacterBackstoryEvent(QWidget):
    def __init__(self, backstory: BackstoryEvent, alignment: int = Qt.AlignmentFlag.AlignRight, first: bool = False,
                 parent=None):
        super(CharacterBackstoryEvent, self).__init__(parent)
        self.alignment = alignment
        self.card = CharacterBackstoryCard(backstory, first)

        self._layout = hbox(self, 0, 3)
        self.spacer = spacer()
        self.spacer.setFixedWidth(self.width() // 2 + 3)
        if self.alignment == Qt.AlignmentFlag.AlignRight:
            self.layout().addWidget(self.spacer)
            self._layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignLeft)
        elif self.alignment == Qt.AlignmentFlag.AlignLeft:
            self._layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignRight)
            self.layout().addWidget(self.spacer)
        else:
            self.layout().addWidget(self.card)

    def toggleAlignment(self):
        if self.alignment == Qt.AlignmentFlag.AlignLeft:
            self.alignment = Qt.AlignmentFlag.AlignRight
            self._layout.takeAt(0)
            self._layout.addWidget(self.spacer)
            self._layout.setAlignment(self.card, Qt.AlignmentFlag.AlignRight)
        else:
            self.alignment = Qt.AlignmentFlag.AlignLeft
            self._layout.takeAt(1)
            self._layout.insertWidget(0, self.spacer)
            self._layout.setAlignment(self.card, Qt.AlignmentFlag.AlignLeft)


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
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.installEventFilter(self)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            self.btnPlaceholderCircle.setHidden(True)
            self.btnPlus.setVisible(True)
            # self.btnSeparator.setVisible(True)
        elif event.type() == QEvent.Type.Leave:
            self.btnPlaceholderCircle.setVisible(True)
            self.btnPlus.setHidden(True)
            # self.btnSeparator.setHidden(True)

        return super().eventFilter(watched, event)


class CharacterTimelineWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent=None):
        self._spacers: List[QWidget] = []
        super(CharacterTimelineWidget, self).__init__(parent)
        self.character: Optional[Character] = None
        self._layout = vbox(self, spacing=0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def setCharacter(self, character: Character):
        self.character = character
        self.refresh()

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        for sp in self._spacers:
            sp.setFixedWidth(self.width() // 2 + 3)

    def refreshCharacter(self):
        item = self._layout.itemAt(0)
        if item:
            wdg = item.widget()
            if isinstance(wdg, QLabel):
                set_avatar(wdg, self.character, 64)

    def refresh(self):
        if self.character is None:
            return
        self._spacers.clear()
        clear_layout(self.layout())

        lblCharacter = QLabel(self)
        lblCharacter.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        transparent(lblCharacter)
        set_avatar(lblCharacter, self.character, 64)

        self._layout.addWidget(lblCharacter, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        prev_alignment = None
        for i, backstory in enumerate(self.character.backstory):
            if prev_alignment is None:
                alignment = Qt.AlignmentFlag.AlignRight
            elif backstory.follow_up and prev_alignment:
                alignment = prev_alignment
            elif prev_alignment == Qt.AlignmentFlag.AlignLeft:
                alignment = Qt.AlignmentFlag.AlignRight
            else:
                alignment = Qt.AlignmentFlag.AlignLeft
            prev_alignment = alignment
            event = CharacterBackstoryEvent(backstory, alignment, first=i == 0, parent=self)
            event.card.deleteRequested.connect(self._remove)

            self._spacers.append(event.spacer)
            event.spacer.setFixedWidth(self.width() // 2 + 3)

            self._addControlButtons(i)
            self._layout.addWidget(event)

            event.card.edited.connect(self.changed.emit)
            event.card.relationChanged.connect(self.changed.emit)
            event.card.relationChanged.connect(self.refresh)

        self._addControlButtons(-1)
        spacer_ = spacer(vertical=True)
        spacer_.setMinimumHeight(200)
        self.layout().addWidget(spacer_)

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor('#1d3557')))
        painter.drawRect(self.width() / 2 - 3, 64, 6, self.height() - 64)

        painter.end()

    def add(self, pos: int = -1):
        backstory: Optional[BackstoryEvent] = BackstoryEditorDialog(
            showRelationOption=len(self.character.backstory) > 0).display()
        if backstory:
            card = CharacterBackstoryCard(backstory)
            card.deleteRequested.connect(self._remove)

            if pos >= 0:
                self.character.backstory.insert(pos, backstory)
            else:
                self.character.backstory.append(backstory)
            self.refresh()
            self.changed.emit()

    def _remove(self, card: CharacterBackstoryCard):
        if card.backstory in self.character.backstory:
            self.character.backstory.remove(card.backstory)

        self.refresh()
        self.changed.emit()

    def _addControlButtons(self, pos: int):
        control = _ControlButtons(self)
        control.btnPlus.clicked.connect(partial(self.add, pos))
        self._layout.addWidget(control, alignment=Qt.AlignmentFlag.AlignHCenter)


class CharacterEmotionButton(QToolButton):
    emotionChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(CharacterEmotionButton, self).__init__(parent)
        self._value = NEUTRAL
        self._color = NEUTRAL_EMOTION_COLOR
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(32, 32)
        pointy(self)
        transparent(self)

        menu = QMenu(self)
        self.setMenu(menu)
        menu.setMaximumWidth(64)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._emoji_font = emoji_font()
        self.setFont(self._emoji_font)
        menu.setFont(self._emoji_font)
        menu.addAction(emoji.emojize(':smiling_face_with_smiling_eyes:'), lambda: self._emotionClicked(VERY_HAPPY))
        menu.addAction(emoji.emojize(':slightly_smiling_face:'), lambda: self._emotionClicked(HAPPY))
        menu.addAction(emoji.emojize(':neutral_face:'), lambda: self._emotionClicked(NEUTRAL))
        menu.addAction(emoji.emojize(':worried_face:'), lambda: self._emotionClicked(UNHAPPY))
        menu.addAction(emoji.emojize(':fearful_face:'), lambda: self._emotionClicked(VERY_UNHAPPY))

        self._setAlready: bool = False

    def value(self) -> int:
        return self._value

    def setValue(self, value: int):
        if value == VERY_UNHAPPY:
            self.setText(emoji.emojize(":fearful_face:"))
        elif value == UNHAPPY:
            self.setText(emoji.emojize(":worried_face:"))
        elif value == NEUTRAL:
            self.setText(emoji.emojize(":neutral_face:"))
        elif value == HAPPY:
            self.setText(emoji.emojize(":slightly_smiling_face:"))
        elif value == VERY_HAPPY:
            self.setText(emoji.emojize(":smiling_face_with_smiling_eyes:"))

        self._color = emotion_color(value)

        self._value = value
        if self._setAlready:
            qtanim.glow(self, duration=300, radius=100, color=QColor(self._color))
        else:
            self._setAlready = True

    def color(self) -> str:
        return self._color

    def _emotionClicked(self, value: int):
        self.setValue(value)
        self.emotionChanged.emit()


class AvatarSelectors(QWidget, Ui_AvatarSelectors):
    updated = pyqtSignal()
    selectorChanged = pyqtSignal()

    def __init__(self, character: Character, parent=None):
        super(AvatarSelectors, self).__init__(parent)
        self.setupUi(self)
        self.character = character
        self.btnUploadAvatar.setIcon(IconRegistry.upload_icon(color='white'))
        self.btnUploadAvatar.clicked.connect(self._upload_avatar)
        self.btnAi.setIcon(IconRegistry.from_name('mdi.robot-happy-outline', 'white'))
        self.btnAi.clicked.connect(self._select_ai)
        self.btnInitial.setIcon(IconRegistry.from_name('mdi.alpha-a-circle'))
        self.btnRole.setIcon(IconRegistry.from_name('fa5s.chess-bishop'))
        self.btnCustomIcon.setIcon(IconRegistry.icons_icon())
        if character.avatar:
            pass
        else:
            self.btnImage.setHidden(True)
            if self.character.prefs.avatar.use_image:
                self.character.prefs.avatar.allow_initial()

        self.btnGroupSelectors.buttonClicked.connect(self._selectorClicked)
        self.refresh()

    def refresh(self):
        prefs = self.character.prefs.avatar
        if prefs.use_image:
            self.btnImage.setChecked(True)
            self.btnImage.setVisible(True)
        elif prefs.use_initial:
            self.btnInitial.setChecked(True)
        elif prefs.use_role:
            self.btnRole.setChecked(True)
        elif prefs.use_custom_icon:
            self.btnCustomIcon.setChecked(True)

        if prefs.icon:
            self.btnCustomIcon.setIcon(IconRegistry.from_name(prefs.icon, prefs.icon_color))
        if self.character.role:
            self.btnRole.setIcon(IconRegistry.from_name(self.character.role.icon, self.character.role.icon_color))
        if avatars.has_name_initial_icon(self.character):
            self.btnInitial.setIcon(avatars.name_initial_icon(self.character))
        if self.character.avatar:
            self.btnImage.setIcon(QIcon(avatars.image(self.character)))

    def _selectorClicked(self):
        if self.btnImage.isChecked():
            self.character.prefs.avatar.allow_image()
        elif self.btnInitial.isChecked():
            self.character.prefs.avatar.allow_initial()
        elif self.btnRole.isChecked():
            self.character.prefs.avatar.allow_role()
        elif self.btnCustomIcon.isChecked():
            self.character.prefs.avatar.allow_custom_icon()
            result = IconSelectorDialog().display()
            if result:
                self.character.prefs.avatar.icon = result[0]
                self.character.prefs.avatar.icon_color = result[1].name()

        self.selectorChanged.emit()

    def _upload_avatar(self):
        filename: str = QFileDialog.getOpenFileName(None, 'Choose an image', '', 'Images (*.png *.jpg *jpeg)')
        if not filename or not filename[0]:
            return
        reader = QImageReader(filename[0])
        reader.setAutoTransform(True)
        image: QImage = reader.read()
        if image is None:
            QMessageBox.warning(self, 'Error while loading image',
                                'Could not load image. Did you select a valid image? (e.g.: png, jpg, jpeg)')
            return
        if image.width() < 128 or image.height() < 128:
            QMessageBox.warning(self, 'Uploaded image is too small',
                                'The uploaded image is too small. It must be larger than 128 pixels')
            return

        pixmap = QPixmap.fromImage(image)
        crop = ImageCropDialog().display(pixmap)
        if crop:
            self._update_avatar(crop)

    def _update_avatar(self, image: Union[QImage, QPixmap]):
        array = QByteArray()
        buffer = QBuffer(array)
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, 'PNG')
        self.character.avatar = array
        self.character.prefs.avatar.allow_image()
        self.refresh()

        self.updated.emit()

    def _select_ai(self):
        diag = ArtbreederDialog()
        pixmap = diag.display()
        if pixmap:
            self._update_avatar(pixmap)


class CharacterAvatar(QWidget, Ui_CharacterAvatar):
    avatarUpdated = pyqtSignal()

    def __init__(self, parent=None):
        super(CharacterAvatar, self).__init__(parent)
        self.setupUi(self)
        apply_bg_image(self.wdgPovFrame, resource_registry.circular_frame1)
        self.wdgPovFrame.setFixedSize(190, 190)
        self.btnPov.installEventFilter(OpacityEventFilter(parent=self.btnPov, enterOpacity=0.7, leaveOpacity=1.0))

        self._character: Optional[Character] = None
        self._uploaded: bool = False
        self._uploadSelectorsEnabled: bool = False

        self.reset()

    def setUploadPopupMenu(self):
        if not self._character:
            raise ValueError('Set character first')
        wdg = AvatarSelectors(self._character)
        wdg.updated.connect(self._uploadedAvatar)
        wdg.selectorChanged.connect(self.updateAvatar)
        btn_popup(self.btnPov, wdg)

    def setCharacter(self, character: Character):
        self._character = character
        self.updateAvatar()

    def updateAvatar(self):
        self.btnPov.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        if self._character.prefs.avatar.use_role or self._character.prefs.avatar.use_custom_icon:
            self.btnPov.setIconSize(QSize(132, 132))
        else:
            self.btnPov.setIconSize(QSize(168, 168))
        avatar = avatars.avatar(self._character, fallback=False)
        if avatar:
            self.btnPov.setIcon(avatar)
        else:
            self.reset()
        self.avatarUpdated.emit()

    def reset(self):
        self.btnPov.setIconSize(QSize(118, 118))
        self.btnPov.setIcon(IconRegistry.character_icon(color='grey'))
        self.btnPov.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

    def imageUploaded(self) -> bool:
        return self._uploaded

    def _uploadedAvatar(self):
        self._uploaded = True
        avatars.update_image(self._character)
        self.updateAvatar()


class CharacterRoleSelector(QWidget, Ui_CharacterRoleSelector):
    roleSelected = pyqtSignal(SelectionItem)
    rolePromoted = pyqtSignal(SelectionItem)

    def __init__(self, parent=None):
        super(CharacterRoleSelector, self).__init__(parent)
        self.setupUi(self)

        self.btnItemProtagonist.setSelectionItem(copy.deepcopy(protagonist_role))
        self.btnItemAntagonist.setSelectionItem(copy.deepcopy(antagonist_role))
        self.btnItemContagonist.setSelectionItem(copy.deepcopy(contagonist_role))
        self.btnItemSecondary.setSelectionItem(copy.deepcopy(secondary_role))
        self.btnItemGuide.setSelectionItem(copy.deepcopy(guide_role))
        self.btnItemLoveInterest.setSelectionItem(copy.deepcopy(love_interest_role))
        self.btnItemSidekick.setSelectionItem(copy.deepcopy(sidekick_role))
        self.btnItemConfidant.setSelectionItem(copy.deepcopy(confidant_role))
        self.btnItemFoil.setSelectionItem(copy.deepcopy(foil_role))
        self.btnItemSupporter.setSelectionItem(copy.deepcopy(supporter_role))
        self.btnItemAdversary.setSelectionItem(copy.deepcopy(adversary_role))
        self.btnItemTertiary.setSelectionItem(copy.deepcopy(tertiary_role))
        self.btnItemHenchmen.setSelectionItem(copy.deepcopy(henchmen_role))

        translucent(self.iconMajor, 0.7)
        translucent(self.iconSecondary, 0.7)
        translucent(self.iconMinor, 0.7)

        incr_font(self.lblRole, 2)
        self.btnPromote.setIcon(IconRegistry.from_name('mdi.chevron-double-up', 'grey', color_on=CHARACTER_MAJOR_COLOR))
        pointy(self.btnPromote)
        self.btnPromote.checkedColor = CHARACTER_MAJOR_COLOR

        link_buttons_to_pages(self.stackedWidget, [(self.btnItemProtagonist, self.pageProtagonist),
                                                   (self.btnItemAntagonist, self.pageAntagonist),
                                                   (self.btnItemContagonist, self.pageContagonist),
                                                   (self.btnItemSecondary, self.pageSecondary),
                                                   (self.btnItemGuide, self.pageGuide),
                                                   (self.btnItemLoveInterest, self.pageLoveInterest),
                                                   (self.btnItemSidekick, self.pageSidekick),
                                                   (self.btnItemConfidant, self.pageConfidant),
                                                   (self.btnItemFoil, self.pageFoil),
                                                   (self.btnItemSupporter, self.pageSupporter),
                                                   (self.btnItemAdversary, self.pageAdversary),
                                                   (self.btnItemTertiary, self.pageTertiary),
                                                   (self.btnItemHenchmen, self.pageHenchmen)
                                                   ])

        for btn in self.buttonGroup.buttons():
            btn.setStyleSheet('''
                QPushButton {
                    border: 1px hidden black;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
                QPushButton:checked {
                    background-color: #ced4da;
                }
            ''')
            btn.toggled.connect(partial(self._roleToggled, btn))
            btn.itemDoubleClicked.connect(self._select)

        self._currentRole = protagonist_role
        self.btnItemProtagonist.setChecked(True)
        self.btnPromote.clicked.connect(self._promoted)

        self.btnSelect.setIcon(IconRegistry.ok_icon('white'))
        self.btnSelect.clicked.connect(self._select)

    @overrides
    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        pass

    def setActiveRole(self, role: Role):
        self._updateSelectionButton(role, checked=True)

    def _updateSelectionButton(self, role: Role, checked: bool = False):
        for btn in self.buttonGroup.buttons():
            if btn.selectionItem().text == role.text:
                btn.setSelectionItem(role)
                if checked:
                    btn.setChecked(True)
                break

    def _roleToggled(self, btn: SelectionItemPushButton, toggled: bool):
        if toggled:
            role: Role = btn.selectionItem()
            self._currentRole = role
            self.iconRole.setRole(role, animate=True)
            self.lblRole.setText(role.text)
            self.btnPromote.setVisible(role.can_be_promoted)
            self.btnPromote.setChecked(role.promoted)

            self._updateRoleIcon()

    def _updateRoleIcon(self, anim: bool = False):
        self.iconMajor.setDisabled(True)
        self.iconSecondary.setDisabled(True)
        self.iconMinor.setDisabled(True)

        if self._currentRole.is_major():
            self.iconMajor.setEnabled(True)
            if anim:
                qtanim.glow(self.iconMajor, color=QColor(CHARACTER_MAJOR_COLOR))
        elif self._currentRole.is_secondary():
            self.iconSecondary.setEnabled(True)
            if anim:
                qtanim.glow(self.iconSecondary, color=QColor(CHARACTER_SECONDARY_COLOR))
        else:
            self.iconMinor.setEnabled(True)

    def _promoted(self, checked: bool):
        if self._currentRole.can_be_promoted:
            self._currentRole.promoted = checked
            self._updateRoleIcon(anim=True)
            if checked:
                promote_role(self._currentRole)
            else:
                demote_role(self._currentRole)

            self.iconRole.setRole(self._currentRole, animate=True)
            self._updateSelectionButton(self._currentRole)
            self.rolePromoted.emit(self._currentRole)

    def _select(self):
        self.roleSelected.emit(self._currentRole)


class CharactersProgressWidget(QWidget, Ui_CharactersProgressWidget, EventListener):
    characterClicked = pyqtSignal(Character)

    RowOverall: int = 1
    RowName: int = 3
    RowRole: int = 4
    RowGender: int = 5

    @dataclass
    class Header:
        header: TemplateField
        row: int
        max_value: int = 0

        def __hash__(self):
            return hash(str(self.header.id))

    def __init__(self, parent=None):
        super(CharactersProgressWidget, self).__init__(parent)
        self.setupUi(self)
        self._layout = QGridLayout()
        self.scrollAreaProgress.setLayout(self._layout)
        margins(self, 2, 2, 2, 2)
        self._layout.setSpacing(5)
        self._refreshNext: bool = False

        self.novel: Optional[Novel] = None

        self._chartMajor = CharacterRoleProgressChart(RoleImportance.MAJOR)
        self.chartViewMajor.setChart(self._chartMajor)
        self._chartSecondary = CharacterRoleProgressChart(RoleImportance.SECONDARY)
        self.chartViewSecondary.setChart(self._chartSecondary)
        self._chartMinor = CharacterRoleProgressChart(RoleImportance.MINOR)
        self.chartViewMinor.setChart(self._chartMinor)

        self._chartMajor.setBackgroundBrush(QColor(RELAXED_WHITE_COLOR))
        self._chartSecondary.setBackgroundBrush(QColor(RELAXED_WHITE_COLOR))
        self._chartMinor.setBackgroundBrush(QColor(RELAXED_WHITE_COLOR))

        self._chartMajor.refresh()
        self._chartSecondary.refresh()
        self._chartMinor.refresh()

        event_dispatcher.register(self, CharacterSummaryChangedEvent)

    def setNovel(self, novel: Novel):
        self.novel = novel

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, CharacterSummaryChangedEvent):
            self._refreshNext = True

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        if self._refreshNext:
            self._refreshNext = False
            self.refresh()

    def refresh(self):
        if not self.novel:
            return

        clear_layout(self._layout)
        for chart_ in [self._chartMajor, self._chartSecondary, self._chartMinor]:
            chart_.setValue(0)
            chart_.setMaxValue(0)

        for i, char in enumerate(self.novel.characters):
            btn = QToolButton(self)
            btn.setIconSize(QSize(45, 45))
            transparent(btn)
            btn.setIcon(avatars.avatar(char))
            btn.setToolTip(char.name)
            self._layout.addWidget(btn, 0, i + 1)
            pointy(btn)
            btn.installEventFilter(ButtonPressResizeEventFilter(btn))
            btn.installEventFilter(OpacityEventFilter(btn, 0.8, 1.0))
            btn.clicked.connect(partial(self.characterClicked.emit, char))
        self._layout.addWidget(spacer(), 0, self._layout.columnCount())

        self._addLabel(self.RowOverall, 'Overall', IconRegistry.progress_check_icon(), Qt.AlignmentFlag.AlignCenter)
        self._addLine(self.RowOverall + 1)
        self._addLabel(self.RowName, 'Name', IconRegistry.character_icon())
        self._addLabel(self.RowRole, 'Role', IconRegistry.major_character_icon())
        self._addLabel(self.RowGender, 'Gender', IconRegistry.male_gender_icon())
        self._addLine(self.RowGender + 1)

        fields = {}
        headers: Dict[CharactersProgressWidget.Header, int] = {}
        header: Optional[CharactersProgressWidget.Header] = None
        row = self.RowGender + 1
        for el in self.novel.character_profiles[0].elements:
            if el.field.type == TemplateFieldType.DISPLAY_HEADER:
                row += 1
                self._addLabel(row, el.field.name)
                header = self.Header(el.field, row)
                headers[header] = 0
            elif not el.field.type.name.startswith('DISPLAY') and header:
                fields[str(el.field.id)] = header
                header.max_value = header.max_value + 1

        row += 1
        self._addLine(row)
        row += 1
        for col, char in enumerate(self.novel.characters):
            self._updateForCharacter(char, fields, headers, row, col)

        self._addLabel(row, 'Backstory', IconRegistry.backstory_icon())
        self._addLabel(row + 1, 'Topics', IconRegistry.topics_icon())
        self._layout.addWidget(vspacer(), row + 2, 0)

        self._chartMajor.refresh()
        self._chartSecondary.refresh()
        self._chartMinor.refresh()

    def _updateForCharacter(self, char: Character, fields, headers, row: int, col: int):
        name_progress = CircularProgressBar(parent=self)
        if char.name:
            name_progress.setValue(1)
        self._addWidget(name_progress, self.RowName, col + 1)

        role_value = 0
        if char.role:
            role_value = 1
            self._addItem(char.role, self.RowRole, col + 1)
        else:
            self._addWidget(CircularProgressBar(parent=self), self.RowRole, col + 1)

        gender_value = 0
        if char.gender:
            gender_value = 1
            self._addIcon(IconRegistry.gender_icon(char.gender), self.RowGender, col + 1)
        else:
            self._addWidget(CircularProgressBar(parent=self), self.RowGender, col + 1)

        for h in headers.keys():
            headers[h] = 0  # reset char values
        for value in char.template_values:
            if str(value.id) not in fields.keys():
                continue
            header = fields[str(value.id)]
            if not header.header.required and char.is_minor():
                continue
            if not char.disabled_template_headers.get(str(header.header.id), header.header.enabled):
                continue
            if value.value or value.ignored:
                if isinstance(value.value, dict):
                    count = 0
                    values = 0
                    for _, attrs in value.value.items():
                        count += 1
                        if attrs.get('value'):
                            values += 1
                        for secondary in attrs.get('secondary', []):
                            count += 1
                            if secondary.get('value'):
                                values += 1

                    headers[header] = headers[header] + values / count
                else:
                    headers[header] = headers[header] + 1

        overall_progress = CircularProgressBar(maxValue=2, parent=self)
        overall_progress.setTooltipMode(ProgressTooltipMode.PERCENTAGE)
        overall_progress.setValue((name_progress.value() + gender_value) // 2 + role_value)

        for h, v in headers.items():
            if not h.header.required and char.is_minor():
                continue
            if not char.disabled_template_headers.get(str(h.header.id), h.header.enabled):
                continue
            value_progress = CircularProgressBar(v, h.max_value, parent=self)
            self._addWidget(value_progress, h.row, col + 1)
            overall_progress.addMaxValue(h.max_value)
            overall_progress.addValue(v)
        if not char.is_minor():
            backstory_progress = CircularProgressBar(parent=self)
            backstory_progress.setMaxValue(5 if char.is_major() else 3)
            backstory_progress.setValue(len(char.backstory))
            overall_progress.addMaxValue(backstory_progress.maxValue())
            overall_progress.addValue(backstory_progress.value())
            self._addWidget(backstory_progress, row, col + 1)

        if char.topics:
            topics_progress = CircularProgressBar(parent=self)
            topics_progress.setMaxValue(len(char.topics))
            topics_progress.setValue(len([x for x in char.topics if x.value]))
            overall_progress.addMaxValue(topics_progress.maxValue())
            overall_progress.addValue(topics_progress.value())
            self._addWidget(topics_progress, row + 1, col + 1)

        self._addWidget(overall_progress, self.RowOverall, col + 1)

        if char.is_major():
            self._chartMajor.setMaxValue(self._chartMajor.maxValue() + overall_progress.maxValue())
            self._chartMajor.setValue(self._chartMajor.value() + overall_progress.value())
        elif char.is_secondary():
            self._chartSecondary.setMaxValue(self._chartSecondary.maxValue() + overall_progress.maxValue())
            self._chartSecondary.setValue(self._chartSecondary.value() + overall_progress.value())
        elif char.is_minor():
            self._chartMinor.setMaxValue(self._chartMinor.maxValue() + overall_progress.maxValue())
            self._chartMinor.setValue(self._chartMinor.value() + overall_progress.value())

    def _addLine(self, row: int):
        self._layout.addWidget(line(), row, 0, 1, self._layout.columnCount() - 1)

    def _addLabel(self, row: int, text: str, icon=None, alignment=Qt.AlignmentFlag.AlignRight):
        if icon:
            wdg = IconText(self)
            wdg.setIcon(icon)
        else:
            wdg = QLabel(parent=self)
        wdg.setText(text)

        self._layout.addWidget(wdg, row, 0, alignment=alignment)

    def _addWidget(self, progress: QWidget, row: int, col: int):
        if row > self.RowOverall:
            progress.installEventFilter(OpacityEventFilter(parent=progress))
        self._layout.addWidget(progress, row, col, alignment=Qt.AlignmentFlag.AlignCenter)

    def _addIcon(self, icon: QIcon, row: int, col: int):
        _icon = Icon()
        _icon.setIcon(icon)
        self._addWidget(_icon, row, col)

    def _addItem(self, item: SelectionItem, row: int, col: int):
        icon = Icon()
        icon.iconName = item.icon
        icon.iconColor = item.icon_color
        icon.setToolTip(item.text)
        self._addWidget(icon, row, col)


default_topics: List[Topic] = [
    Topic('Family', uuid.UUID('2ce9c3b4-1dd9-4f88-a16e-b8dc507633b7'), 'mdi6.human-male-female-child', '#457b9d'),
    Topic('Job', uuid.UUID('19d9bfe9-5432-42d8-a444-0bd849720b2d'), 'fa5s.briefcase', '9c6644'),
    Topic('Education', uuid.UUID('01e9ef93-7a71-4b2d-af88-53b30d3947cb'), 'fa5s.graduation-cap'),
    Topic('Hometown', uuid.UUID('1ac1eec9-7953-419c-a265-88a0723a64ea'), 'ei.home-alt', '#4c334d'),
    Topic('Physical appearance', uuid.UUID('3c1a00d2-5085-47f0-8fe5-6d253e708999'), 'ri.body-scan-fill', ''),
    Topic('Scars, injuries', uuid.UUID('088ae5e0-99f8-4308-9d77-3daa624ca7a3'), 'mdi.bandage', ''),
    Topic('Clothing', uuid.UUID('4572a00f-9039-43a1-8eb9-8abd39fbec32'), 'fa5s.tshirt', ''),
    Topic('Accessories', uuid.UUID('eaab9129-576a-4042-9dfc-eedce3f6f3ab'), 'fa5s.glasses', ''),
    Topic('Health', uuid.UUID('ec218ea4-d8f9-4eb7-9850-1ce0e7eff5e6'), 'mdi.hospital-box', ''),
    Topic('Handwriting', uuid.UUID('65a43dc8-ee8d-4a4a-adb9-ee8a0e246e33'), 'mdi.signature-freehand', ''),
    Topic('Gait', uuid.UUID('26bdeb49-116a-470a-8427-2e5c061243a8'), 'mdi.motion-sensor', ''),

    Topic('Friends', uuid.UUID('d6d78fc4-d9d4-497b-8b61-cca465d5e8e7'), 'fa5s.user-friends', '#457b9d'),
    Topic('Relationships', uuid.UUID('62f5e2b6-ac35-4b6e-ae3b-bfd5b083b026'), 'ei.heart', '#e63946'),

    Topic('Faith', uuid.UUID('c4df6cdb-c92d-421b-8a2e-77598fc475a3'), 'fa5s.hands', ''),
    Topic('Spirituality', uuid.UUID('01f750eb-c6e1-4efb-b32c-76cb1d7a33f6'), 'mdi6.meditation', ''),

    Topic('Sport', uuid.UUID('d1e898d3-f9cc-4f65-8cfa-cc1a0c8cd8a2'), 'fa5.futbol', '#0096c7'),
    Topic('Fitness', uuid.UUID('0e3e6e19-b284-4f7d-85ef-ce2ba047743c'), 'mdi.dumbbell', ''),
    Topic('Hobby', uuid.UUID('97c66076-e97d-4f11-a20d-1ae6ff6ba246'), 'fa5s.book-reader', ''),
    Topic('Art', uuid.UUID('ed6749da-d1b0-49cd-becf-c7ddc67725d2'), 'ei.picture', ''),
]
default_topics.sort(key=lambda x: x.text)

topic_ids = {}
for topic in default_topics:
    topic_ids[str(topic.id)] = topic


class CharacterTopicSelector(MenuWidget):
    topicTriggered = pyqtSignal(Topic)

    def __init__(self, character: Character, parent=None):
        super(CharacterTopicSelector, self).__init__(parent)
        self._character = character
        self._actions: Dict[Topic, QAction] = {}
        char_topic_ids = set([str(x.id) for x in character.topics])

        for topic in default_topics:
            action_ = self._Action(topic, self)
            self._actions[topic] = action_
            action_.triggered.connect(partial(self.topicTriggered.emit, topic))
            if str(topic.id) in char_topic_ids:
                action_.setDisabled(True)
            self.addAction(action_)

        # self.addSeparator()
        # new_topic_action = action('New topic', IconRegistry.topics_icon(),
        #                           slot=self._newTopic, parent=menu)
        # self.addAction(new_topic_action)

    def updateTopic(self, topic: Topic, enabled: bool):
        self._actions[topic].setEnabled(enabled)

    class _Action(QAction):
        def __init__(self, topic: Topic, parent=None):
            super().__init__(parent)
            self.topic = topic
            if topic.icon:
                self.setIcon(IconRegistry.from_name(topic.icon, topic.icon_color))
            self.setText(topic.text)
            self.setToolTip(topic.description)


class CharacterTopicsEditor(QWidget, Ui_CharacterTopicEditor):
    def __init__(self, parent=None):
        super(CharacterTopicsEditor, self).__init__(parent)
        self._character: Optional[Character] = None
        self._menu: Optional[CharacterTopicSelector] = None
        self.setupUi(self)

        self.btnAdd.setIcon(IconRegistry.plus_icon('white'))
        self.btnAdd.setText('Add topic')

        self._wdgTopics = TopicsEditor(self)
        self.scrollAreaWidgetTopics.layout().addWidget(self._wdgTopics)
        self._wdgTopics.topicRemoved.connect(self._topicRemoved)

    def setCharacter(self, character: Character):
        self._character = character
        self._menu = CharacterTopicSelector(self._character, self.btnAdd)
        self._menu.topicTriggered.connect(self._addTopic)

        for tc in character.topics:
            topic = topic_ids.get(str(tc.id))
            if topic:
                self._wdgTopics.addTopic(topic, tc)

    def _addTopic(self, topic: Topic):
        if self._character is None:
            return
        value = TemplateValue(topic.id, '')
        self._character.topics.append(value)
        self._wdgTopics.addTopic(topic, value)

        self._menu.updateTopic(topic, False)

    def _topicRemoved(self, topic: Topic, value: TemplateValue):
        self._character.topics.remove(value)
        self._menu.updateTopic(topic, True)
