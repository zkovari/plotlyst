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
import pickle
from abc import abstractmethod
from functools import partial
from typing import List, Optional, Union, Dict

import qtanim
from PyQt5.QtCore import Qt, QObject, QEvent, QMimeData, QByteArray, QTimer, QSize, pyqtSignal
from PyQt5.QtGui import QDrag, QMouseEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent, QDragLeaveEvent, \
    QResizeEvent, QCursor
from PyQt5.QtWidgets import QSizePolicy, QWidget, QListView, QFrame, QToolButton, QHBoxLayout, QSplitter, \
    QPushButton
from overrides import overrides
from qtanim import fade_out
from qthandy import decr_font, ask_confirmation, gc, transparent, retain_when_hidden, opaque, underline, flow, \
    clear_layout, hbox, spacer
from qthandy.filter import InstantTooltipEventFilter

from src.main.python.plotlyst.common import ACT_ONE_COLOR, ACT_THREE_COLOR, ACT_TWO_COLOR
from src.main.python.plotlyst.core.domain import Scene, SelectionItem, Novel, SceneType, \
    SceneStructureItemType, SceneStructureAgenda, SceneStructureItem, SceneOutcome, NEUTRAL, StoryBeat, Conflict, \
    Character
from src.main.python.plotlyst.event.core import emit_critical
from src.main.python.plotlyst.model.common import SelectionItemsModel
from src.main.python.plotlyst.model.novel import NovelPlotsModel, NovelTagsModel
from src.main.python.plotlyst.view.common import OpacityEventFilter, DisabledClickEventFilter, PopupMenuBuilder
from src.main.python.plotlyst.view.generated.scene_beat_item_widget_ui import Ui_SceneBeatItemWidget
from src.main.python.plotlyst.view.generated.scene_filter_widget_ui import Ui_SceneFilterWidget
from src.main.python.plotlyst.view.generated.scene_ouctome_selector_ui import Ui_SceneOutcomeSelectorWidget
from src.main.python.plotlyst.view.generated.scene_structure_editor_widget_ui import Ui_SceneStructureWidget
from src.main.python.plotlyst.view.generated.scenes_view_preferences_widget_ui import Ui_ScenesViewPreferences
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterConflictSelector
from src.main.python.plotlyst.view.widget.input import RotatedButtonOrientation
from src.main.python.plotlyst.view.widget.labels import LabelsEditorWidget
from src.main.python.plotlyst.worker.cache import acts_registry


# class SceneGoalsWidget(LabelsEditorWidget):
#
#     def __init__(self, novel: Novel, agenda: SceneStructureAgenda, parent=None):
#         self.novel = novel
#         self.agenda = agenda
#         super(SceneGoalsWidget, self).__init__(parent=parent)
#         self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
#         self.setValue([x.text for x in self.agenda.goals(self.novel)])
#         self.btnEdit.setIcon(IconRegistry.goal_icon())
#         self.btnEdit.setText('Track goals')
#         self._wdgLabels.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
#         self.setStyleSheet('SceneGoalsWidget {border: 0px;}')
#
#     @overrides
#     def _initModel(self) -> SelectionItemsModel:
#         model = SceneGoalsModel(self.novel, self.scene_structure_item)
#         model.setCheckable(True, SceneGoalsModel.ColName)
#         return model
#
#     @overrides
#     def items(self) -> List[SelectionItem]:
#         return self.novel.scene_goals
#
#     @overrides
#     def _addItems(self, items: Set[SceneGoal]):
#         pass
# for item in items:
#     self._wdgLabels.addLabel(GoalLabel(item))
# self.agenda.goal_ids.clear()
# self.agenda.goal_ids.extend(items)


class SceneOutcomeSelector(QWidget, Ui_SceneOutcomeSelectorWidget):
    def __init__(self, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneOutcomeSelector, self).__init__(parent)
        self.scene_structure_item = scene_structure_item
        self.setupUi(self)
        self.btnDisaster.setIcon(IconRegistry.disaster_icon(color='grey'))
        self.btnResolution.setIcon(IconRegistry.success_icon(color='grey'))
        self.btnTradeOff.setIcon(IconRegistry.tradeoff_icon(color='grey'))

        if self.scene_structure_item.outcome == SceneOutcome.DISASTER:
            self.btnDisaster.setChecked(True)
        elif self.scene_structure_item.outcome == SceneOutcome.RESOLUTION:
            self.btnResolution.setChecked(True)
        elif self.scene_structure_item.outcome == SceneOutcome.TRADE_OFF:
            self.btnTradeOff.setChecked(True)

        self.btnGroupOutcome.buttonClicked.connect(self._clicked)

    def _clicked(self):
        if self.btnDisaster.isChecked():
            self.scene_structure_item.outcome = SceneOutcome.DISASTER
        elif self.btnResolution.isChecked():
            self.scene_structure_item.outcome = SceneOutcome.RESOLUTION
        elif self.btnTradeOff.isChecked():
            self.scene_structure_item.outcome = SceneOutcome.TRADE_OFF


class _SceneLabelsEditor(LabelsEditorWidget):

    def __init__(self, novel: Novel, parent=None):
        self.novel = novel
        super().__init__(parent=parent)

    @overrides
    def _initPopupWidget(self) -> QWidget:
        _view = QListView()
        _view.setModel(self._model)
        _view.setModelColumn(SelectionItemsModel.ColName)
        return _view

    @abstractmethod
    def _initModel(self) -> SelectionItemsModel:
        pass

    @abstractmethod
    def items(self) -> List[SelectionItem]:
        pass


