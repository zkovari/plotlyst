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
import pickle
from abc import abstractmethod
from typing import List, Set, Optional, Union

from PyQt5.QtCore import Qt, QObject, QEvent, QMimeData, QByteArray, QTimer
from PyQt5.QtGui import QDrag, QMouseEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent, QDragLeaveEvent
from PyQt5.QtWidgets import QSizePolicy, QWidget, QListView, QFrame, QToolButton, QHBoxLayout, QHeaderView
from overrides import overrides

from src.main.python.plotlyst.core.domain import Scene, SelectionItem, Novel, SceneGoal, SceneType, \
    SceneStructureItemType, SceneStructureAgenda, SceneStructureItem, Conflict, SceneOutcome, NEUTRAL
from src.main.python.plotlyst.model.common import SelectionItemsModel
from src.main.python.plotlyst.model.novel import NovelPlotsModel, NovelTagsModel
from src.main.python.plotlyst.model.scenes_model import SceneGoalsModel, SceneConflictsModel
from src.main.python.plotlyst.view.common import spacer_widget
from src.main.python.plotlyst.view.generated.scene_beat_item_widget_ui import Ui_SceneBeatItemWidget
from src.main.python.plotlyst.view.generated.scene_filter_widget_ui import Ui_SceneFilterWidget
from src.main.python.plotlyst.view.generated.scene_ouctome_selector_ui import Ui_SceneOutcomeSelectorWidget
from src.main.python.plotlyst.view.generated.scene_structure_editor_widget_ui import Ui_SceneStructureWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterConflictWidget
from src.main.python.plotlyst.view.widget.input import RotatedButtonOrientation
from src.main.python.plotlyst.view.widget.labels import LabelsEditorWidget, GoalLabel, ConflictLabel


class SceneGoalsWidget(LabelsEditorWidget):

    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        self.novel = novel
        self.scene_structure_item = scene_structure_item
        super(SceneGoalsWidget, self).__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.setValue([x.text for x in self.scene_structure_item.goals])
        self.btnEdit.setIcon(IconRegistry.goal_icon())
        self.btnEdit.setText('Track goals')
        self._wdgLabels.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.setStyleSheet('SceneGoalsWidget {border: 0px;}')

    @overrides
    def _initModel(self) -> SelectionItemsModel:
        model = SceneGoalsModel(self.novel, self.scene_structure_item)
        model.setCheckable(True, SceneGoalsModel.ColName)
        return model

    @overrides
    def items(self) -> List[SelectionItem]:
        return self.novel.scene_goals

    @overrides
    def _addItems(self, items: Set[SceneGoal]):
        for item in items:
            self._wdgLabels.addLabel(GoalLabel(item))
        self.scene_structure_item.goals.clear()
        self.scene_structure_item.goals.extend(items)


class SceneConflictsWidget(LabelsEditorWidget):
    def __init__(self, novel: Novel, scene: Scene, scene_structure_item: SceneStructureItem, parent=None):
        self.novel = novel
        self.scene = scene
        self.scene_structure_item = scene_structure_item
        super(SceneConflictsWidget, self).__init__(parent=parent)
        self.setValue([x.text for x in self.scene_structure_item.conflicts])
        self.btnEdit.setIcon(IconRegistry.conflict_icon())
        self.btnEdit.setText('Track conflicts')
        self._wdgLabels.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.setStyleSheet('SceneConflictsWidget {border: 0px;}')
        self._popup.new_conflict_added.connect(self.btnEdit.menu().hide)

    @overrides
    def _initModel(self) -> SelectionItemsModel:
        return SceneConflictsModel(self.novel, self.scene, self.scene_structure_item)

    @overrides
    def _initPopupWidget(self) -> QWidget:
        widget = CharacterConflictWidget(self.novel, self.scene, self.scene_structure_item)
        widget.tblConflicts.setModel(self._model)
        widget.tblConflicts.horizontalHeader().hideSection(SceneConflictsModel.ColBgColor)
        widget.tblConflicts.horizontalHeader().setSectionResizeMode(SceneConflictsModel.ColIcon,
                                                                    QHeaderView.ResizeToContents)
        widget.tblConflicts.horizontalHeader().setSectionResizeMode(SceneConflictsModel.ColName,
                                                                    QHeaderView.Stretch)
        return widget

    @overrides
    def items(self) -> List[SelectionItem]:
        return [x for x in self.novel.conflicts if self.scene.pov and x.character_id == self.scene.pov.id]

    @overrides
    def _addItems(self, items: Set[Conflict]):
        for item in items:
            self._wdgLabels.addLabel(ConflictLabel(self.novel, item))
        self.scene_structure_item.conflicts.clear()
        self.scene_structure_item.conflicts.extend(items)


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
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, placeholder: str = 'Beat',
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

    def sceneStructureItem(self) -> SceneStructureItem:
        self.scene_structure_item.text = self.text.toPlainText()
        return self.scene_structure_item

    def activate(self):
        self.text.setFocus()


class SceneGoalItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneGoalItemWidget, self).__init__(novel, scene_structure_item, placeholder='Goal', topVisible=True,
                                                  parent=parent)
        self._wdgGoals = SceneGoalsWidget(self.novel, self.scene_structure_item)
        self.layoutTop.addWidget(self._wdgGoals)
        self.btnIcon.setIcon(IconRegistry.goal_icon())

    @overrides
    def activate(self):
        self._wdgGoals.btnEdit.click()


class SceneConflictItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene: Scene, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneConflictItemWidget, self).__init__(novel, scene_structure_item, topVisible=True, parent=parent)
        self._wdgConflicts = SceneConflictsWidget(self.novel, scene, self.scene_structure_item)
        self.layoutTop.addWidget(self._wdgConflicts)
        self.text.setPlaceholderText('Conflict')
        self.btnIcon.setIcon(IconRegistry.conflict_icon())

    @overrides
    def activate(self):
        self._wdgConflicts.btnEdit.click()


class SceneOutcomeItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneOutcomeItemWidget, self).__init__(novel, scene_structure_item, topVisible=True, parent=parent)

        self.layoutTop.addWidget(SceneOutcomeSelector(self.scene_structure_item))
        self.layoutTop.addWidget(spacer_widget())
        self.text.setPlaceholderText('Outcome')
        self.btnIcon.setIcon(IconRegistry.action_scene_icon())


class ReactionSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(ReactionSceneItemWidget, self).__init__(novel, scene_structure_item, placeholder='Initial reaction',
                                                      parent=parent)
        self.btnIcon.setIcon(IconRegistry.reaction_icon())


class DilemmaSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(DilemmaSceneItemWidget, self).__init__(novel, scene_structure_item,
                                                     placeholder='Dilemma throughout the scene', parent=parent)
        self.btnIcon.setIcon(IconRegistry.dilemma_icon())


