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
from enum import Enum
from functools import partial
from typing import Dict, Optional
from typing import List

import qtanim
from PyQt5.QtCore import QPoint, QTimeLine
from PyQt5.QtCore import Qt, QObject, QEvent, QSize, pyqtSignal, QModelIndex, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDragLeaveEvent, \
    QResizeEvent, QCursor, QColor, QDragMoveEvent, QDropEvent, QMouseEvent
from PyQt5.QtGui import QPaintEvent, QPainter, QPen, QPainterPath
from PyQt5.QtWidgets import QSizePolicy, QWidget, QFrame, QToolButton, QHBoxLayout, QSplitter, \
    QPushButton, QHeaderView, QTreeView, QMenu, QWidgetAction, QTextEdit
from overrides import overrides
from qtanim import fade_out
from qthandy import busy, margins, vspacer
from qthandy import decr_font, ask_confirmation, gc, transparent, retain_when_hidden, opaque, underline, flow, \
    clear_layout, hbox, spacer, btn_popup, vbox, italic
from qthandy.filter import InstantTooltipEventFilter

from src.main.python.plotlyst.common import ACT_ONE_COLOR, ACT_THREE_COLOR, ACT_TWO_COLOR, RELAXED_WHITE_COLOR
from src.main.python.plotlyst.common import truncate_string
from src.main.python.plotlyst.core.domain import Scene, Novel, SceneType, \
    SceneStructureItemType, SceneStructureAgenda, SceneStructureItem, SceneOutcome, NEUTRAL, StoryBeat, Conflict, \
    Character, Plot, ScenePlotReference, CharacterGoal, Chapter, StoryBeatType, Tag, PlotValue, ScenePlotValueCharge
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import emit_critical, emit_event
from src.main.python.plotlyst.events import ChapterChangedEvent, SceneChangedEvent
from src.main.python.plotlyst.model.chapters_model import ChaptersTreeModel, ChapterNode, SceneNode
from src.main.python.plotlyst.model.novel import NovelTagsTreeModel, TagNode
from src.main.python.plotlyst.view.common import OpacityEventFilter, DisabledClickEventFilter, PopupMenuBuilder, \
    DragEventFilter, hmax
from src.main.python.plotlyst.view.generated.scene_beat_item_widget_ui import Ui_SceneBeatItemWidget
from src.main.python.plotlyst.view.generated.scene_filter_widget_ui import Ui_SceneFilterWidget
from src.main.python.plotlyst.view.generated.scene_ouctome_selector_ui import Ui_SceneOutcomeSelectorWidget
from src.main.python.plotlyst.view.generated.scene_structure_editor_widget_ui import Ui_SceneStructureWidget
from src.main.python.plotlyst.view.generated.scenes_view_preferences_widget_ui import Ui_ScenesViewPreferences
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import WordWrappedPushButton, SecondaryActionToolButton
from src.main.python.plotlyst.view.widget.characters import CharacterConflictSelector, CharacterGoalSelector
from src.main.python.plotlyst.view.widget.input import RotatedButtonOrientation, RotatedButton
from src.main.python.plotlyst.view.widget.labels import SelectionItemLabel, ScenePlotValueLabel, \
    PlotLabel, PlotValueLabel
from src.main.python.plotlyst.view.widget.tree_view import ActionBasedTreeView
from src.main.python.plotlyst.worker.cache import acts_registry
from src.main.python.plotlyst.worker.persistence import RepositoryPersistenceManager


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


class ScenePlotValueChargeWidget(QWidget):
    def __init__(self, plotReference: ScenePlotReference, value: PlotValue, parent=None):
        super(ScenePlotValueChargeWidget, self).__init__(parent)
        self.plotReference = plotReference
        self.value: PlotValue = value
        lbl = PlotValueLabel(value)
        hmax(lbl)
        hbox(self)

        self.charge: int = 0
        self.plot_value_charge: Optional[ScenePlotValueCharge] = None
        for v in self.plotReference.data.values:
            if v.plot_value_id == value.id:
                self.charge = v.charge
                self.plot_value_charge = v

        self.chargeIcon = QToolButton()
        transparent(self.chargeIcon)
        self.chargeIcon.setIconSize(QSize(22, 22))
        self.chargeIcon.setIcon(IconRegistry.charge_icon(self.charge))

        self.posCharge = SecondaryActionToolButton()
        self.posCharge.setIcon(IconRegistry.plus_circle_icon('grey'))
        self.posCharge.setIconSize(QSize(18, 18))
        self.posCharge.clicked.connect(lambda: self._changeCharge(1))
        retain_when_hidden(self.posCharge)
        self.negCharge = SecondaryActionToolButton()
        self.negCharge.setIcon(IconRegistry.minus_icon('grey'))
        self.negCharge.setIconSize(QSize(18, 18))
        self.negCharge.clicked.connect(lambda: self._changeCharge(-1))
        retain_when_hidden(self.negCharge)

        self.layout().addWidget(self.chargeIcon)
        self.layout().addWidget(lbl, alignment=Qt.AlignLeft)
        self.layout().addWidget(spacer())
        self.layout().addWidget(self.negCharge)
        self.layout().addWidget(self.posCharge)

        self._updateButtons()

    def _changeCharge(self, increment: int):
        self.charge += increment
        if self.plot_value_charge is None:
            self.plot_value_charge = ScenePlotValueCharge(self.value.id, self.charge)
            self.plotReference.data.values.append(self.plot_value_charge)
        self.plot_value_charge.charge = self.charge

        self.chargeIcon.setIcon(IconRegistry.charge_icon(self.charge))
        if increment > 0:
            qtanim.glow(self.chargeIcon, color=QColor('#52b788'))
        else:
            qtanim.glow(self.chargeIcon, color=QColor('#9d0208'))

        self._updateButtons()

    def _updateButtons(self):
        if not self.negCharge.isEnabled():
            self.negCharge.setEnabled(True)
            self.negCharge.setVisible(True)
        if not self.posCharge.isEnabled():
            self.posCharge.setEnabled(True)
            self.posCharge.setVisible(True)
        if self.charge == 3:
            self.posCharge.setDisabled(True)
            self.posCharge.setHidden(True)
        if self.charge == -3:
            self.negCharge.setDisabled(True)
            self.negCharge.setHidden(True)