class SceneDramaticQuestionsWidget(_SceneLabelsEditor):

    @overrides
    def _initModel(self) -> SelectionItemsModel:
        model = NovelPlotsModel(self.novel)
        model.setEditable(False)
        return model

    @overrides
    def items(self) -> List[SelectionItem]:
        return self.novel.plots


class SceneTagsWidget(_SceneLabelsEditor):

    def __init__(self, novel: Novel, parent=None):
        super(SceneTagsWidget, self).__init__(novel, parent)
        self.btnEdit.setIcon(IconRegistry.tag_plus_icon())

    @overrides
    def _initModel(self) -> SelectionItemsModel:
        model = NovelTagsModel(self.novel)
        model.setEditable(False)
        return model

    @overrides
    def items(self) -> List[SelectionItem]:
        return self.novel.tags


class SceneFilterWidget(QFrame, Ui_SceneFilterWidget):
    def __init__(self, novel: Novel, parent=None):
        super(SceneFilterWidget, self).__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.povFilter.setExclusive(False)
        self.povFilter.setCharacters(self.novel.pov_characters())

        self.tabWidget.setTabIcon(self.tabWidget.indexOf(self.tabPov), IconRegistry.character_icon())


class _PlaceHolder(QFrame):
    def __init__(self):
        super(_PlaceHolder, self).__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(3)
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Box)

        self.setStyle()

    def setStyle(self, dropMode: bool = False) -> None:
        if dropMode:
            self.setLineWidth(2)
        else:
            self.setLineWidth(0)

    @overrides
    def parent(self) -> QWidget:
        return super(_PlaceHolder, self).parent()

    @overrides
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        self.setStyle(True)

    @overrides
    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.setStyle()


def is_placeholder(widget: QWidget) -> bool:
    return isinstance(widget, _PlaceHolder)


class SceneStructureItemWidget(QWidget, Ui_SceneBeatItemWidget):

    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem,
                 placeholder: str = 'General beat in this scene',
                 topVisible: bool = False, parent=None):
        super(SceneStructureItemWidget, self).__init__(parent)
        self.novel = novel
        self.scene_structure_item = scene_structure_item
        self.setupUi(self)

        self.text.setPlaceholderText(placeholder)
        self.text.setMaximumHeight(20)
        self.text.setText(self.scene_structure_item.text)
        self.btnPlaceholder.setVisible(topVisible)
        self.btnIcon.setIcon(IconRegistry.circle_icon())
        self.btnDelete.setIcon(IconRegistry.wrong_icon(color='black'))
        self.btnDelete.clicked.connect(self._remove)
        retain_when_hidden(self.btnDelete)
        self.btnDelete.installEventFilter(OpacityEventFilter(parent=self.btnDelete))
        self.btnDelete.setHidden(True)

    def sceneStructureItem(self) -> SceneStructureItem:
        self.scene_structure_item.text = self.text.toPlainText()
        return self.scene_structure_item

    def activate(self):
        self.text.setFocus()

    @overrides
    def enterEvent(self, event: QEvent) -> None:
        self.btnDelete.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        self.btnDelete.setHidden(True)

    def _remove(self):
        if self.parent():
            anim = fade_out(self, duration=150)
            anim.finished.connect(self.__destroy)

    def __destroy(self):
        self.parent().layout().removeWidget(self)
        gc(self)


class SceneGoalItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneGoalItemWidget, self).__init__(novel, scene_structure_item,
                                                  placeholder='Goal of the character is clearly stated to the reader',
                                                  parent=parent)
        self.btnIcon.setIcon(IconRegistry.goal_icon())


class SceneConflictItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneConflictItemWidget, self).__init__(novel, scene_structure_item,
                                                      placeholder="Conflict arises that hinders the character's goals",
                                                      parent=parent)
        self.btnIcon.setIcon(IconRegistry.conflict_icon())


class SceneOutcomeItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneOutcomeItemWidget, self).__init__(novel, scene_structure_item, topVisible=True, parent=parent)

        self.layoutTop.addWidget(SceneOutcomeSelector(self.scene_structure_item))
        self.layoutTop.addWidget(spacer())
        self.text.setPlaceholderText(
            "Outcome of the scene, typically ending with disaster")
        self.btnIcon.setIcon(IconRegistry.action_scene_icon())


class ReactionSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(ReactionSceneItemWidget, self).__init__(novel, scene_structure_item,
                                                      placeholder='Initial reaction to a previous conflict',
                                                      parent=parent)
        self.btnIcon.setIcon(IconRegistry.reaction_icon())


class DilemmaSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super().__init__(novel, scene_structure_item,
                         placeholder='Dilemma throughout the scene. What to do next?',
                         parent=parent)
        self.btnIcon.setIcon(IconRegistry.dilemma_icon())


class DecisionSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super().__init__(novel, scene_structure_item,
                         placeholder='The character comes up with a new goal and might act right away',
                         parent=parent)
        self.btnIcon.setIcon(IconRegistry.decision_icon())


class HookSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super().__init__(novel, scene_structure_item, placeholder='Initial hook of the scene', parent=parent)
        self.btnIcon.setIcon(IconRegistry.hook_icon())


class IncitingIncidentSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super().__init__(novel, scene_structure_item,
                         placeholder='Is there a surprising, unforeseen incident in this scene?',
                         parent=parent)
        self.btnIcon.setIcon(IconRegistry.inciting_incident_icon())


class RisingActionSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super().__init__(novel, scene_structure_item, placeholder='Increasing tension or suspense throughout the scene',
                         parent=parent)
        self.btnIcon.setIcon(IconRegistry.rising_action_icon())


class CrisisSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super().__init__(novel, scene_structure_item,
                         placeholder='The impossible decision between two equally good or bad outcomes', parent=parent)
        self.btnIcon.setIcon(IconRegistry.crisis_icon())


class TickingClockSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super().__init__(novel, scene_structure_item, placeholder='Ticking clock is activated to increase tension',
                         parent=parent)
        self.btnIcon.setIcon(IconRegistry.ticking_clock_icon())


class ExpositionSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super().__init__(novel, scene_structure_item,
                         placeholder='Exposition beat with character or imaginary exposition',
                         parent=parent)
        self.btnIcon.setIcon(IconRegistry.exposition_icon())


class _SceneTypeButton(QPushButton):
    def __init__(self, type: SceneType, parent=None):
        super(_SceneTypeButton, self).__init__(parent)
        self.type = type
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        if type == SceneType.ACTION:
            bgColor = '#eae4e9'
            borderColor = '#f94144'
            bgColorChecked = '#f4978e'
            borderColorChecked = '#fb5607'
            self.setText('Scene (action)')
            self.setIcon(IconRegistry.action_scene_icon())
        else:
            bgColor = '#bee1e6'
            borderColor = '#168aad'
            bgColorChecked = '#89c2d9'
            borderColorChecked = '#1a759f'
            self.setText('Sequel (reaction)')
            self.setIcon(IconRegistry.reaction_scene_icon())

        self.setStyleSheet(f'''
            QPushButton {{
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 0,
                                      stop: 0 {bgColor};);
                border: 2px dashed {borderColor};
                border-radius: 8px;
                padding: 2px;
            }}
            QPushButton:checked {{
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 0,
                                      stop: 0 {bgColorChecked});
                border: 3px solid {borderColorChecked};
                padding: 1px;
            }}
            ''')
        self._toggled(self.isChecked())
        self.installEventFilter(OpacityEventFilter(0.7, 0.5, self, ignoreCheckedButton=True))
        self.toggled.connect(self._toggled)

    def _toggled(self, toggled: bool):
        opaque(self, 1.0 if toggled else 0.5)
        font = self.font()
        font.setBold(toggled)
        self.setFont(font)