class DecisionSceneItemWidget(SceneGoalItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(DecisionSceneItemWidget, self).__init__(novel, scene_structure_item, parent=parent)
        self._wdgGoals.btnEdit.setText('New goal')
        self.btnIcon.setIcon(IconRegistry.decision_icon())
        self.text.setPlaceholderText('New goal and action')


class IncitingIncidentSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super().__init__(novel, scene_structure_item, placeholder='Inciting incident of the scene', parent=parent)
        self.btnIcon.setIcon(IconRegistry.inciting_incident_icon())


class RisingActionSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super().__init__(novel, scene_structure_item, placeholder='Increasing tension throughout the scene',
                         parent=parent)
        self.btnIcon.setIcon(IconRegistry.rising_action_icon())


class CrisisSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super().__init__(novel, scene_structure_item,
                         placeholder='The impossible decision of two good or two equally bad outcomes', parent=parent)
        self.btnIcon.setIcon(IconRegistry.crisis_icon())


class TicklingClockSceneItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super().__init__(novel, scene_structure_item, placeholder='Ticking clock is activated to increase tension',
                         parent=parent)
        self.btnIcon.setIcon(IconRegistry.tickling_clock_icon())


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

        self.rbScene.setIcon(IconRegistry.action_scene_icon())
        self.rbSequel.setIcon(IconRegistry.reaction_scene_icon())

        self.btnTemplates.setIcon(IconRegistry.template_icon())

        self.btnBeginningIcon.setIcon(IconRegistry.cause_icon())
        self.btnMiddleIcon.setIcon(IconRegistry.from_name('mdi.ray-vertex'))
        self.btnEndIcon.setIcon(IconRegistry.from_name('mdi.ray-end'))

        self.btnSceneIcon.setIcon(IconRegistry.action_scene_icon())
        self.btnSequelIcon.setIcon(IconRegistry.reaction_scene_icon())
        self.btnGoal.setIcon(IconRegistry.goal_icon())
        self.btnConflict.setIcon(IconRegistry.conflict_icon())
        self.btnOutcome.setIcon(IconRegistry.disaster_icon())

        self.btnReaction.setIcon(IconRegistry.reaction_icon())
        self.btnDilemma.setIcon(IconRegistry.dilemma_icon())
        self.btnDecision.setIcon(IconRegistry.decision_icon())

        self.btnIncitingIncident.setIcon(IconRegistry.inciting_incident_icon())
        self.btnRisingAction.setIcon(IconRegistry.rising_action_icon())
        self.btnCrisis.setIcon(IconRegistry.crisis_icon())
        self.btnTickingClock.setIcon(IconRegistry.tickling_clock_icon())

        self._addPlaceholder(self.wdgBeginning)
        self._addPlaceholder(self.wdgMiddle)
        self._addPlaceholder(self.wdgEnd)

        self.btnGoal.installEventFilter(self)
        self.btnConflict.installEventFilter(self)
        self.btnOutcome.installEventFilter(self)
        self.btnReaction.installEventFilter(self)
        self.btnDilemma.installEventFilter(self)
        self.btnDecision.installEventFilter(self)
        self.btnIncitingIncident.installEventFilter(self)
        self.btnRisingAction.installEventFilter(self)
        self.btnCrisis.installEventFilter(self)
        self.btnTickingClock.installEventFilter(self)

        self.btnGroupType.buttonClicked.connect(self._type_clicked)
        self.btnGroupType.buttonToggled.connect(self._type_toggled)

    def setScene(self, novel: Novel, scene: Scene):
        self.novel = novel
        self.scene = scene

        self.clear()
        self.btnInventory.setChecked(False)

        if self.scene.type == SceneType.ACTION:
            self.rbScene.setChecked(True)
        elif self.scene.type == SceneType.REACTION:
            self.rbSequel.setChecked(True)
        else:
            self.btnInventory.setChecked(True)
            self.rbCustom.setChecked(True)

        if scene.agendas and scene.agendas[0].items:
            widgets_per_parts = {1: self.wdgBeginning, 2: self.wdgMiddle, 3: self.wdgEnd}

            for item in scene.agendas[0].items:
                if item.type == SceneStructureItemType.GOAL:
                    widget = SceneGoalItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.CONFLICT:
                    widget = SceneConflictItemWidget(self.novel, self.scene, item)
                elif item.type == SceneStructureItemType.OUTCOME:
                    widget = SceneOutcomeItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.REACTION:
                    widget = ReactionSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.DILEMMA:
                    widget = DilemmaSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.DECISION:
                    widget = DecisionSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.INCITING_INCIDENT:
                    widget = IncitingIncidentSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.RISING_ACTION:
                    widget = RisingActionSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.CRISIS:
                    widget = CrisisSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.TICKING_CLOCK:
                    widget = TicklingClockSceneItemWidget(self.novel, item)
                else:
                    widget = SceneStructureItemWidget(self.novel, item)
                widgets_per_parts.get(item.part, self.wdgEnd).layout().addWidget(widget)
                self._addPlaceholder(widgets_per_parts.get(item.part, self.wdgEnd))

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

        if not self.agendas()[0].items:
            self._type_clicked()

    def _setEmotionColorChange(self):
        color_start = self.btnEmotionStart.color()
        color_end = self.btnEmotionEnd.color()
        self.btnEmotionRangeDisplay.setStyleSheet(f'''
        background-color: qlineargradient(x1: 1, y1: 0, x2: 0, y2: 0,
                                      stop: 0 {color_start}, stop: 1 {color_end});
        color: white;
        ''')

    def updatePov(self):
        self.clear(addPlaceholders=True)

    def clear(self, addPlaceholders: bool = False):
        for widget in [self.wdgBeginning, self.wdgMiddle, self.wdgEnd]:
            while widget.layout().count():
                item = widget.layout().takeAt(0)
                if item:
                    item.widget().deleteLater()
        if addPlaceholders:
            self._addPlaceholder(self.wdgBeginning)
            self._addPlaceholder(self.wdgMiddle)
            self._addPlaceholder(self.wdgEnd)

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

    def agendas(self) -> List[SceneStructureAgenda]:
        agenda = SceneStructureAgenda()
        self._collect_agenda_items(agenda, self.wdgBeginning, 1)
        self._collect_agenda_items(agenda, self.wdgMiddle, 2)
        self._collect_agenda_items(agenda, self.wdgEnd, 3)
        agenda.beginning_emotion = self.btnEmotionStart.value()
        agenda.ending_emotion = self.btnEmotionEnd.value()
        return [agenda]

    def _collect_agenda_items(self, agenda: SceneStructureAgenda, widget: QWidget, part: int):
        for i in range(widget.layout().count()):
            item = widget.layout().itemAt(i)
            if isinstance(item.widget(), SceneStructureItemWidget):
                structure_item: SceneStructureItem = item.widget().sceneStructureItem()
                structure_item.part = part
                agenda.items.append(structure_item)

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
        if dragged is self.btnIncitingIncident:
            return SceneStructureItemType.INCITING_INCIDENT
        if dragged is self.btnRisingAction:
            return SceneStructureItemType.RISING_ACTION
        if dragged is self.btnCrisis:
            return SceneStructureItemType.CRISIS
        if dragged is self.btnTickingClock:
            return SceneStructureItemType.TICKING_CLOCK

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
            widget = SceneConflictItemWidget(self.novel, self.scene, SceneStructureItem(data))
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
        elif data == SceneStructureItemType.INCITING_INCIDENT:
            widget = IncitingIncidentSceneItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.RISING_ACTION:
            widget = RisingActionSceneItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.CRISIS:
            widget = CrisisSceneItemWidget(self.novel, SceneStructureItem(data))
        elif data == SceneStructureItemType.TICKING_CLOCK:
            widget = TicklingClockSceneItemWidget(self.novel, SceneStructureItem(data))
        else:
            raise ValueError('Unknown scene structure item')

        self._addWidget(placeholder, widget)

        event.accept()

        QTimer.singleShot(50, widget.activate)

    def _addWidget(self, placeholder: _PlaceHolder, widget: SceneStructureItemWidget):
        parent = placeholder.parent()
        layout: QHBoxLayout = parent.layout()
        index = layout.indexOf(placeholder)
        layout.takeAt(index)
        placeholder.deleteLater()
        layout.insertWidget(index, widget)
        self._addPlaceholder(parent)

    def _addPlaceholder(self, widget: QWidget):
        _placeholder = _PlaceHolder()
        widget.layout().addWidget(_placeholder)
        _placeholder.installEventFilter(self)

    def _type_clicked(self):
        self.clear(addPlaceholders=True)

        if self.rbScene.isChecked():
            self.scene.type = SceneType.ACTION
            top = SceneGoalItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.GOAL))
            middle = SceneConflictItemWidget(self.novel, self.scene,
                                             SceneStructureItem(SceneStructureItemType.CONFLICT))
            bottom = SceneOutcomeItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.OUTCOME,
                                                                           outcome=SceneOutcome.DISASTER))
        elif self.rbSequel.isChecked():
            self.scene.type = SceneType.REACTION
            top = ReactionSceneItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.REACTION))
            middle = DilemmaSceneItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.DILEMMA))
            bottom = DecisionSceneItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.DECISION))
        else:
            self.scene.type = SceneType.MIXED
            top = SceneStructureItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.BEAT),
                                           placeholder='Describe the beginning event')
            middle = SceneStructureItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.BEAT),
                                              placeholder='Describe the middle part of this scene')
            bottom = SceneStructureItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.BEAT),
                                              placeholder='Describe the ending of this scene')
            self.btnInventory.setChecked(True)

        self._addWidget(self.wdgBeginning.layout().itemAt(0).widget(), top)
        self._addWidget(self.wdgMiddle.layout().itemAt(0).widget(), middle)
        self._addWidget(self.wdgEnd.layout().itemAt(0).widget(), bottom)

    def _type_toggled(self):
        font = self.rbScene.font()
        font.setBold(self.rbScene.isChecked())
        self.rbScene.setFont(font)
        font = self.rbSequel.font()
        font.setBold(self.rbSequel.isChecked())
        self.rbSequel.setFont(font)
        font = self.rbCustom.font()
        font.setBold(self.rbCustom.isChecked())
        self.rbCustom.setFont(font)

    def _dragDestroyed(self):
        self._dragged = None