class ScenePlotValueEditor(QWidget):
    def __init__(self, plotReference: ScenePlotReference, parent=None):
        super(ScenePlotValueEditor, self).__init__(parent)
        self.plotReference = plotReference

        vbox(self)
        self.textComment = QTextEdit(self)
        self.textComment.setAcceptRichText(False)
        self.textComment.setFixedHeight(100)
        self.textComment.setPlaceholderText('Describe how this scene is related to the selected plot')
        self.textComment.setText(self.plotReference.data.comment)
        self.textComment.textChanged.connect(self._commentChanged)
        self.layout().addWidget(self.textComment)

        for value in self.plotReference.plot.values:
            wdg = ScenePlotValueChargeWidget(self.plotReference, value)
            self.layout().addWidget(wdg)

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        pass

    def _commentChanged(self):
        self.plotReference.data.comment = self.textComment.toPlainText()


class ScenePlotSelector(QWidget):
    plotSelected = pyqtSignal()

    def __init__(self, novel: Novel, scene: Scene, simplified: bool = False, parent=None):
        super(ScenePlotSelector, self).__init__(parent)
        self.novel = novel
        self.scene = scene
        self.plotValue: Optional[ScenePlotReference] = None
        hbox(self)

        self.label: Optional[SelectionItemLabel] = None

        self.btnLinkPlot = QPushButton(self)
        if simplified:
            self.btnLinkPlot.setIcon(IconRegistry.plus_circle_icon('grey'))
        else:
            self.btnLinkPlot.setText('Associate plot')
        self.layout().addWidget(self.btnLinkPlot)
        self.btnLinkPlot.setCursor(Qt.PointingHandCursor)
        self.btnLinkPlot.setStyleSheet('''
                                QPushButton {
                                    border: 2px dotted darkGrey;
                                    border-radius: 6px;
                                    padding: 2px;
                                    color: darkGrey;
                                }
                                QPushButton:hover {
                                    border: 2px dotted black;
                                    color: black;
                                }
                                QPushButton:pressed {
                                    border: 2px solid black;
                                }
                            ''')

        self.btnLinkPlot.installEventFilter(
            OpacityEventFilter(leaveOpacity=0.4 if simplified else 0.7, parent=self.btnLinkPlot))

        self.selectorWidget = QWidget()
        vbox(self.selectorWidget)
        occupied_plot_ids = [x.plot.id for x in self.scene.plot_values]
        for plot in self.novel.plots:
            if plot.id in occupied_plot_ids:
                continue
            label = PlotLabel(plot)
            label.installEventFilter(OpacityEventFilter(leaveOpacity=0.7, parent=label))
            label.clicked.connect(partial(self._plotSelected, plot))
            self.selectorWidget.layout().addWidget(label)

        btn_popup(self.btnLinkPlot, self.selectorWidget)

    def setPlot(self, plotValue: ScenePlotReference):
        self.plotValue = plotValue
        self.label = ScenePlotValueLabel(plotValue)
        self.label.setCursor(Qt.PointingHandCursor)
        self.label.clicked.connect(self._plotValueClicked)

        self.label.removalRequested.connect(self._remove)
        self.layout().addWidget(self.label)
        self.btnLinkPlot.setHidden(True)

    def _plotSelected(self, plot: Plot):
        self.btnLinkPlot.menu().hide()
        plotValue = ScenePlotReference(plot)
        self.scene.plot_values.append(plotValue)
        self.setPlot(plotValue)

        self.plotSelected.emit()

    def _plotValueClicked(self):
        menu = QMenu(self.label)
        action = QWidgetAction(menu)
        action.setDefaultWidget(ScenePlotValueEditor(self.plotValue))
        menu.addAction(action)
        menu.popup(QCursor.pos())

    def _remove(self):
        if self.parent():
            anim = qtanim.fade_out(self, duration=150)
            anim.finished.connect(self.__destroy)

    def __destroy(self):
        self.scene.plot_values.remove(self.plotValue)
        self.parent().layout().removeWidget(self)
        gc(self)