class SceneStructureWidget(QWidget, Ui_SceneStructureWidget):
    MimeType: str = 'application/structure-item'

    def __init__(self, parent=None):
        super(SceneStructureWidget, self).__init__(parent)
        self.setupUi(self)
        self._dragged: Optional[QToolButton] = None
        self._target_to_drop: Optional[Union[_PlaceHolder, QWidget]] = None

        self.btnEmotionRangeDisplay.setOrientation(RotatedButtonOrientation.VerticalBottomToTop)

        self.novel: Optional[Novel] = None
        self.scene: Optional[Scene] = None

        self.btnInventory.setIcon(IconRegistry.from_name('mdi.file-tree-outline'))
        decr_font(self.lblBeatsInventory)
        underline(self.lblBeatsInventory)

        self.btnScene = _SceneTypeButton(SceneType.ACTION)
        self.btnSequel = _SceneTypeButton(SceneType.REACTION)

        self.wdgTypes.layout().addWidget(self.btnScene)
        self.wdgTypes.layout().addWidget(self.btnSequel)

        flow(self.wdgGoalConflictContainer)

        self.btnBeginningIcon.setIcon(IconRegistry.cause_icon())
        self.btnMiddleIcon.setIcon(IconRegistry.from_name('mdi.ray-vertex'))
        self.btnEndIcon.setIcon(IconRegistry.from_name('mdi.ray-end'))

        self.btnGoal.setIcon(IconRegistry.goal_icon())
        self.btnConflict.setIcon(IconRegistry.conflict_icon())
        self.btnOutcome.setIcon(IconRegistry.disaster_icon())

        self.btnReaction.setIcon(IconRegistry.reaction_icon())
        self.btnDilemma.setIcon(IconRegistry.dilemma_icon())
        self.btnDecision.setIcon(IconRegistry.decision_icon())

        self.btnHook.setIcon(IconRegistry.hook_icon())
        self.btnIncitingIncident.setIcon(IconRegistry.inciting_incident_icon())
        self.btnRisingAction.setIcon(IconRegistry.rising_action_icon())
        self.btnCrisis.setIcon(IconRegistry.crisis_icon())
        self.btnTickingClock.setIcon(IconRegistry.ticking_clock_icon())

        self.btnExposition.setIcon(IconRegistry.exposition_icon())
        self.btnBeat.setIcon(IconRegistry.circle_icon())

        self._addPlaceholder(self.wdgBeginning)
        self._addPlaceholder(self.wdgMiddle)
        self._addPlaceholder(self.wdgEnd)

        self.btnGoal.installEventFilter(self)
        self.btnConflict.installEventFilter(self)
        self.btnOutcome.installEventFilter(self)
        self.btnReaction.installEventFilter(self)
        self.btnDilemma.installEventFilter(self)
        self.btnDecision.installEventFilter(self)
        self.btnHook.installEventFilter(self)
        self.btnIncitingIncident.installEventFilter(self)
        self.btnRisingAction.installEventFilter(self)
        self.btnCrisis.installEventFilter(self)
        self.btnTickingClock.installEventFilter(self)
        self.btnExposition.installEventFilter(self)
        self.btnBeat.installEventFilter(self)

        self.btnScene.installEventFilter(OpacityEventFilter(parent=self.btnScene, ignoreCheckedButton=True))
        self.btnSequel.installEventFilter(OpacityEventFilter(parent=self.btnSequel, ignoreCheckedButton=True))

        self.btnScene.clicked.connect(partial(self._typeClicked, SceneType.ACTION))
        self.btnSequel.clicked.connect(partial(self._typeClicked, SceneType.REACTION))

        self.wdgAgendaCharacter.characterSelected.connect(self._agendaCharacterSelected)
        self.unsetCharacterSlot = None

    def setUnsetCharacterSlot(self, unsetCharacterSlot):
        self.unsetCharacterSlot = unsetCharacterSlot

    def setScene(self, novel: Novel, scene: Scene):
        self.novel = novel
        self.scene = scene

        self.updateAvailableAgendaCharacters()
        self._toggleCharacterStatus()

        self.reset()
        self.btnInventory.setChecked(False)

        self._checkSceneType()

        if scene.agendas and scene.agendas[0].items:
            widgets_per_parts = {1: self.wdgBeginning, 2: self.wdgMiddle, 3: self.wdgEnd}

            for item in scene.agendas[0].items:
                if item.type == SceneStructureItemType.GOAL:
                    widget = SceneGoalItemWidget(self.novel, item)
                    # self.btnGoal.setDisabled(True)
                elif item.type == SceneStructureItemType.CONFLICT:
                    widget = SceneConflictItemWidget(self.novel, item)
                    # self.btnConflict.setDisabled(True)
                elif item.type == SceneStructureItemType.OUTCOME:
                    widget = SceneOutcomeItemWidget(self.novel, item)
                    # self.btnOutcome.setDisabled(True)
                elif item.type == SceneStructureItemType.REACTION:
                    widget = ReactionSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.DILEMMA:
                    widget = DilemmaSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.DECISION:
                    widget = DecisionSceneItemWidget(self.novel, item)
                    # self.btnDecision.setDisabled(True)
                elif item.type == SceneStructureItemType.HOOK:
                    widget = HookSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.INCITING_INCIDENT:
                    widget = IncitingIncidentSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.RISING_ACTION:
                    widget = RisingActionSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.CRISIS:
                    widget = CrisisSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.TICKING_CLOCK:
                    widget = TickingClockSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.EXPOSITION:
                    widget = ExpositionSceneItemWidget(self.novel, item)
                else:
                    widget = SceneStructureItemWidget(self.novel, item)

                widgets_per_parts.get(item.part, self.wdgEnd).layout().addWidget(widget)
                self._addPlaceholder(widgets_per_parts[item.part])

            for part in widgets_per_parts.values():
                self._addPlaceholder(part, 0)

            self.btnEmotionStart.setValue(scene.agendas[0].beginning_emotion)
            self.btnEmotionEnd.setValue(scene.agendas[0].ending_emotion)
        else:
            self.btnEmotionStart.setValue(NEUTRAL)
            self.btnEmotionEnd.setValue(NEUTRAL)

        self._setEmotionColorChange()
        self.btnEmotionStart.emotionChanged.connect(self._setEmotionColorChange)
        self.btnEmotionEnd.emotionChanged.connect(self._setEmotionColorChange)

        if not self.wdgBeginning.layout().count():
            self._addPlaceholder(self.wdgBeginning)
        if not self.wdgMiddle.layout().count():
            self._addPlaceholder(self.wdgMiddle)
        if not self.wdgEnd.layout().count():
            self._addPlaceholder(self.wdgEnd)

        if not self.scene.agendas[0].items:
            self._typeClicked(SceneType.DEFAULT, True, lazy=False)

    def updateAvailableAgendaCharacters(self):
        chars = []
        chars.extend(self.scene.characters)
        if self.scene.pov:
            chars.insert(0, self.scene.pov)
        self.wdgAgendaCharacter.setAvailableCharacters(chars)

    def updateAgendaCharacter(self):
        self._toggleCharacterStatus()
        self.reset(clearBeats=False)

    def reset(self, clearBeats: bool = True, addPlaceholders: bool = False):
        if clearBeats:
            for widget in [self.wdgBeginning, self.wdgMiddle, self.wdgEnd]:
                clear_layout(widget)
        if clearBeats and addPlaceholders:
            self._addPlaceholder(self.wdgBeginning)
            self._addPlaceholder(self.wdgMiddle)
            self._addPlaceholder(self.wdgEnd)

        clear_layout(self.wdgGoalConflictContainer)
        if self.scene.agendas and self.scene.agendas[0].conflict_references:
            for conflict in self.scene.agendas[0].conflicts(self.novel):
                self._addConfictSelector(simplified=False, conflict=conflict)
            self._addConfictSelector()
        else:
            self._addConfictSelector(simplified=False)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        self._dragged = watched
        if event.type() == QEvent.MouseButtonPress:
            self.mousePressEvent(event)
        elif event.type() == QEvent.MouseMove:
            self.mouseMoveEvent(event)
        elif event.type() == QEvent.MouseButtonRelease:
            self.mouseReleaseEvent(event)
        elif event.type() == QEvent.DragEnter:
            self._target_to_drop = watched
            self.dragMoveEvent(event)
        elif event.type() == QEvent.Drop:
            self.dropEvent(event)
            self._target_to_drop = None
        return super().eventFilter(watched, event)

    @overrides
    def mousePressEvent(self, event: QMouseEvent):
        self._dragged = None

    @overrides
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton and self._dragged and self._dragged.isEnabled():
            drag = QDrag(self._dragged)
            pix = self._dragged.grab()
            mimedata = QMimeData()
            mimedata.setData(self.MimeType, QByteArray(pickle.dumps(self._buttonType(self._dragged))))
            drag.setMimeData(mimedata)
            drag.setPixmap(pix)
            drag.setHotSpot(event.pos())
            drag.destroyed.connect(self._dragDestroyed)
            drag.exec_()

    def updateAgendas(self):
        if not self.scene.agendas:
            return
        self.scene.agendas[0].items.clear()
        self._collect_agenda_items(self.scene.agendas[0], self.wdgBeginning, 1)
        self._collect_agenda_items(self.scene.agendas[0], self.wdgMiddle, 2)
        self._collect_agenda_items(self.scene.agendas[0], self.wdgEnd, 3)
        self.scene.agendas[0].beginning_emotion = self.btnEmotionStart.value()
        self.scene.agendas[0].ending_emotion = self.btnEmotionEnd.value()

    @overrides
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat(self.MimeType):
            event.accept()
        else:
            event.ignore()

    @overrides
    def dragMoveEvent(self, event: QDragMoveEvent):
        if not self._target_to_drop:
            event.ignore()
            return
        if is_placeholder(self._target_to_drop):
            event.accept()
        else:
            event.ignore()

    @overrides
    def dropEvent(self, event: QDropEvent):
        if not self._target_to_drop:
            event.ignore()
            return

        if is_placeholder(self._target_to_drop):
            placeholder: _PlaceHolder = self._target_to_drop
        else:
            event.ignore()
            return
        data: SceneStructureItemType = pickle.loads(event.mimeData().data(self.MimeType))

        if data == SceneStructureItemType.GOAL:
            widget = SceneGoalItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.CONFLICT:
            widget = SceneConflictItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.OUTCOME:
            widget = SceneOutcomeItemWidget(self.novel, SceneStructureItem(data, outcome=SceneOutcome.DISASTER))
        elif data == SceneStructureItemType.REACTION:
            widget = ReactionSceneItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.DILEMMA:
            widget = DilemmaSceneItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.DECISION:
            widget = DecisionSceneItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.BEAT:
            widget = SceneStructureItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.HOOK:
            widget = HookSceneItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.INCITING_INCIDENT:
            widget = IncitingIncidentSceneItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.RISING_ACTION:
            widget = RisingActionSceneItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.CRISIS:
            widget = CrisisSceneItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.TICKING_CLOCK:
            widget = TickingClockSceneItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.EXPOSITION:
            widget = ExpositionSceneItemWidget(self.novel, SceneStructureItem(data))
        else:
            widget = SceneStructureItemWidget(self.novel, SceneStructureItem(data))

        self._addWidget(placeholder, widget)

        event.accept()

        QTimer.singleShot(50, widget.activate)

    def _toggleCharacterStatus(self):
        if self.scene.agendas[0].character_id:
            self.btnEmotionStart.setEnabled(True)
            self.btnEmotionEnd.setEnabled(True)
            self.wdgAgendaCharacter.setEnabled(True)
            self.btnEmotionStart.setToolTip('')
            self.btnEmotionEnd.setToolTip('')
            self.wdgAgendaCharacter.setCharacter(self.scene.agendas[0].character(self.novel))
        else:
            self.btnEmotionStart.installEventFilter(DisabledClickEventFilter(self.unsetCharacterSlot, self))
            self.btnEmotionEnd.installEventFilter(DisabledClickEventFilter(self.unsetCharacterSlot, self))
            self.wdgAgendaCharacter.btnLinkCharacter.installEventFilter(
                DisabledClickEventFilter(self.unsetCharacterSlot, self))

            self.btnEmotionStart.setDisabled(True)
            self.btnEmotionEnd.setDisabled(True)
            self.wdgAgendaCharacter.setDisabled(True)
            self.wdgAgendaCharacter.setToolTip('Select POV character first')
            self.btnEmotionStart.setToolTip('Select POV character first')
            self.btnEmotionEnd.setToolTip('Select POV character first')

    def _agendaCharacterSelected(self, character: Character):
        self.scene.agendas[0].set_character(character)
        self.scene.agendas[0].conflict_references.clear()
        self.updateAgendaCharacter()

    def _collect_agenda_items(self, agenda: SceneStructureAgenda, widget: QWidget, part: int):
        for i in range(widget.layout().count()):
            item = widget.layout().itemAt(i)
            if isinstance(item.widget(), SceneStructureItemWidget):
                structure_item: SceneStructureItem = item.widget().sceneStructureItem()
                structure_item.part = part
                agenda.items.append(structure_item)

    def _checkSceneType(self):
        if self.scene.type == SceneType.ACTION:
            self.btnScene.setChecked(True)
            self.btnScene.setVisible(True)
            self.btnSequel.setChecked(False)
            self.btnSequel.setHidden(True)
        elif self.scene.type == SceneType.REACTION:
            self.btnSequel.setChecked(True)
            self.btnSequel.setVisible(True)
            self.btnScene.setChecked(False)
            self.btnScene.setHidden(True)
        else:
            self.btnScene.setChecked(False)
            self.btnScene.setVisible(True)
            self.btnSequel.setChecked(False)
            self.btnSequel.setVisible(True)
            self.btnInventory.setChecked(True)

    def _setEmotionColorChange(self):
        color_start = self.btnEmotionStart.color()
        color_end = self.btnEmotionEnd.color()
        self.btnEmotionRangeDisplay.setStyleSheet(f'''
           background-color: qlineargradient(x1: 1, y1: 0, x2: 0, y2: 0,
                                         stop: 0 {color_start}, stop: 1 {color_end});
           color: white;
           ''')

    def _buttonType(self, dragged: QToolButton) -> SceneStructureItemType:
        if dragged is self.btnGoal:
            return SceneStructureItemType.GOAL
        if dragged is self.btnConflict:
            return SceneStructureItemType.CONFLICT
        if dragged is self.btnOutcome:
            return SceneStructureItemType.OUTCOME
        if dragged is self.btnReaction:
            return SceneStructureItemType.REACTION
        if dragged is self.btnDilemma:
            return SceneStructureItemType.DILEMMA
        if dragged is self.btnDecision:
            return SceneStructureItemType.DECISION
        if dragged is self.btnHook:
            return SceneStructureItemType.HOOK
        if dragged is self.btnIncitingIncident:
            return SceneStructureItemType.INCITING_INCIDENT
        if dragged is self.btnRisingAction:
            return SceneStructureItemType.RISING_ACTION
        if dragged is self.btnCrisis:
            return SceneStructureItemType.CRISIS
        if dragged is self.btnTickingClock:
            return SceneStructureItemType.TICKING_CLOCK
        if dragged is self.btnExposition:
            return SceneStructureItemType.EXPOSITION
        if dragged is self.btnBeat:
            return SceneStructureItemType.BEAT

    def _addWidget(self, placeholder: _PlaceHolder, widget: SceneStructureItemWidget):
        parent = placeholder.parent()
        layout: QHBoxLayout = parent.layout()
        index = layout.indexOf(placeholder)
        layout.takeAt(index)
        placeholder.deleteLater()
        layout.insertWidget(index, widget)

        _placeholder = _PlaceHolder()
        layout.insertWidget(index + 1, _placeholder)
        _placeholder.installEventFilter(self)

    def _addPlaceholder(self, widget: QWidget, pos: int = -1):
        _placeholder = _PlaceHolder()
        if pos >= 0:
            widget.layout().insertWidget(pos, _placeholder)
        else:
            widget.layout().addWidget(_placeholder)
        _placeholder.installEventFilter(self)

    def _typeClicked(self, type: SceneType, checked: bool, lazy: bool = True):
        if lazy and type == self.scene.type and checked:
            return

        for item in self.scene.agendas[0].items:
            if item.text or self.scene.agendas[0].goals(self.novel) or self.scene.agendas[0].conflicts(self.novel):
                if not ask_confirmation(
                        "Some beats are filled up. Are you sure you want to change the scene's structure?"):
                    self._checkSceneType()  # revert
                    return
                break

        if type == SceneType.ACTION and checked:
            self.scene.type = type
            top = SceneGoalItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.GOAL))
            middle = SceneConflictItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.CONFLICT))
            bottom = SceneOutcomeItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.OUTCOME,
                                                                           outcome=SceneOutcome.DISASTER))
            self.btnSequel.setChecked(False)
            qtanim.fade_out(self.btnSequel)
        elif type == SceneType.REACTION and checked:
            self.scene.type = type
            top = ReactionSceneItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.REACTION))
            middle = DilemmaSceneItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.DILEMMA))
            bottom = DecisionSceneItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.DECISION))
            self.btnScene.setChecked(False)
            qtanim.fade_out(self.btnScene)
        else:
            self.scene.type = SceneType.DEFAULT
            top = SceneStructureItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.BEAT),
                                           placeholder='Describe the beginning event')
            middle = SceneStructureItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.BEAT),
                                              placeholder='Describe the middle part of this scene')
            bottom = SceneStructureItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.BEAT),
                                              placeholder='Describe the ending of this scene')
            self.btnInventory.setChecked(True)
            if self.btnScene.isHidden():
                qtanim.fade_in(self.btnScene)
            if self.btnSequel.isHidden():
                qtanim.fade_in(self.btnSequel)

        self.reset(addPlaceholders=True)
        self._addWidget(self.wdgBeginning.layout().itemAt(0).widget(), top)
        self._addWidget(self.wdgMiddle.layout().itemAt(0).widget(), middle)
        self._addWidget(self.wdgEnd.layout().itemAt(0).widget(), bottom)

    def _dragDestroyed(self):
        self._dragged = None

    def _addConfictSelector(self, simplified: bool = True, conflict: Optional[Conflict] = None):
        conflict_selector = CharacterConflictSelector(self.novel, self.scene, simplified=simplified,
                                                      parent=self.wdgGoalConflictContainer)
        if conflict:
            conflict_selector.setConflict(conflict)
        self.wdgGoalConflictContainer.layout().addWidget(conflict_selector)
        conflict_selector.conflictSelected.connect(self._addConfictSelector)