class SceneTagSelector(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super(SceneTagSelector, self).__init__(parent)
        self.novel = novel

        hbox(self)
        self.btnSelect = QToolButton(self)
        self.btnSelect.setIcon(IconRegistry.tag_plus_icon())
        self.btnSelect.setCursor(Qt.PointingHandCursor)

        self._tagsModel = NovelTagsTreeModel(self.novel)
        self._tagsModel.selectionChanged.connect(self._selectionChanged)
        self._treeSelectorView = QTreeView()
        self._treeSelectorView.setCursor(Qt.PointingHandCursor)
        self._treeSelectorView.setModel(self._tagsModel)
        self._treeSelectorView.setHeaderHidden(True)
        self._treeSelectorView.clicked.connect(self._toggle)
        self._treeSelectorView.expandAll()
        self._tagsModel.modelReset.connect(self._treeSelectorView.expandAll)
        btn_popup(self.btnSelect, self._treeSelectorView)

        self.wdgTags = QFrame(self)
        flow(self.wdgTags)
        self.setStyleSheet('#wdgTags {background-color: white;}')

        self.layout().addWidget(self.btnSelect, alignment=Qt.AlignTop)
        self.layout().addWidget(self.wdgTags)

    def setScene(self, scene: Scene):
        self._tagsModel.clear()
        for tag in scene.tags(self.novel):
            self._tagsModel.check(tag)

    def tags(self) -> List[Tag]:
        return self._tagsModel.checkedTags()

    def _selectionChanged(self):
        tags = self._tagsModel.checkedTags()
        clear_layout(self.wdgTags)
        for tag in tags:
            label = SelectionItemLabel(tag, self.wdgTags, removalEnabled=True)
            label.removalRequested.connect(partial(self._tagsModel.uncheck, tag))
            self.wdgTags.layout().addWidget(label)

    def _toggle(self, index: QModelIndex):
        node = index.data(NovelTagsTreeModel.NodeRole)
        if isinstance(node, TagNode):
            self._tagsModel.toggle(node.tag)


class SceneFilterWidget(QFrame, Ui_SceneFilterWidget):
    def __init__(self, novel: Novel, parent=None):
        super(SceneFilterWidget, self).__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.povFilter.setExclusive(False)
        self.povFilter.setCharacters(self.novel.pov_characters())

        self.tabWidget.setTabIcon(self.tabWidget.indexOf(self.tabPov), IconRegistry.character_icon())


StructureItemMimeType: str = 'application/structure-item'


class _PlaceHolder(QFrame):
    dropped = pyqtSignal(object, SceneStructureItemType)

    def __init__(self):
        super(_PlaceHolder, self).__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(5)
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
        if event.mimeData().hasFormat(StructureItemMimeType):
            self.setStyle(True)
            event.accept()
        else:
            event.ignore()

    @overrides
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        event.accept()

    @overrides
    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.setStyle()

    @overrides
    def dropEvent(self, event: QDropEvent) -> None:
        self.setStyle()
        data: SceneStructureItemType = pickle.loads(event.mimeData().data(StructureItemMimeType))
        self.dropped.emit(self, data)


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

    def __init__(self, parent=None):
        super(SceneStructureWidget, self).__init__(parent)
        self.setupUi(self)

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

        for btn in [self.btnGoal, self.btnConflict, self.btnOutcome, self.btnReaction, self.btnDilemma,
                    self.btnDecision, self.btnHook, self.btnIncitingIncident, self.btnRisingAction, self.btnCrisis,
                    self.btnTickingClock, self.btnExposition, self.btnBeat]:
            btn.installEventFilter(DragEventFilter(btn, StructureItemMimeType, self._buttonType))

        self.btnScene.installEventFilter(OpacityEventFilter(parent=self.btnScene, ignoreCheckedButton=True))
        self.btnSequel.installEventFilter(OpacityEventFilter(parent=self.btnSequel, ignoreCheckedButton=True))

        self.btnScene.clicked.connect(partial(self._typeClicked, SceneType.ACTION))
        self.btnSequel.clicked.connect(partial(self._typeClicked, SceneType.REACTION))

        self.wdgAgendaCharacter.setDefaultText('Agenda character')
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
                elif item.type == SceneStructureItemType.CONFLICT:
                    widget = SceneConflictItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.OUTCOME:
                    widget = SceneOutcomeItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.REACTION:
                    widget = ReactionSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.DILEMMA:
                    widget = DilemmaSceneItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.DECISION:
                    widget = DecisionSceneItemWidget(self.novel, item)
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

        self._initSelectors()

    def updateAgendas(self):
        if not self.scene.agendas:
            return
        self.scene.agendas[0].items.clear()
        self._collect_agenda_items(self.scene.agendas[0], self.wdgBeginning, 1)
        self._collect_agenda_items(self.scene.agendas[0], self.wdgMiddle, 2)
        self._collect_agenda_items(self.scene.agendas[0], self.wdgEnd, 3)
        self.scene.agendas[0].beginning_emotion = self.btnEmotionStart.value()
        self.scene.agendas[0].ending_emotion = self.btnEmotionEnd.value()

    def _dropped(self, placeholder: _PlaceHolder, data: SceneStructureItemType):
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

        QTimer.singleShot(50, widget.activate)

    def _toggleCharacterStatus(self):
        if self.scene.agendas[0].character_id:
            self.btnEmotionStart.setEnabled(True)
            self.btnEmotionEnd.setEnabled(True)
            self.wdgAgendaCharacter.setEnabled(True)
            self.btnEmotionStart.setToolTip('')
            self.btnEmotionEnd.setToolTip('')
            char = self.scene.agendas[0].character(self.novel)
            if char:
                self.wdgAgendaCharacter.setCharacter(char)
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
        _placeholder.dropped.connect(self._dropped)

    def _addPlaceholder(self, widget: QWidget, pos: int = -1):
        _placeholder = _PlaceHolder()
        if pos >= 0:
            widget.layout().insertWidget(pos, _placeholder)
        else:
            widget.layout().addWidget(_placeholder)
        _placeholder.dropped.connect(self._dropped)

    def _typeClicked(self, type: SceneType, checked: bool, lazy: bool = True):
        if lazy and type == self.scene.type and checked:
            return

        if any(x.text for x in self.scene.agendas[0].items):
            if not ask_confirmation(
                    "Some beats are filled up. Are you sure you want to change the scene's structure?"):
                self._checkSceneType()  # revert
                return
                # break

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

    def _initSelectors(self):
        if not self.scene.agendas[0].character_id:
            return
        clear_layout(self.wdgGoalConflictContainer)
        if self.scene.agendas[0].goal_references:
            for char_goal in self.scene.agendas[0].goals(self.scene.agendas[0].character(self.novel)):
                self._addGoalSelector(char_goal)
            self._addGoalSelector()
        else:
            self._addGoalSelector()

        if self.scene.agendas[0].conflict_references:
            for conflict in self.scene.agendas[0].conflicts(self.novel):
                self._addConfictSelector(conflict=conflict)
            self._addConfictSelector()
        else:
            self._addConfictSelector()

    def _addGoalSelector(self, charGoal: Optional[CharacterGoal] = None):
        simplified = len(self.scene.agendas[0].goal_references) > 0
        selector = CharacterGoalSelector(self.novel, self.scene, simplified=simplified)
        self.wdgGoalConflictContainer.layout().addWidget(selector)
        selector.goalSelected.connect(self._initSelectors)
        if charGoal:
            selector.setGoal(charGoal)

    def _addConfictSelector(self, conflict: Optional[Conflict] = None):
        simplified = len(self.scene.agendas[0].conflict_references) > 0
        conflict_selector = CharacterConflictSelector(self.novel, self.scene, simplified=simplified,
                                                      parent=self.wdgGoalConflictContainer)
        if conflict:
            conflict_selector.setConflict(conflict)
        self.wdgGoalConflictContainer.layout().addWidget(conflict_selector)
        conflict_selector.conflictSelected.connect(self._initSelectors)


class SceneStoryStructureWidget(QWidget):
    beatSelected = pyqtSignal(StoryBeat)
    beatRemovalRequested = pyqtSignal(StoryBeat)
    actsResized = pyqtSignal()

    def __init__(self, parent=None):
        super(SceneStoryStructureWidget, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self._checkOccupiedBeats: bool = True
        self._beatsCheckable: bool = False
        self._removalContextMenuEnabled: bool = False
        self._actsClickable: bool = False
        self._actsResizeable: bool = False
        self._beatCursor = Qt.PointingHandCursor
        self.novel: Optional[Novel] = None
        self._acts: List[QPushButton] = []
        self._beats: Dict[StoryBeat, QToolButton] = {}
        self._containers: Dict[StoryBeat, QPushButton] = {}
        self._actsSplitter: Optional[QSplitter] = None
        self.btnCurrentScene = QToolButton(self)
        self._currentScenePercentage = 1
        self.btnCurrentScene.setIcon(IconRegistry.circle_icon(color='red'))
        self.btnCurrentScene.setHidden(True)
        transparent(self.btnCurrentScene)
        self._wdgLine = QWidget(self)
        hbox(self._wdgLine, 0, 0)
        self._lineHeight: int = 22
        self._beatHeight: int = 20
        self._margin: int = 5
        self._containerTopMargin: int = 6

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
            if beat.type == StoryBeatType.CONTAINER:
                btn = QPushButton(self)
                if beat.percentage_end - beat.percentage > 7:
                    btn.setText(beat.text)
                self._containers[beat] = btn
                btn.setStyleSheet(f'''
                    QPushButton {{border-top:2px dashed {beat.icon_color}; color: {beat.icon_color};}}
                ''')
                italic(btn)
                opaque(btn)
            else:
                btn = QToolButton(self)
                self._beats[beat] = btn
                btn.setStyleSheet('QToolButton {background-color: rgba(0,0,0,0); border:0px;} QToolTip {border: 0px;}')

            if beat.icon:
                btn.setIcon(IconRegistry.from_name(beat.icon, beat.icon_color))
            btn.setToolTip(f'<b style="color: {beat.icon_color}">{beat.text}')

            if beat.type == StoryBeatType.BEAT:
                btn.installEventFilter(InstantTooltipEventFilter(btn))
                btn.toggled.connect(partial(self._beatToggled, btn))
                btn.clicked.connect(partial(self._beatClicked, beat, btn))
                btn.installEventFilter(self)
                btn.setCursor(self._beatCursor)
                if self._checkOccupiedBeats and beat not in occupied_beats:
                    if self._beatsCheckable:
                        btn.setCheckable(True)
                    self._beatToggled(btn, False)

            if not beat.enabled:
                btn.setHidden(True)

        self._actsSplitter = QSplitter(self._wdgLine)
        self._actsSplitter.setContentsMargins(0, 0, 0, 0)
        self._actsSplitter.setChildrenCollapsible(False)
        self._actsSplitter.setHandleWidth(1)
        self._wdgLine.layout().addWidget(self._actsSplitter)

        act = self._actButton('Act 1', ACT_ONE_COLOR, left=True)
        self._acts.append(act)
        self._wdgLine.layout().addWidget(act)
        self._actsSplitter.addWidget(act)
        act = self._actButton('Act 2', ACT_TWO_COLOR)
        self._acts.append(act)
        self._actsSplitter.addWidget(act)

        act = self._actButton('Act 3', ACT_THREE_COLOR, right=True)
        self._acts.append(act)
        self._actsSplitter.addWidget(act)
        for btn in self._acts:
            btn.setEnabled(self._actsClickable)

        beats = self.novel.active_story_structure.act_beats()
        if not len(beats) == 2:
            return emit_critical('Only 3 acts are supported at the moment for story structure widget')

        self._actsSplitter.setSizes([10 * beats[0].percentage,
                                     10 * (beats[1].percentage - beats[0].percentage),
                                     10 * (100 - beats[1].percentage)])
        self._actsSplitter.setEnabled(self._actsResizeable)
        self._actsSplitter.splitterMoved.connect(self._actResized)
        self.update()

    @overrides
    def minimumSizeHint(self) -> QSize:
        beat_height = self._beatHeight * 2 if self._containers else self._beatHeight
        return QSize(300, self._lineHeight + beat_height + 6)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QToolButton) and watched.isCheckable() and not watched.isChecked():
            if event.type() == QEvent.Enter:
                opaque(watched)
            elif event.type() == QEvent.Leave:
                opaque(watched, 0.2)
        return super(SceneStoryStructureWidget, self).eventFilter(watched, event)

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        self._rearrangeBeats()
        if self._actsResizeable and self._acts:
            self._acts[0].setMinimumWidth(max(self._xForPercentage(15), 1))
            self._acts[0].setMaximumWidth(self._xForPercentage(30))
            self._acts[2].setMinimumWidth(max(self._xForPercentage(10), 1))
            self._acts[2].setMaximumWidth(self._xForPercentage(30))

    def _rearrangeBeats(self):
        for beat, btn in self._beats.items():
            btn.setGeometry(self._xForPercentage(beat.percentage), self._lineHeight,
                            self._beatHeight,
                            self._beatHeight)
        for beat, btn in self._containers.items():
            x = self._xForPercentage(beat.percentage)
            btn.setGeometry(x + self._beatHeight // 2,
                            self._lineHeight + self._beatHeight + self._containerTopMargin,
                            self._xForPercentage(beat.percentage_end) - x,
                            self._beatHeight)
        self._wdgLine.setGeometry(0, 0, self.width(), self._lineHeight)
        if self.btnCurrentScene:
            self.btnCurrentScene.setGeometry(self.width() * self._currentScenePercentage / 100 - self._lineHeight // 2,
                                             self._lineHeight,
                                             self._beatHeight,
                                             self._beatHeight)

    def _xForPercentage(self, percentage: int) -> int:
        return int(self.width() * percentage / 100 - self._lineHeight // 2)

    def _percentageForX(self, x: int) -> float:
        return (x + self._lineHeight // 2) * 100 / self.width()

    def uncheckActs(self):
        for act in self._acts:
            act.setChecked(False)

    def setActChecked(self, act: int, checked: bool = True):
        self._acts[act - 1].setChecked(checked)

    def setActsClickable(self, clickable: bool):
        self._actsClickable = clickable
        for act in self._acts:
            act.setEnabled(clickable)

    def setActsResizeable(self, enabled: bool):
        self._actsResizeable = enabled
        if self._actsSplitter:
            self._actsSplitter.setEnabled(self._actsResizeable)

    def highlightBeat(self, beat: StoryBeat):
        self.clearHighlights()
        btn = self._beats.get(beat)
        if btn is None:
            return
        btn.setStyleSheet(
            'QToolButton {border: 3px dotted #9b2226; border-radius: 5;} QToolTip {border: 0px;}')
        btn.setFixedSize(self._beatHeight + 6, self._beatHeight + 6)
        qtanim.glow(btn, color=QColor(beat.icon_color))

    def highlightScene(self, scene: Scene):
        if not self.isVisible():
            return
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

    def _actResized(self, pos: int, index: int):
        old_percentage = 0
        new_percentage = 0
        for beat in self._beats.keys():
            if beat.ends_act and beat.act == index:
                old_percentage = beat.percentage
                beat.percentage = self._percentageForX(pos - self._beatHeight // 2)
                new_percentage = beat.percentage
                break

        if new_percentage:
            for con in self._containers:
                if con.percentage == old_percentage:
                    con.percentage = new_percentage
                elif con.percentage_end == old_percentage:
                    con.percentage_end = new_percentage

        self._rearrangeBeats()
        self.actsResized.emit()


class ScenesPreferencesWidget(QWidget, Ui_ScenesViewPreferences):
    def __init__(self, parent=None):
        super(ScenesPreferencesWidget, self).__init__(parent)
        self.setupUi(self)

        self.btnCardsWidth.setIcon(IconRegistry.from_name('ei.resize-horizontal'))

        self.tabWidget.setTabIcon(self.tabWidget.indexOf(self.tabCards), IconRegistry.cards_icon())


class ScenesTreeView(ActionBasedTreeView):

    def __init__(self, parent=None):
        super(ScenesTreeView, self).__init__(parent)
        self.clicked.connect(self._on_chapter_clicked)
        self.repo = RepositoryPersistenceManager.instance()

    @overrides
    def setModel(self, model: ChaptersTreeModel) -> None:
        super(ScenesTreeView, self).setModel(model)
        self.expandAll()
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.setColumnWidth(ChaptersTreeModel.ColPlus, 24)
        model.orderChanged.connect(self._on_scene_moved)
        model.modelReset.connect(self.expandAll)

    def insertChapter(self, index: int = -1):
        self.model().newChapter(index)
        self.repo.update_novel(app_env.novel)
        emit_event(ChapterChangedEvent(self))

    def insertSceneAfter(self, scene: Scene, chapter: Optional[Chapter] = None):
        new_scene = app_env.novel.insert_scene_after(scene, chapter)
        self.model().update()
        self.model().modelReset.emit()
        self.repo.insert_scene(app_env.novel, new_scene)
        emit_event(SceneChangedEvent(self))

    def selectedChapter(self) -> Optional[Chapter]:
        indexes = self.selectionModel().selectedIndexes()
        if indexes:
            node = indexes[0].data(ChaptersTreeModel.NodeRole)
            if isinstance(node, ChapterNode):
                return node.chapter

    def _on_chapter_clicked(self, index: QModelIndex):
        if index.column() == 0:
            return

        indexes = self.selectionModel().selectedIndexes()
        if not indexes:
            return
        node = indexes[0].data(ChaptersTreeModel.NodeRole)

        novel = app_env.novel
        if isinstance(node, ChapterNode):
            builder = PopupMenuBuilder.from_index(self, index)

            scenes = novel.scenes_in_chapter(node.chapter)
            if scenes:
                builder.add_action('Add scene', IconRegistry.scene_icon(), lambda: self.insertSceneAfter(scenes[-1]))
                builder.add_separator()

            builder.add_action('Add chapter before', IconRegistry.chapter_icon(),
                               slot=lambda: self.insertChapter(novel.chapters.index(node.chapter)))
            builder.add_action('Add chapter after', IconRegistry.chapter_icon(),
                               slot=lambda: self.insertChapter(novel.chapters.index(node.chapter) + 1))
            builder.popup()
        elif isinstance(node, SceneNode):
            if node.scene and node.scene.chapter:
                self.insertSceneAfter(node.scene)

    def _on_scene_moved(self):
        self.repo.update_novel(app_env.novel)
        emit_event(SceneChangedEvent(self))


class StoryMapDisplayMode(Enum):
    DOTS = 0
    TITLE = 1
    DETAILED = 2


class StoryLinesMapWidget(QWidget):
    sceneSelected = pyqtSignal(Scene)

    def __init__(self, mode: StoryMapDisplayMode, acts_filter: Dict[int, bool], parent=None):
        super().__init__(parent=parent)
        hbox(self)
        self.setMouseTracking(True)
        self.novel: Optional[Novel] = None
        self._scene_coord_y: Dict[int, int] = {}
        self._clicked_scene: Optional[Scene] = None
        self._display_mode: StoryMapDisplayMode = mode
        self._acts_filter = acts_filter

        if mode == StoryMapDisplayMode.DOTS:
            self._scene_width = 25
            self._top_height = 50
        else:
            self._scene_width = 120
            self._top_height = 50
        self._line_height = 50
        self._first_paint_triggered: bool = False

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu_requested)

    def setNovel(self, novel: Novel, animated: bool = True):
        def changed(x: int):
            self._first_paint_triggered = True
            self.update(0, 0, x, self.minimumSizeHint().height())

        self.novel = novel
        if animated:
            timeline = QTimeLine(700, parent=self)
            timeline.setFrameRange(0, self.minimumSizeHint().width())
            timeline.frameChanged.connect(changed)

            timeline.start()
        else:
            self._first_paint_triggered = True

    def scenes(self) -> List[Scene]:
        return [x for x in self.novel.scenes if self._acts_filter.get(acts_registry.act(x), True)]

    @overrides
    def minimumSizeHint(self) -> QSize:
        if self.novel:
            x = self._scene_x(len(self.scenes()) - 1) + 50
            y = self._story_line_y(len(self.novel.plots)) * 2
            return QSize(x, y)
        return super().minimumSizeHint()

    @overrides
    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.ToolTip:
            index = self._index_from_pos(event.pos())
            scenes = self.scenes()
            if index < len(scenes):
                self.setToolTip(scenes[index].title_or_index(self.novel))

            return super().event(event)
        return super().event(event)

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        index = self._index_from_pos(event.pos())
        scenes = self.scenes()
        if index < len(scenes):
            self._clicked_scene: Scene = scenes[index]
            self.sceneSelected.emit(self._clicked_scene)
            self.update()

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(RELAXED_WHITE_COLOR))

        if not self._first_paint_triggered:
            painter.end()
            return

        scenes = self.scenes()

        self._scene_coord_y.clear()
        y = 0
        last_sc_x: Dict[int, int] = {}
        for sl_i, plot in enumerate(self.novel.plots):
            previous_y = 0
            previous_x = 0
            y = self._story_line_y(sl_i)
            path = QPainterPath()
            painter.setPen(QPen(QColor(plot.icon_color), 4, Qt.SolidLine))
            path.moveTo(0, y)
            painter.drawPixmap(0, y - 35, IconRegistry.from_name(plot.icon, plot.icon_color).pixmap(24, 24))
            path.lineTo(5, y)
            painter.drawPath(path)

            for sc_i, scene in enumerate(scenes):
                x = self._scene_x(sc_i)
                if plot in scene.plots():
                    if sc_i not in self._scene_coord_y.keys():
                        self._scene_coord_y[sc_i] = y
                    if previous_y > self._scene_coord_y[sc_i] or (previous_y == 0 and y > self._scene_coord_y[sc_i]):
                        path.lineTo(x - self._scene_width // 2, y)
                    elif 0 < previous_y < self._scene_coord_y[sc_i]:
                        path.lineTo(previous_x + self._scene_width // 2, y)

                    if previous_y == self._scene_coord_y[sc_i] and previous_y != y:
                        path.arcTo(previous_x + 4, self._scene_coord_y[sc_i] - 3, x - previous_x,
                                   self._scene_coord_y[sc_i] - 25,
                                   -180, 180)
                    else:
                        path.lineTo(x, self._scene_coord_y[sc_i])

                    painter.drawPath(path)
                    previous_y = self._scene_coord_y[sc_i]
                    previous_x = x
                    last_sc_x[sl_i] = x

        for sc_i, scene in enumerate(scenes):
            if sc_i not in self._scene_coord_y.keys():
                continue
            self._draw_scene_ellipse(painter, scene, self._scene_x(sc_i), self._scene_coord_y[sc_i])

        for sc_i, scene in enumerate(scenes):
            if not scene.plots():
                self._draw_scene_ellipse(painter, scene, self._scene_x(sc_i), 3)

        if len(self.novel.plots) <= 1:
            return

        base_y = y
        for sl_i, plot in enumerate(self.novel.plots):
            y = 50 * (sl_i + 1) + 25 + base_y
            painter.setPen(QPen(QColor(plot.icon_color), 4, Qt.SolidLine))
            painter.drawLine(0, y, last_sc_x.get(sl_i, 15), y)
            painter.setPen(QPen(Qt.black, 5, Qt.SolidLine))
            painter.drawPixmap(0, y - 35, IconRegistry.from_name(plot.icon, plot.icon_color).pixmap(24, 24))
            painter.drawText(26, y - 15, plot.text)

            for sc_i, scene in enumerate(scenes):
                if plot in scene.plots():
                    self._draw_scene_ellipse(painter, scene, self._scene_x(sc_i), y)

        painter.end()

    def _draw_scene_ellipse(self, painter: QPainter, scene: Scene, x: int, y: int):
        if scene.plot_values:
            pen = Qt.red if scene is self._clicked_scene else Qt.black
            if len(scene.plot_values) == 1:
                painter.setPen(QPen(pen, 3, Qt.SolidLine))
                painter.setBrush(Qt.black)
                painter.drawEllipse(x, y - 7, 14, 14)
            else:
                painter.setPen(QPen(pen, 3, Qt.SolidLine))
                painter.setBrush(Qt.white)
                painter.drawEllipse(x, y - 10, 20, 20)
        else:
            pen = Qt.red if scene is self._clicked_scene else Qt.gray
            painter.setPen(QPen(pen, 3, Qt.SolidLine))
            painter.setBrush(Qt.gray)
            painter.drawEllipse(x, y, 14, 14)

    def _story_line_y(self, index: int) -> int:
        return self._top_height + self._line_height * (index)

    def _scene_x(self, index: int) -> int:
        return self._scene_width * (index + 1)

    def _index_from_pos(self, pos: QPoint) -> int:
        return int((pos.x() / self._scene_width) - 1)

    def _context_menu_requested(self, pos: QPoint) -> None:
        index = self._index_from_pos(pos)
        scenes = self.scenes()
        if index < len(scenes):
            self._clicked_scene: Scene = scenes[index]
            self.update()

            builder = PopupMenuBuilder.from_widget_position(self, pos)
            if self.novel.plots:
                for plot in self.novel.plots:
                    plot_action = builder.add_action(truncate_string(plot.text, 70),
                                                     IconRegistry.from_name(plot.icon, plot.icon_color),
                                                     slot=partial(self._plot_changed, plot))
                    plot_action.setCheckable(True)
                    if plot in self._clicked_scene.plots():
                        plot_action.setChecked(True)

                builder.popup()

    @busy
    def _plot_changed(self, plot: Plot, checked: bool):
        if checked:
            self._clicked_scene.plot_values.append(ScenePlotReference(plot))
        else:
            to_be_removed = None
            for plot_v in self._clicked_scene.plot_values:
                if plot_v.plot is plot:
                    to_be_removed = plot_v
                    break
            if to_be_removed:
                self._clicked_scene.plot_values.remove(to_be_removed)
        RepositoryPersistenceManager.instance().update_scene(self._clicked_scene)

        self.update()


GRID_ITEM_SIZE: int = 150


class _SceneGridItem(QWidget):
    def __init__(self, novel: Novel, scene: Scene, parent=None):
        super(_SceneGridItem, self).__init__(parent)
        self.novel = novel
        self.scene = scene

        vbox(self)

        btn = WordWrappedPushButton(parent=self)
        btn.setFixedWidth(120)
        btn.setText(scene.title_or_index(self.novel))
        decr_font(btn.label, step=2)
        transparent(btn)

        self.wdgTop = QWidget()
        hbox(self.wdgTop, 0)
        self.wdgTop.layout().addWidget(btn)

        self.textSynopsis = QTextEdit()
        self.textSynopsis.setFontPointSize(btn.label.font().pointSize())
        self.textSynopsis.verticalScrollBar().setVisible(False)
        transparent(self.textSynopsis)
        self.textSynopsis.setAcceptRichText(False)
        self.textSynopsis.setText(self.scene.synopsis)
        self.textSynopsis.textChanged.connect(self._synopsisChanged)

        self.layout().addWidget(self.wdgTop)
        self.layout().addWidget(self.textSynopsis)

        self.repo = RepositoryPersistenceManager.instance()

    def _synopsisChanged(self):
        self.scene.synopsis = self.textSynopsis.toPlainText()
        self.repo.update_scene(self.scene)


class _ScenesLineWidget(QWidget):
    def __init__(self, novel: Novel, parent=None, vertical: bool = False):
        super(_ScenesLineWidget, self).__init__(parent)
        self.novel = novel

        if vertical:
            vbox(self, margin=0)
        else:
            hbox(self, margin=0)

        wdgEmpty = QWidget()
        wdgEmpty.setFixedSize(GRID_ITEM_SIZE, GRID_ITEM_SIZE)
        self.layout().addWidget(wdgEmpty)

        if vertical:
            hmax(self)
            btnScenes = QPushButton()
        else:
            btnScenes = RotatedButton()
            btnScenes.setOrientation(RotatedButtonOrientation.VerticalBottomToTop)
        btnScenes.setText('Scenes')
        transparent(btnScenes)
        italic(btnScenes)
        underline(btnScenes)
        btnScenes.setIcon(IconRegistry.scene_icon())
        self.layout().addWidget(btnScenes)

        for scene in self.novel.scenes:
            wdg = _SceneGridItem(self.novel, scene)
            wdg.setFixedSize(GRID_ITEM_SIZE, GRID_ITEM_SIZE)
            self.layout().addWidget(wdg)

        if vertical:
            self.layout().addWidget(vspacer())
        else:
            self.layout().addWidget(spacer())


class _ScenePlotAssociationsWidget(QWidget):
    LineSize: int = 15

    def __init__(self, novel: Novel, plot: Plot, parent=None, vertical: bool = False):
        super(_ScenePlotAssociationsWidget, self).__init__(parent)
        self.novel = novel
        self.plot = plot

        self.wdgReferences = QWidget()
        line = QPushButton()
        line.setStyleSheet(f'''
                    background-color: {plot.icon_color};
                    border-radius: 6px;
                ''')

        if vertical:
            hbox(self, 0, 0)
            vbox(self.wdgReferences, margin=0)
            btnPlot = RotatedButton()
            btnPlot.setOrientation(RotatedButtonOrientation.VerticalBottomToTop)
            hmax(btnPlot)
            self.layout().addWidget(btnPlot, alignment=Qt.AlignTop)

            line.setFixedWidth(self.LineSize)
            line.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            hmax(self)
        else:
            vbox(self, 0, 0)
            hbox(self.wdgReferences, margin=0)
            btnPlot = QPushButton()
            self.layout().addWidget(btnPlot, alignment=Qt.AlignLeft)

            line.setFixedHeight(self.LineSize)
            line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        btnPlot.setText(self.plot.text)
        if self.plot.icon:
            btnPlot.setIcon(IconRegistry.from_name(self.plot.icon, self.plot.icon_color))
        transparent(btnPlot)

        self.layout().addWidget(line)
        self.layout().addWidget(self.wdgReferences)

        wdgEmpty = QWidget()
        wdgEmpty.setFixedSize(GRID_ITEM_SIZE, GRID_ITEM_SIZE)
        self.wdgReferences.layout().addWidget(wdgEmpty)

        for scene in self.novel.scenes:
            pv = next((x for x in scene.plot_values if x.plot.id == self.plot.id), None)
            if pv:
                wdg = QTextEdit()
                wdg.setText(pv.data.comment)
                wdg.textChanged.connect(partial(self._commentChanged, wdg, scene, pv))
            else:
                wdg = QWidget()

            wdg.setFixedSize(GRID_ITEM_SIZE, GRID_ITEM_SIZE)
            self.wdgReferences.layout().addWidget(wdg)

        if vertical:
            self.wdgReferences.layout().addWidget(vspacer())
        else:
            self.wdgReferences.layout().addWidget(spacer())

        self.setStyleSheet(f'QWidget {{background-color: {RELAXED_WHITE_COLOR};}}')

        self.repo = RepositoryPersistenceManager.instance()

    def _commentChanged(self, editor: QTextEdit, scene: Scene, scenePlotRef: ScenePlotReference):
        scenePlotRef.data.comment = editor.toPlainText()
        self.repo.update_scene(scene)


class StoryMap(QWidget):
    sceneSelected = pyqtSignal(Scene)

    def __init__(self, parent=None):
        super(StoryMap, self).__init__(parent)
        self.novel: Optional[Novel] = None
        self._display_mode: StoryMapDisplayMode = StoryMapDisplayMode.DOTS
        self._orientation: int = Qt.Horizontal
        self._acts_filter: Dict[int, bool] = {}
        vbox(self, spacing=0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setStyleSheet(f'QWidget {{background-color: {RELAXED_WHITE_COLOR};}}')

    def setNovel(self, novel: Novel):
        self.novel = novel
        self.refresh()

    def refresh(self, animated: bool = True):
        if not self.novel:
            return
        clear_layout(self)

        if self._display_mode == StoryMapDisplayMode.DETAILED:
            wdgScenePlotParent = QWidget(self)
            if self._orientation == Qt.Horizontal:
                vbox(wdgScenePlotParent, spacing=0)
            else:
                hbox(wdgScenePlotParent, spacing=0)

            wdgScenes = _ScenesLineWidget(self.novel, vertical=self._orientation == Qt.Vertical)
            wdgScenePlotParent.layout().addWidget(wdgScenes)

            for plot in self.novel.plots:
                wdg = _ScenePlotAssociationsWidget(self.novel, plot, parent=self,
                                                   vertical=self._orientation == Qt.Vertical)
                wdgScenePlotParent.layout().addWidget(wdg)

            if self._orientation == Qt.Horizontal:
                wdgScenePlotParent.layout().addWidget(vspacer())
            else:
                wdgScenePlotParent.layout().addWidget(spacer())
            self.layout().addWidget(wdgScenePlotParent)

        else:
            wdg = StoryLinesMapWidget(self._display_mode, self._acts_filter, parent=self)
            self.layout().addWidget(wdg)
            wdg.setNovel(self.novel, animated=animated)
            if self._display_mode == StoryMapDisplayMode.TITLE:
                titles = QWidget(self)
                titles.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
                titles.setStyleSheet(f'QWidget {{background-color: {RELAXED_WHITE_COLOR};}}')
                hbox(titles, 0, 0)
                margins(titles, left=70)
                self.layout().insertWidget(0, titles)
                for scene in wdg.scenes():
                    btn = WordWrappedPushButton(parent=self)
                    btn.setFixedWidth(120)
                    btn.setText(scene.title_or_index(self.novel))
                    decr_font(btn.label, step=2)
                    transparent(btn)
                    titles.layout().addWidget(btn)
                titles.layout().addWidget(spacer())
            wdg.sceneSelected.connect(self.sceneSelected.emit)

    @busy
    def setMode(self, mode: StoryMapDisplayMode):
        if self._display_mode == mode:
            return
        self._display_mode = mode
        if self.novel:
            self.refresh()

    @busy
    def setOrientation(self, orientation: int):
        self._orientation = orientation
        if self._display_mode != StoryMapDisplayMode.DETAILED:
            return
        if self.novel:
            self.refresh()

    def setActsFilter(self, act: int, filtered: bool):
        self._acts_filter[act] = filtered
        if self.novel:
            self.refresh(animated=False)