class SceneStoryStructureWidget(QWidget):
    beatSelected = pyqtSignal(StoryBeat)
    beatRemovalRequested = pyqtSignal(StoryBeat)

    def __init__(self, parent=None):
        super(SceneStoryStructureWidget, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self._checkOccupiedBeats: bool = True
        self._beatsCheckable: bool = False
        self._removalContextMenuEnabled: bool = False
        self._beatCursor = Qt.PointingHandCursor
        self.novel: Optional[Novel] = None
        self._acts: List[QPushButton] = []
        self._beats: Dict[StoryBeat, QToolButton] = {}
        self.btnCurrentScene = QToolButton(self)
        self._currentScenePercentage = 1
        self.btnCurrentScene.setIcon(IconRegistry.circle_icon(color='red'))
        self.btnCurrentScene.setHidden(True)
        transparent(self.btnCurrentScene)
        self._wdgLine = QWidget(self)
        hbox(self._wdgLine, 0, 0)
        self._lineHeight: int = 22
        self._beatHeight: int = 20
        self._margin = 5

    def checkOccupiedBeats(self) -> bool:
        return self._checkOccupiedBeats

    def setCheckOccupiedBeats(self, value: bool):
        self._checkOccupiedBeats = value

    def beatsCheckable(self) -> bool:
        return self._beatsCheckable

    def setBeatsCheckable(self, value: bool):
        self._beatsCheckable = value

    def setRemovalContextMenuEnabled(self, value: bool):
        self._removalContextMenuEnabled = value

    def beatCursor(self) -> int:
        return self._beatCursor

    def setBeatCursor(self, value: int):
        self._beatCursor = value

    def setNovel(self, novel: Novel):
        self.novel = novel
        self._acts.clear()
        self._beats.clear()

        occupied_beats = acts_registry.occupied_beats()
        for beat in self.novel.active_story_structure.beats:
            btn = QToolButton(self)
            if beat.icon:
                btn.setIcon(IconRegistry.from_name(beat.icon, beat.icon_color))
            btn.setStyleSheet('QToolButton {background-color: rgba(0,0,0,0); border:0px;} QToolTip {border: 0px;}')
            btn.setToolTip(f'<b style="color: {beat.icon_color}">{beat.text}')
            btn.installEventFilter(InstantTooltipEventFilter(btn))
            btn.toggled.connect(partial(self._beatToggled, btn))
            btn.clicked.connect(partial(self._beatClicked, beat, btn))
            btn.installEventFilter(self)
            btn.setCursor(self._beatCursor)
            if self._checkOccupiedBeats and beat not in occupied_beats:
                if self._beatsCheckable:
                    btn.setCheckable(True)
                self._beatToggled(btn, False)
            self._beats[beat] = btn
            if not beat.enabled:
                btn.setHidden(True)

        splitter = QSplitter(self._wdgLine)
        splitter.setContentsMargins(0, 0, 0, 0)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)
        self._wdgLine.layout().addWidget(splitter)

        act = self._actButton('Act 1', ACT_ONE_COLOR, left=True)
        self._acts.append(act)
        self._wdgLine.layout().addWidget(act)
        splitter.addWidget(act)
        act = self._actButton('Act 2', ACT_TWO_COLOR)
        self._acts.append(act)
        splitter.addWidget(act)

        act = self._actButton('Act 3', ACT_THREE_COLOR, right=True)
        self._acts.append(act)
        splitter.addWidget(act)

        beats = self.novel.active_story_structure.act_beats()
        if not len(beats) == 2:
            return emit_critical('Only 3 acts are supported at the moment for story structure widget')

        splitter.setSizes([10 * beats[0].percentage,
                           10 * (beats[1].percentage - beats[0].percentage),
                           10 * (100 - beats[1].percentage)])
        splitter.setDisabled(True)
        self.update()

    @overrides
    def minimumSizeHint(self) -> QSize:
        return QSize(300, self._lineHeight + self._beatHeight + 8)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QToolButton) and watched.isCheckable() and not watched.isChecked():
            if event.type() == QEvent.Enter:
                opaque(watched, 0.5)
            elif event.type() == QEvent.Leave:
                opaque(watched, 0.2)
        return super(SceneStoryStructureWidget, self).eventFilter(watched, event)

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        for beat, btn in self._beats.items():
            btn.setGeometry(self.width() * beat.percentage / 100 - self._lineHeight // 2, self._lineHeight,
                            self._beatHeight,
                            self._beatHeight)
        self._wdgLine.setGeometry(0, 0, self.width(), self._lineHeight)
        if self.btnCurrentScene:
            self.btnCurrentScene.setGeometry(self.width() * self._currentScenePercentage / 100 - self._lineHeight // 2,
                                             self._lineHeight,
                                             self._beatHeight,
                                             self._beatHeight)

    def uncheckActs(self):
        for act in self._acts:
            act.setChecked(False)

    def setActChecked(self, act: int, checked: bool = True):
        self._acts[act - 1].setChecked(checked)

    def setActsClickable(self, clickable: bool):
        for act in self._acts:
            act.setEnabled(clickable)

    def highlightBeat(self, beat: StoryBeat):
        self.clearHighlights()
        btn = self._beats.get(beat)
        if btn is None:
            return
        btn.setStyleSheet('QToolButton {border: 4px dotted #9b2226; border-radius: 6;} QToolTip {border: 0px;}')
        btn.setFixedSize(self._beatHeight + 8, self._beatHeight + 8)

    def highlightScene(self, scene: Scene):
        beat = scene.beat(self.novel)
        if beat:
            self.highlightBeat(beat)
        else:
            self.clearHighlights()
            index = self.novel.scenes.index(scene)
            previous_beat_scene = None
            previous_beat = None
            next_beat_scene = None
            next_beat = None
            for _scene in self.novel.scenes[0: index]:
                previous_beat = _scene.beat(self.novel)
                if previous_beat:
                    previous_beat_scene = _scene
                    break
            for _scene in self.novel.scenes[index: len(self.novel.scenes)]:
                next_beat = _scene.beat(self.novel)
                if next_beat:
                    next_beat_scene = _scene
                    break

            min_percentage = previous_beat.percentage if previous_beat else 1
            if not next_beat:
                return
            max_percentage = next_beat.percentage
            min_index = self.novel.scenes.index(previous_beat_scene) if previous_beat_scene else 0
            max_index = self.novel.scenes.index(next_beat_scene) if next_beat_scene else len(self.novel.scenes) - 1

            self._currentScenePercentage = (max_percentage - min_percentage) / (max_index - min_index) * (
                    index - min_index)

            self.btnCurrentScene.setVisible(True)
            self.btnCurrentScene.setGeometry(self.width() * self._currentScenePercentage / 100 - self._lineHeight // 2,
                                             self._lineHeight,
                                             self._beatHeight,
                                             self._beatHeight)

    def unhighlightBeats(self):
        for btn in self._beats.values():
            btn.setStyleSheet('border: 0px;')
            btn.setFixedSize(self._beatHeight, self._beatHeight)

    def clearHighlights(self):
        self.unhighlightBeats()
        self.btnCurrentScene.setHidden(True)

    def toggleBeat(self, beat: StoryBeat, toggled: bool):
        btn = self._beats.get(beat)
        if btn is None:
            return

        if toggled:
            btn.setCheckable(False)
        else:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            self._beatToggled(btn, False)

    def toggleBeatVisibility(self, beat: StoryBeat):
        btn = self._beats.get(beat)
        if btn is None:
            return

        if beat.enabled:
            qtanim.fade_in(btn)
        else:
            qtanim.fade_out(btn)

    def _xForAct(self, act: int):
        if act == 1:
            return self.rect().x() + self._margin
        width = self.rect().width() - 2 * self._margin
        if act == 2:
            return width * 0.2 - 8
        if act == 3:
            return width * 0.75 - 8

    def _actButton(self, text: str, color: str, left: bool = False, right: bool = False) -> QPushButton:
        act = QPushButton(self)
        act.setText(text)
        act.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        act.setFixedHeight(self._lineHeight)
        act.setCursor(Qt.PointingHandCursor)
        act.setCheckable(True)
        act.setStyleSheet(f'''
        QPushButton {{
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {color}, stop: 1 {color});
            border: 1px solid #8f8f91;
            border-top-left-radius: {8 if left else 0}px;
            border-bottom-left-radius: {8 if left else 0}px;
            border-top-right-radius: {8 if right else 0}px;
            border-bottom-right-radius: {8 if right else 0}px;
            color:white;
            padding: 0px;
        }}
        ''')

        act.setChecked(True)
        act.toggled.connect(partial(self._actToggled, act))

        return act

    def _actToggled(self, btn: QToolButton, toggled: bool):
        opaque(btn, 1.0 if toggled else 0.2)

    def _beatToggled(self, btn: QToolButton, toggled: bool):
        opaque(btn, 1.0 if toggled else 0.2)

    def _beatClicked(self, beat: StoryBeat, btn: QToolButton):
        if btn.isCheckable() and btn.isChecked():
            self.beatSelected.emit(beat)
            btn.setCheckable(False)
        elif not btn.isCheckable() and self._removalContextMenuEnabled:
            builder = PopupMenuBuilder.from_widget_position(self, self.mapFromGlobal(QCursor.pos()))
            builder.add_action('Remove', IconRegistry.trash_can_icon(), lambda: self.beatRemovalRequested.emit(beat))
            builder.popup()


class ScenesPreferencesWidget(QWidget, Ui_ScenesViewPreferences):
    def __init__(self, parent=None):
        super(ScenesPreferencesWidget, self).__init__(parent)
        self.setupUi(self)

        self.btnCardsWidth.setIcon(IconRegistry.from_name('ei.resize-horizontal'))

        self.tabWidget.setTabIcon(self.tabWidget.indexOf(self.tabCards), IconRegistry.cards_icon())
