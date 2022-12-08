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
from typing import Dict, Optional, Set, Union
from typing import List

import qtanim
from PyQt6.QtCore import QPoint, QTimeLine, QRectF, QMimeData, QPointF
from PyQt6.QtCore import Qt, QObject, QEvent, QSize, pyqtSignal, QModelIndex
from PyQt6.QtGui import QDragEnterEvent, QResizeEvent, QCursor, QColor, QDropEvent, QMouseEvent, QIcon, \
    QDragMoveEvent, QLinearGradient, QPaintEvent, QPainter, QPen, QPainterPath, QEnterEvent
from PyQt6.QtWidgets import QSizePolicy, QWidget, QFrame, QToolButton, QSplitter, \
    QPushButton, QTreeView, QMenu, QWidgetAction, QTextEdit, QLabel, QTableView, \
    QAbstractItemView, QApplication, QScrollArea
from overrides import overrides
from qthandy import busy, margins, vspacer, btn_popup_menu, bold, incr_font
from qthandy import decr_font, gc, transparent, retain_when_hidden, translucent, underline, flow, \
    clear_layout, hbox, spacer, btn_popup, vbox, italic
from qthandy.filter import InstantTooltipEventFilter, DisabledClickEventFilter, VisibilityToggleEventFilter, \
    OpacityEventFilter, DragEventFilter, DropEventFilter

from src.main.python.plotlyst.common import ACT_ONE_COLOR, ACT_THREE_COLOR, ACT_TWO_COLOR, RELAXED_WHITE_COLOR, \
    emotion_color
from src.main.python.plotlyst.common import truncate_string
from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Scene, Novel, SceneType, \
    SceneStructureItemType, SceneStructureAgenda, SceneStructureItem, SceneOutcome, StoryBeat, Conflict, \
    Character, Plot, ScenePlotReference, Chapter, StoryBeatType, Tag, PlotValue, ScenePlotValueCharge, \
    SceneStage, GoalReference, CharacterGoal, ConflictReference, ReaderPosition, InformationAcquisition, Document, \
    StoryStructure
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import emit_critical, emit_event, Event, EventListener
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import SceneOrderChangedEvent, ChapterChangedEvent
from src.main.python.plotlyst.events import SceneStatusChangedEvent, \
    ActiveSceneStageChanged, AvailableSceneStagesChanged, SceneSelectedEvent, SceneDeletedEvent, \
    SceneChangedEvent
from src.main.python.plotlyst.model.novel import NovelTagsTreeModel, TagNode
from src.main.python.plotlyst.model.scenes_model import ScenesTableModel
from src.main.python.plotlyst.service.cache import acts_registry
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import PopupMenuBuilder, hmax, pointy, action, stretch_col
from src.main.python.plotlyst.view.generated.scene_beat_item_widget_ui import Ui_SceneBeatItemWidget
from src.main.python.plotlyst.view.generated.scene_drive_editor_ui import Ui_SceneDriveTrackingEditor
from src.main.python.plotlyst.view.generated.scene_filter_widget_ui import Ui_SceneFilterWidget
from src.main.python.plotlyst.view.generated.scene_ouctome_selector_ui import Ui_SceneOutcomeSelectorWidget
from src.main.python.plotlyst.view.generated.scene_structure_editor_widget_ui import Ui_SceneStructureWidget
from src.main.python.plotlyst.view.generated.scenes_view_preferences_widget_ui import Ui_ScenesViewPreferences
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.button import WordWrappedPushButton, SecondaryActionToolButton, \
    SecondaryActionPushButton, FadeOutButtonGroup
from src.main.python.plotlyst.view.widget.characters import CharacterConflictSelector, CharacterGoalSelector, \
    CharacterEmotionButton
from src.main.python.plotlyst.view.widget.display import Icon
from src.main.python.plotlyst.view.widget.input import RotatedButtonOrientation, RotatedButton, MenuWithDescription, \
    DocumentTextEditor
from src.main.python.plotlyst.view.widget.labels import SelectionItemLabel, ScenePlotValueLabel, \
    PlotLabel, PlotValueLabel, SceneLabel


class SceneOutcomeSelector(QWidget, Ui_SceneOutcomeSelectorWidget):
    selected = pyqtSignal(SceneOutcome)

    def __init__(self, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneOutcomeSelector, self).__init__(parent)
        self.scene_structure_item = scene_structure_item
        self.setupUi(self)
        self.btnDisaster.setChecked(True)
        self.btnDisaster.setIcon(IconRegistry.disaster_icon(color='grey'))
        self.btnResolution.setIcon(IconRegistry.success_icon(color='grey'))
        self.btnTradeOff.setIcon(IconRegistry.tradeoff_icon(color='grey'))

        self.refresh()

        self.btnGroupOutcome.buttonClicked.connect(self._clicked)

    def refresh(self):
        if self.scene_structure_item.outcome == SceneOutcome.DISASTER:
            self.btnDisaster.setChecked(True)
        elif self.scene_structure_item.outcome == SceneOutcome.RESOLUTION:
            self.btnResolution.setChecked(True)
        elif self.scene_structure_item.outcome == SceneOutcome.TRADE_OFF:
            self.btnTradeOff.setChecked(True)

    def _clicked(self):
        if self.btnDisaster.isChecked():
            self.scene_structure_item.outcome = SceneOutcome.DISASTER
        elif self.btnResolution.isChecked():
            self.scene_structure_item.outcome = SceneOutcome.RESOLUTION
        elif self.btnTradeOff.isChecked():
            self.scene_structure_item.outcome = SceneOutcome.TRADE_OFF

        self.selected.emit(self.scene_structure_item.outcome)


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
        self.layout().addWidget(lbl, alignment=Qt.AlignmentFlag.AlignLeft)
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
        self.btnLinkPlot.setCursor(Qt.CursorShape.PointingHandCursor)
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
            OpacityEventFilter(parent=self.btnLinkPlot, leaveOpacity=0.4 if simplified else 0.7))

        self.selectorWidget = QWidget()
        vbox(self.selectorWidget)
        occupied_plot_ids = [x.plot.id for x in self.scene.plot_values]
        for plot in self.novel.plots:
            if plot.id in occupied_plot_ids:
                continue
            label = PlotLabel(plot)
            label.installEventFilter(OpacityEventFilter(parent=label, leaveOpacity=0.7))
            label.clicked.connect(partial(self._plotSelected, plot))
            self.selectorWidget.layout().addWidget(label)

        btn_popup(self.btnLinkPlot, self.selectorWidget)

    def setPlot(self, plotValue: ScenePlotReference):
        self.plotValue = plotValue
        self.label = ScenePlotValueLabel(plotValue)
        pointy(self.label)
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
        self.btnSelect.setCursor(Qt.CursorShape.PointingHandCursor)

        self._tagsModel = NovelTagsTreeModel(self.novel)
        self._tagsModel.selectionChanged.connect(self._selectionChanged)
        self._treeSelectorView = QTreeView()
        self._treeSelectorView.setCursor(Qt.CursorShape.PointingHandCursor)
        self._treeSelectorView.setModel(self._tagsModel)
        self._treeSelectorView.setHeaderHidden(True)
        self._treeSelectorView.clicked.connect(self._toggle)
        self._treeSelectorView.expandAll()
        self._tagsModel.modelReset.connect(self._treeSelectorView.expandAll)
        btn_popup(self.btnSelect, self._treeSelectorView)

        self.wdgTags = QFrame(self)
        flow(self.wdgTags)
        self.setStyleSheet('#wdgTags {background-color: white;}')

        self.layout().addWidget(group(self.btnSelect, QLabel('Tags:'), margin=0), alignment=Qt.AlignmentFlag.AlignTop)
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


class SceneSelector(SecondaryActionPushButton):
    sceneSelected = pyqtSignal(Scene)

    def __init__(self, novel: Novel, text: str = '', parent=None):
        super(SceneSelector, self).__init__(parent)
        self.novel = novel
        self.setText(text)
        italic(self)
        self.setIcon(IconRegistry.scene_icon())

        self._lstScenes = QTableView()
        self._lstScenes.verticalHeader().setHidden(True)
        self._lstScenes.horizontalHeader().setHidden(True)
        self._lstScenes.verticalHeader().setDefaultSectionSize(20)
        self._lstScenes.horizontalHeader().setDefaultSectionSize(24)
        self._lstScenes.setShowGrid(False)
        self._lstScenes.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._lstScenes.clicked.connect(self._selected)
        pointy(self._lstScenes)
        self.menu = btn_popup(self, self._lstScenes)
        self.menu.aboutToShow.connect(self._beforePopup)

    @busy
    def _beforePopup(self):
        self._scenesModel = ScenesTableModel(self.novel)

        self._lstScenes.setModel(self._scenesModel)
        for col in range(self._scenesModel.columnCount()):
            self._lstScenes.hideColumn(col)
        self._lstScenes.showColumn(ScenesTableModel.ColPov)
        self._lstScenes.showColumn(ScenesTableModel.ColType)
        self._lstScenes.showColumn(ScenesTableModel.ColTitle)
        self._lstScenes.horizontalHeader().swapSections(ScenesTableModel.ColType, ScenesTableModel.ColTitle)

        stretch_col(self._lstScenes, ScenesTableModel.ColTitle)

    def _selected(self, index: QModelIndex):
        scene = index.data(ScenesTableModel.SceneRole)
        self.sceneSelected.emit(scene)
        self.menu.hide()


class SceneLabelLinkWidget(QWidget):
    sceneSelected = pyqtSignal(Scene)

    def __init__(self, novel: Novel, text: str = '', parent=None):
        super(SceneLabelLinkWidget, self).__init__(parent)
        self.novel = novel
        self.scene: Optional[Scene] = None

        self.label: Optional[SceneLabel] = None

        hbox(self)
        self.btnSelect = SceneSelector(self.novel, text, parent=self)
        self.layout().addWidget(self.btnSelect)
        self.btnSelect.sceneSelected.connect(self.sceneSelected.emit)

    def setScene(self, scene: Scene):
        self.scene = scene
        if self.label is None:
            self.label = SceneLabel(self.scene)
            self.layout().addWidget(self.label)
            self.label.clicked.connect(self.btnSelect.menu.show)
        else:
            self.label.setScene(scene)

        self.btnSelect.setHidden(True)


class SceneFilterWidget(QFrame, Ui_SceneFilterWidget):
    def __init__(self, novel: Novel, parent=None):
        super(SceneFilterWidget, self).__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.povFilter.setExclusive(False)
        self.povFilter.setCharacters(self.novel.pov_characters())

        self.tabWidget.setTabIcon(self.tabWidget.indexOf(self.tabPov), IconRegistry.character_icon())


BeatDescriptions = {SceneStructureItemType.BEAT: 'Beat: a new action, reaction, thought, or emotion in this scene',
                    SceneStructureItemType.ACTION: 'The character takes an action to achieve their goal',
                    SceneStructureItemType.CONFLICT: "Conflict arises that hinders the character's goals",
                    SceneStructureItemType.OUTCOME: 'Outcome of the scene, typically ending with disaster',
                    SceneStructureItemType.REACTION: "Initial reaction to a previous scene's outcome",
                    SceneStructureItemType.DILEMMA: 'Dilemma throughout the scene. What to do next?',
                    SceneStructureItemType.DECISION: 'The character makes a decision and might act right away',
                    SceneStructureItemType.HOOK: 'Initial hook of the scene to raise curiosity',
                    SceneStructureItemType.INCITING_INCIDENT: 'An inciting incident that triggers events in this scene',
                    SceneStructureItemType.TICKING_CLOCK: 'Ticking clock is activated to add urgency',
                    SceneStructureItemType.RISING_ACTION: 'Increasing complication throughout the scene',
                    SceneStructureItemType.CRISIS: 'The impossible decision between two equally good or bad outcomes',
                    SceneStructureItemType.EXPOSITION: 'Exposition beat with character or imaginary exposition',
                    }


def beat_icon(beat_type: SceneStructureItemType, resolved: bool = False, trade_off: bool = False) -> QIcon:
    if beat_type == SceneStructureItemType.ACTION:
        return IconRegistry.goal_icon()
    elif beat_type == SceneStructureItemType.CONFLICT:
        return IconRegistry.conflict_icon()
    elif beat_type == SceneStructureItemType.OUTCOME:
        return IconRegistry.action_scene_icon(resolved, trade_off)
    elif beat_type == SceneStructureItemType.REACTION:
        return IconRegistry.reaction_icon()
    elif beat_type == SceneStructureItemType.DILEMMA:
        return IconRegistry.dilemma_icon()
    elif beat_type == SceneStructureItemType.DECISION:
        return IconRegistry.decision_icon()
    elif beat_type == SceneStructureItemType.HOOK:
        return IconRegistry.hook_icon()
    elif beat_type == SceneStructureItemType.INCITING_INCIDENT:
        return IconRegistry.inciting_incident_icon()
    elif beat_type == SceneStructureItemType.TICKING_CLOCK:
        return IconRegistry.ticking_clock_icon()
    elif beat_type == SceneStructureItemType.RISING_ACTION:
        return IconRegistry.rising_action_icon()
    elif beat_type == SceneStructureItemType.CRISIS:
        return IconRegistry.crisis_icon()
    elif beat_type == SceneStructureItemType.EXPOSITION:
        return IconRegistry.exposition_icon()
    elif beat_type == SceneStructureItemType.BEAT:
        return IconRegistry.beat_icon()
    else:
        return IconRegistry.circle_icon()


class _SceneTypeButton(QPushButton):
    def __init__(self, type: SceneType, parent=None):
        super(_SceneTypeButton, self).__init__(parent)
        self.type = type
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

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
        self.installEventFilter(OpacityEventFilter(self, 0.7, 0.5, ignoreCheckedButton=True))
        self.toggled.connect(self._toggled)

    def _toggled(self, toggled: bool):
        translucent(self, 1.0 if toggled else 0.5)
        font = self.font()
        font.setBold(toggled)
        self.setFont(font)


class _SceneBeatPlaceholderButton(QToolButton):
    selected = pyqtSignal(SceneStructureItemType)

    def __init__(self, parent=None):
        super(_SceneBeatPlaceholderButton, self).__init__(parent)
        self.setIcon(IconRegistry.plus_circle_icon('grey'))
        # self.installEventFilter(OpacityEventFilter(parent=self, 0.5, 0.12))
        self.setIconSize(QSize(24, 24))
        transparent(self)
        # self.setStyleSheet('''
        #     QToolButton {
        #         border: 1px hidden black;
        #         border-radius: 19px; padding: 2px;
        #     }
        #     QToolButton:pressed {
        #         border: 1px solid grey;
        #     }
        #     ''')
        pointy(self)
        self.setToolTip('Insert new beat')

        self._menu = MenuWithDescription(self)
        self._addAction('Action', SceneStructureItemType.ACTION, description='')
        self._addAction('Conflict', SceneStructureItemType.CONFLICT, description='')
        self._addAction('Outcome', SceneStructureItemType.OUTCOME, description='')
        self._addAction('Reaction', SceneStructureItemType.REACTION, description='')
        self._addAction('Dilemma', SceneStructureItemType.DILEMMA, description='')
        self._addAction('Decision', SceneStructureItemType.DECISION, description='')
        self._addAction('Hook', SceneStructureItemType.HOOK, description='')
        self._addAction('Inciting incident', SceneStructureItemType.INCITING_INCIDENT,
                        description='')
        self._addAction('Rising action', SceneStructureItemType.RISING_ACTION, description='')
        self._addAction('Ticking clock', SceneStructureItemType.TICKING_CLOCK, description='')
        self._addAction('Crisis', SceneStructureItemType.CRISIS, description='')
        self._addAction('Exposition', SceneStructureItemType.EXPOSITION, description='')
        self._addAction('Beat', SceneStructureItemType.BEAT, description='')

        btn_popup_menu(self, self._menu)

    def _addAction(self, text: str, beat_type: SceneStructureItemType, description: str):
        if not description:
            description = BeatDescriptions[beat_type]
        self._menu.addAction(action(text, beat_icon(beat_type), slot=lambda: self.selected.emit(beat_type)),
                             description)


class SceneStructureItemWidget(QWidget, Ui_SceneBeatItemWidget):
    removed = pyqtSignal(object)
    emotionChanged = pyqtSignal()

    SceneBeatMimeType: str = 'application/scene-beat'

    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneStructureItemWidget, self).__init__(parent)
        self.novel = novel
        self.beat = scene_structure_item
        self.setupUi(self)
        self._outcome = SceneOutcomeSelector(self.beat)
        self._outcome.selected.connect(self._outcomeChanged)
        self.wdgBottom.layout().addWidget(self._outcome, alignment=Qt.AlignmentFlag.AlignCenter)

        self.btnIcon = QToolButton(self)
        self.btnIcon.setIconSize(QSize(24, 24))
        self.btnIcon.installEventFilter(OpacityEventFilter(parent=self.btnIcon, enterOpacity=0.9, leaveOpacity=1.0))
        pointy(self.btnIcon)

        bold(self.btnName)

        decr_font(self.text)
        self.text.setText(self.beat.text)

        self._initStyle()

        self.btnDelete.clicked.connect(self._remove)
        self.installEventFilter(VisibilityToggleEventFilter(self.btnDelete, parent=self))
        self.btnDrag.installEventFilter(DragEventFilter(self, self.SceneBeatMimeType, self._beatDataFunc,
                                                        grabbed=self.btnIcon, hideTarget=True))
        self.installEventFilter(VisibilityToggleEventFilter(self.btnDrag, parent=self))
        retain_when_hidden(self.btnDelete)
        retain_when_hidden(self.btnDrag)

    def outcomeVisible(self) -> bool:
        return self._outcome.isVisible()

    def sceneStructureItem(self) -> SceneStructureItem:
        self.beat.text = self.text.toPlainText()
        return self.beat

    def activate(self):
        self.text.setFocus()

    def swap(self, beatType: SceneStructureItemType):
        if self.beat.type != beatType:
            self.beat.type = beatType
            if self.beat.type == SceneStructureItemType.OUTCOME:
                if self.beat.outcome is None:
                    self.beat.outcome = SceneOutcome.DISASTER
                self._outcome.refresh()
            self._initStyle()
        self._glow()

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.btnIcon.setGeometry(self.width() // 2 - 18, 0, 36, 36)

    def _beatDataFunc(self, btn):
        return id(self)

    def _initStyle(self):
        self._outcome.setVisible(self.beat.type == SceneStructureItemType.OUTCOME)
        desc = BeatDescriptions[self.beat.type]
        self.text.setPlaceholderText(desc)
        self.btnName.setToolTip(desc)
        self.text.setToolTip(desc)
        self.btnIcon.setToolTip(desc)
        if self.beat.type == SceneStructureItemType.OUTCOME:
            name = SceneOutcome.to_str(self.beat.outcome)
        else:
            name = self.beat.type.name
        self.btnName.setText(name.lower().capitalize().replace('_', ' '))
        self.btnIcon.setIcon(beat_icon(self.beat.type, resolved=self.beat.outcome == SceneOutcome.RESOLUTION,
                                       trade_off=self.beat.outcome == SceneOutcome.TRADE_OFF))

        color = self._color()
        self.btnIcon.setStyleSheet(f'''
                    QToolButton {{
                                    background-color: white;
                                    border: 2px solid {color};
                                    border-radius: 18px; padding: 4px;
                                }}
                    QToolButton:pressed {{
                        border: 2px solid white;
                    }}
                    ''')
        self.btnName.setStyleSheet(f'QPushButton {{border: 0px; background-color: rgba(0, 0, 0, 0); color: {color};}}')
        self.text.setStyleSheet(f'''
                    border: 2px solid {color};
                    border-radius: 3px;
                    ''')

    def _color(self) -> str:
        if self.beat.type == SceneStructureItemType.ACTION:
            return 'darkBlue'
        elif self.beat.type == SceneStructureItemType.CONFLICT:
            return '#f3a712'
        elif self.beat.type == SceneStructureItemType.OUTCOME:
            if self.beat.outcome == SceneOutcome.TRADE_OFF:
                return '#832161'
            elif self.beat.outcome == SceneOutcome.RESOLUTION:
                return '#0b6e4f'
            else:
                return '#fe4a49'
        elif self.beat.type == SceneStructureItemType.DECISION:
            return '#3cdbd3'
        elif self.beat.type == SceneStructureItemType.HOOK:
            return '#829399'
        elif self.beat.type == SceneStructureItemType.INCITING_INCIDENT:
            return '#a2ad59'
        elif self.beat.type == SceneStructureItemType.TICKING_CLOCK:
            return '#f7cb15'
        elif self.beat.type == SceneStructureItemType.RISING_ACTION:
            return '#08605f'
        elif self.beat.type == SceneStructureItemType.CRISIS:
            return '#ce2d4f'
        elif self.beat.type == SceneStructureItemType.EXPOSITION:
            return '#1ea896'
        else:
            return 'black'

    def _remove(self):
        if self.parent():
            anim = qtanim.fade_out(self, duration=150)
            anim.finished.connect(lambda: self.removed.emit(self))

    def _outcomeChanged(self):
        self._initStyle()
        self._glow()

    def _glow(self):
        color = QColor(self._color())
        qtanim.glow(self.btnName, color=color)
        qtanim.glow(self.text, color=color)


class SceneStructureTimeline(QWidget):
    emotionChanged = pyqtSignal()
    timelineChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(SceneStructureTimeline, self).__init__(parent)
        self.novel = app_env.novel
        self._margin = 80
        self._lineDistance = 140
        self._arcWidth = 80
        self._beatWidth: int = 180
        self._emotionSize: int = 32
        self._path: Optional[QPainterPath] = None
        self._agenda: Optional[SceneStructureAgenda] = None
        self._beatWidgets: List[SceneStructureItemWidget] = []
        self._placeholder = _SceneBeatPlaceholderButton(self)
        self._placeholder.setVisible(False)
        self._placeholder.menu().aboutToHide.connect(lambda: self._placeholder.setVisible(False))
        self._placeholder.selected.connect(self._insertBeatWidget)
        self._emotionStart = CharacterEmotionButton(self)
        self._emotionStart.setVisible(False)
        self._emotionStart.emotionChanged.connect(self._emotionChanged)
        self._emotionEnd = CharacterEmotionButton(self)
        self._emotionEnd.setVisible(False)
        self._emotionEnd.emotionChanged.connect(self._emotionChanged)

        self.setMouseTracking(True)
        self.setAcceptDrops(True)

    def setAgenda(self, agenda: SceneStructureAgenda, sceneTyoe: SceneType):
        self.reset()

        self._agenda = agenda
        for item in agenda.items:
            self._addBeatWidget(item)
        self._emotionStart.setValue(agenda.beginning_emotion)
        self._emotionStart.setVisible(True)
        self._emotionEnd.setValue(agenda.ending_emotion)
        self._emotionEnd.setVisible(True)

        if not agenda.items:
            self._initBeatsFromType(sceneTyoe)

        for i in range(1, len(agenda.items) - 1):
            beat = agenda.items[i]
            if beat.percentage == 0.0:
                beat.percentage = i * (0.9 / (len(agenda.items) - 1))
        last_beat = agenda.items[-1]
        if last_beat.percentage == 0.0:
            last_beat.percentage = 0.9

        self._rearrangeBeats()

    def setSceneType(self, sceneTyoe: SceneType):
        if not self._beatWidgets:
            self._initBeatsFromType(sceneTyoe)
            return

        if len(self._beatWidgets) < 3:
            for _ in range(3 - len(self._beatWidgets)):
                self._addBeat(SceneStructureItemType.BEAT)

        if sceneTyoe == SceneType.ACTION:
            self._beatWidgets[0].swap(SceneStructureItemType.ACTION)
            self._beatWidgets[1].swap(SceneStructureItemType.CONFLICT)
            self._beatWidgets[-1].swap(SceneStructureItemType.OUTCOME)
        elif sceneTyoe == SceneType.REACTION:
            self._beatWidgets[0].swap(SceneStructureItemType.REACTION)
            self._beatWidgets[1].swap(SceneStructureItemType.DILEMMA)
            self._beatWidgets[-1].swap(SceneStructureItemType.DECISION)
        else:
            self._beatWidgets[0].swap(SceneStructureItemType.BEAT)
            self._beatWidgets[1].swap(SceneStructureItemType.BEAT)
            self._beatWidgets[-1].swap(SceneStructureItemType.BEAT)

    def agendaItems(self) -> List[SceneStructureItem]:
        return [x.sceneStructureItem() for x in self._beatWidgets]

    def reset(self):
        clear_layout(self)
        self._beatWidgets.clear()

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        width = event.rect().width()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(0.5)

        first_el = self._path.elementAt(0)
        last_el = self._path.elementAt(self._path.elementCount() - 1)

        if self._curves():
            gradient = QLinearGradient(width // 2, 0, width // 2, last_el.y)
        else:
            gradient = QLinearGradient(0, first_el.y, last_el.x, last_el.y)
        gradient.setColorAt(0, QColor(emotion_color(self._agenda.beginning_emotion)))
        gradient.setColorAt(1, QColor(emotion_color(self._agenda.ending_emotion)))
        pen = QPen(gradient, 10, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        path = QPainterPath()

        path.moveTo(0, first_el.y)
        path.lineTo(first_el.x, first_el.y)
        if self._path:
            path.connectPath(self._path)
            pos = path.currentPosition()
            path.lineTo(width - 10, pos.y())
        painter.fillRect(self.rect(), QColor(RELAXED_WHITE_COLOR))
        painter.drawPath(path)

        painter.end()

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        self._rearrangeBeats()

    @overrides
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(SceneStructureItemWidget.SceneBeatMimeType):
            event.accept()
        else:
            event.ignore()

    @overrides
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasFormat(SceneStructureItemWidget.SceneBeatMimeType) and self._intersects(
                event.position()):
            event.accept()
        else:
            event.ignore()

    @overrides
    def dropEvent(self, event: QDropEvent) -> None:
        id_ = pickle.loads(event.mimeData().data(SceneStructureItemWidget.SceneBeatMimeType))

        for wdg in self._beatWidgets:
            if id(wdg) == id_:
                wdg.beat.percentage = self._percentage(event.position())
                break

        sorted(self._agenda.items, key=lambda x: x.percentage)
        sorted(self._beatWidgets, key=lambda x: x.beat.percentage)

        event.accept()

        self._rearrangeBeats()
        self.update()

    @overrides
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._contains(event.pos()) and self._intersects(event.pos()):
            if not QApplication.overrideCursor():
                QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)
            self._placeholder.setVisible(True)
            self._placeholder.setGeometry(event.pos().x() - 12, event.pos().y() - 12, 24, 24)
            self.update()
            return

        if QApplication.overrideCursor():
            self._placeholder.setVisible(False)
            self.update()
            QApplication.restoreOverrideCursor()

    def _contains(self, pos: QPoint) -> bool:
        if not self._path:
            return False
        return self._path.intersects(QRectF(pos.x(), pos.y(), 1, 1))

    def _intersects(self, pos: QPoint) -> bool:
        for i in range(self._path.elementCount()):
            el = self._path.elementAt(i)
            if el.y - 10 < pos.y() < el.y + 10:
                if el.isLineTo():
                    return True
        return False

    def _percentage(self, pos: QPoint) -> float:
        length = 0
        for i in range(self._path.elementCount()):
            el = self._path.elementAt(i)
            if i > 0:
                prev_el = self._path.elementAt(i - 1)
                if prev_el.y == el.y:
                    length += abs(el.x - prev_el.x)
                elif prev_el.isCurveTo():
                    length += self._lineDistance / 2
            if el.y - 10 < pos.y() < el.y + 10:
                if pos.x() <= el.x:
                    length += abs(el.x - pos.x())
                if pos.x() >= el.x:
                    length += abs(pos.x() - el.x)

                return self._path.percentAtLength(length)

        return -1

    def _curves(self) -> int:
        if not self.width():
            return 0
        w = self.width() - self._margin * 2
        return max(sum([x.maximumWidth() for x in self._beatWidgets]) // w, 0)

    def _drawLine(self, path: QPainterPath, width: int, y: int, forward: bool):
        if forward:
            path.lineTo(width - self._margin - self._arcWidth, y)
        else:
            path.lineTo(self._margin + self._arcWidth + 5, y)

    def _drawArc(self, path: QPainterPath, width: int, y: int, forward: bool):
        if forward:
            path.arcTo(QRectF(width - self._margin - self._arcWidth, y, self._arcWidth, self._lineDistance), 90, -180)
        else:
            path.arcTo(QRectF(self._margin, y, self._arcWidth, self._lineDistance), -270, 180)

    def _rearrangeBeats(self):
        width = self.width()
        if not width:
            return
        trackedPath = QPainterPath()

        y = 20
        trackedPath.moveTo(self._margin + self._beatWidth // 2, y)
        trackedPath.lineTo(width - self._margin - self._arcWidth // 2 - 5, y)
        curves = self._curves()
        for i in range(curves):
            if i > 0:
                self._drawLine(trackedPath, width, y, True)
            self._drawArc(trackedPath, width, y, True)
            y += self._lineDistance
            self._drawLine(trackedPath, width, y, False)
            self._drawArc(trackedPath, width, y, False)
            y += self._lineDistance
        trackedPath.lineTo(width - 10 - self._margin, y)

        self._path = trackedPath

        for i in range(len(self._beatWidgets)):
            wdg = self._beatWidgets[i]
            point = self._path.pointAtPercent(wdg.beat.percentage)
            wdg.setGeometry(point.x() - wdg.minimumWidth() // 2, point.y() - 15, wdg.minimumWidth(),
                            wdg.minimumHeight())

        self._emotionStart.setGeometry(10, 25, self._emotionSize, self._emotionSize)
        self._emotionEnd.setGeometry(width - 30, y + 5, self._emotionSize, self._emotionSize)
        self.setMinimumHeight(y + 150)

    def _addBeat(self, beatType: SceneStructureItemType):
        item = SceneStructureItem(beatType)
        if beatType == SceneStructureItemType.OUTCOME:
            item.outcome = SceneOutcome.DISASTER
        self._agenda.items.append(item)
        self._addBeatWidget(item)

    def _addBeatWidget(self, item: SceneStructureItem):
        widget = self._newBeatWidget(item)
        self._beatWidgets.append(widget)
        widget.setVisible(True)
        self.timelineChanged.emit()

    def _insertBeatWidget(self, beatType: SceneStructureItemType):
        self._placeholder.setVisible(False)

        item = SceneStructureItem(beatType)
        perc = self._percentage(self._placeholder.geometry().center())
        item.percentage = perc
        widget = self._newBeatWidget(item)

        pos = 0
        for i, item_ in enumerate(self._agenda.items):
            if item_.percentage > perc:
                pos = i
                break
        self._agenda.items.insert(pos, item)
        self._beatWidgets.insert(pos, widget)
        widget.setVisible(True)
        widget.activate()
        self._rearrangeBeats()
        self.update()
        self.timelineChanged.emit()

    def _newBeatWidget(self, item: SceneStructureItem) -> SceneStructureItemWidget:
        widget = SceneStructureItemWidget(self.novel, item, parent=self)
        widget.removed.connect(self._beatRemoved)
        widget.emotionChanged.connect(self.emotionChanged.emit)

        return widget

    def _initBeatsFromType(self, sceneTyoe: SceneType):
        if sceneTyoe == SceneType.ACTION:
            self._addBeat(SceneStructureItemType.ACTION)
            self._addBeat(SceneStructureItemType.CONFLICT)
            self._addBeat(SceneStructureItemType.OUTCOME)
        elif sceneTyoe == SceneType.REACTION:
            self._addBeat(SceneStructureItemType.REACTION)
            self._addBeat(SceneStructureItemType.DILEMMA)
            self._addBeat(SceneStructureItemType.DECISION)
        else:
            self._addBeat(SceneStructureItemType.BEAT)
            self._addBeat(SceneStructureItemType.BEAT)
            self._addBeat(SceneStructureItemType.BEAT)

    def _emotionChanged(self):
        self._agenda.beginning_emotion = self._emotionStart.value()
        self._agenda.ending_emotion = self._emotionEnd.value()

        self.update()

    def _beatRemoved(self, wdg: SceneStructureItemWidget):
        self._agenda.items.remove(wdg.beat)
        self._beatWidgets.remove(wdg)
        gc(wdg)
        self._rearrangeBeats()
        self.update()

        self.timelineChanged.emit()


class SceneStructureWidget(QWidget, Ui_SceneStructureWidget):

    def __init__(self, parent=None):
        super(SceneStructureWidget, self).__init__(parent)
        self.setupUi(self)

        self.novel: Optional[Novel] = None
        self.scene: Optional[Scene] = None

        self.btnScene = _SceneTypeButton(SceneType.ACTION)
        self.btnSequel = _SceneTypeButton(SceneType.REACTION)

        self.wdgTypes.layout().addWidget(self.btnScene)
        self.wdgTypes.layout().addWidget(self.btnSequel)

        flow(self.wdgGoalConflictContainer)

        self.timeline = SceneStructureTimeline(self)
        self.timeline.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scrollAreaWidgetContents.layout().addWidget(self.timeline)

        self.btnScene.installEventFilter(OpacityEventFilter(parent=self.btnScene, ignoreCheckedButton=True))
        self.btnSequel.installEventFilter(OpacityEventFilter(parent=self.btnSequel, ignoreCheckedButton=True))
        self.btnScene.clicked.connect(partial(self._typeClicked, SceneType.ACTION))
        self.btnSequel.clicked.connect(partial(self._typeClicked, SceneType.REACTION))

        self.wdgAgendaCharacter.setDefaultText('Select character')
        self.wdgAgendaCharacter.characterSelected.connect(self._agendaCharacterSelected)
        self.unsetCharacterSlot = None

    def setUnsetCharacterSlot(self, unsetCharacterSlot):
        self.unsetCharacterSlot = unsetCharacterSlot

    def setScene(self, novel: Novel, scene: Scene):
        self.novel = novel
        self.scene = scene

        self.updateAvailableAgendaCharacters()
        self._toggleCharacterStatus()

        self.timeline.reset()
        self._initSelectors()

        self._checkSceneType()

        self.timeline.setAgenda(scene.agendas[0], self.scene.type)

    def updateAvailableAgendaCharacters(self):
        chars = []
        chars.extend(self.scene.characters)
        if self.scene.pov:
            chars.insert(0, self.scene.pov)
        self.wdgAgendaCharacter.setAvailableCharacters(chars)

    def updateAgendaCharacter(self):
        self._toggleCharacterStatus()
        self._initSelectors()

    def updateAgendas(self):
        if not self.scene.agendas:
            return
        self.scene.agendas[0].items.clear()
        self.scene.agendas[0].items.extend(self.timeline.agendaItems())
        # self.scene.agendas[0].beginning_emotion = self.btnEmotionStart.value()
        # self.scene.agendas[0].ending_emotion = self.btnEmotionEnd.value()

    def _toggleCharacterStatus(self):
        if self.scene.agendas[0].character_id:
            self.wdgAgendaCharacter.setEnabled(True)
            char = self.scene.agendas[0].character(self.novel)
            if char:
                self.wdgAgendaCharacter.setCharacter(char)
        else:
            self.wdgAgendaCharacter.btnLinkCharacter.installEventFilter(
                DisabledClickEventFilter(self, self.unsetCharacterSlot))

            self.wdgAgendaCharacter.setDisabled(True)
            self.wdgAgendaCharacter.setToolTip('Select POV character first')

    def _agendaCharacterSelected(self, character: Character):
        self.scene.agendas[0].set_character(character)
        self.scene.agendas[0].conflict_references.clear()
        self.updateAgendaCharacter()

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

    def _typeClicked(self, type: SceneType, checked: bool, lazy: bool = True):
        if lazy and type == self.scene.type and checked:
            return

        if type == SceneType.ACTION and checked:
            self.scene.type = type
            self.btnSequel.setChecked(False)
            qtanim.fade_out(self.btnSequel)
        elif type == SceneType.REACTION and checked:
            self.scene.type = type
            self.btnScene.setChecked(False)
            qtanim.fade_out(self.btnScene)
        else:
            self.scene.type = SceneType.DEFAULT
            # top = SceneStructureItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.BEAT),
            #                                placeholder='Describe the beginning event')
            # middle = SceneStructureItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.BEAT),
            #                                   placeholder='Describe the middle part of this scene')
            # bottom = SceneStructureItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.BEAT),
            #                                   placeholder='Describe the ending of this scene')
            if self.btnScene.isHidden():
                qtanim.fade_in(self.btnScene)
            if self.btnSequel.isHidden():
                qtanim.fade_in(self.btnSequel)

        self.timeline.setSceneType(self.scene.type)

    def _initSelectors(self):
        if not self.scene.agendas[0].character_id:
            return
        clear_layout(self.wdgGoalConflictContainer)
        if self.scene.agendas[0].goal_references:
            for goal_ref in self.scene.agendas[0].goal_references:
                goal = goal_ref.goal(self.scene.agendas[0].character(self.novel))
                if goal:
                    self._addGoalSelector(goal, goal_ref)
            self._addGoalSelector()
        else:
            self._addGoalSelector()

        if self.scene.agendas[0].conflict_references:
            for conflict_ref in self.scene.agendas[0].conflict_references:
                conflict = conflict_ref.conflict(self.novel)
                if conflict:
                    self._addConfictSelector(conflict, conflict_ref)

            # for conflict in self.scene.agendas[0].conflicts(self.novel):
            #     self._addConfictSelector(conflict=conflict)
            self._addConfictSelector()
        else:
            self._addConfictSelector()

    def _addGoalSelector(self, goal: Optional[CharacterGoal] = None, goalRef: Optional[GoalReference] = None):
        simplified = len(self.scene.agendas[0].goal_references) > 0
        selector = CharacterGoalSelector(self.novel, self.scene, simplified=simplified)
        self.wdgGoalConflictContainer.layout().addWidget(selector)
        selector.goalSelected.connect(self._initSelectors)
        if goal and goalRef:
            selector.setGoal(goal, goalRef)

    def _addConfictSelector(self, conflict: Optional[Conflict] = None,
                            conflict_ref: Optional[ConflictReference] = None):
        simplified = len(self.scene.agendas[0].conflict_references) > 0
        conflict_selector = CharacterConflictSelector(self.novel, self.scene, simplified=simplified,
                                                      parent=self.wdgGoalConflictContainer)
        if conflict and conflict_ref:
            conflict_selector.setConflict(conflict, conflict_ref)
        self.wdgGoalConflictContainer.layout().addWidget(conflict_selector)
        conflict_selector.conflictSelected.connect(self._initSelectors)


class SceneStoryStructureWidget(QWidget):
    BeatMimeType = 'application/story-beat'

    beatSelected = pyqtSignal(StoryBeat)
    beatRemovalRequested = pyqtSignal(StoryBeat)
    actsResized = pyqtSignal()
    beatMoved = pyqtSignal(StoryBeat)

    def __init__(self, parent=None):
        super(SceneStoryStructureWidget, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self._checkOccupiedBeats: bool = True
        self._beatsCheckable: bool = False
        self._beatsMoveable: bool = False
        self._removalContextMenuEnabled: bool = False
        self._actsClickable: bool = False
        self._actsResizeable: bool = False
        self._beatCursor = Qt.CursorShape.PointingHandCursor
        self.novel: Optional[Novel] = None
        self.structure: Optional[StoryStructure] = None
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

    def setBeatsMoveable(self, enabled: bool):
        self._beatsMoveable = enabled
        self.setAcceptDrops(enabled)

    def setRemovalContextMenuEnabled(self, value: bool):
        self._removalContextMenuEnabled = value

    def beatCursor(self) -> int:
        return self._beatCursor

    def setBeatCursor(self, value: int):
        self._beatCursor = value

    def setStructure(self, novel: Novel, structure: Optional[StoryStructure] = None):
        def _beat(beat, btn):
            return beat

        self.novel = novel
        self.structure = structure if structure else novel.active_story_structure
        self._acts.clear()
        self._beats.clear()

        occupied_beats = acts_registry.occupied_beats()
        for beat in self.structure.beats:
            if beat.type == StoryBeatType.CONTAINER:
                btn = QPushButton(self)
                if beat.percentage_end - beat.percentage > 7:
                    btn.setText(beat.text)
                self._containers[beat] = btn
                btn.setStyleSheet(f'''
                    QPushButton {{border-top:2px dashed {beat.icon_color}; color: {beat.icon_color};}}
                ''')
                italic(btn)
                translucent(btn)
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
                if self._beatsMoveable and not beat.ends_act and not beat.text == 'Midpoint':
                    btn.installEventFilter(
                        DragEventFilter(btn, self.BeatMimeType, partial(_beat, beat), hideTarget=True))
                    btn.setCursor(Qt.CursorShape.OpenHandCursor)
                else:
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

        beats = self.structure.act_beats()
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
            if event.type() == QEvent.Type.Enter:
                translucent(watched)
            elif event.type() == QEvent.Type.Leave:
                translucent(watched, 0.2)
        return super(SceneStoryStructureWidget, self).eventFilter(watched, event)

    @overrides
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat(self.BeatMimeType):
            event.accept()
        else:
            event.ignore()

    @overrides
    def dropEvent(self, event: QDropEvent) -> None:
        dropped_beat: StoryBeat = pickle.loads(event.mimeData().data(self.BeatMimeType))

        for beat in self._beats.keys():
            if beat == dropped_beat:
                beat.percentage = self._percentageForX(event.position().x() - self._beatHeight // 2)
                self._rearrangeBeats()
                event.accept()
                self.beatMoved.emit(beat)
                break

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
            for _scene in reversed(self.novel.scenes[0: index]):
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
            max_percentage = next_beat.percentage if next_beat else 99
            min_index = self.novel.scenes.index(previous_beat_scene) if previous_beat_scene else 0
            max_index = self.novel.scenes.index(next_beat_scene) if next_beat_scene else len(self.novel.scenes) - 1

            self._currentScenePercentage = min_percentage + (max_percentage - min_percentage) / (
                    max_index - min_index) * (index - min_index)

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
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        act.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        act.setFixedHeight(self._lineHeight)
        act.setCursor(Qt.CursorShape.PointingHandCursor)
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
        translucent(btn, 1.0 if toggled else 0.2)

    def _beatToggled(self, btn: QToolButton, toggled: bool):
        translucent(btn, 1.0 if toggled else 0.2)

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


class SceneWidget(QFrame):
    selectionChanged = pyqtSignal(bool)

    def __init__(self, scene: Scene, novel: Novel, animation: bool = True, parent=None):
        super(SceneWidget, self).__init__(parent)
        self._scene = scene
        self._novel = novel
        self._animation = animation
        hbox(self)

        self._selected: bool = False

        self._scenePovIcon = Icon(self)
        retain_when_hidden(self._scenePovIcon)
        self._sceneTypeIcon = Icon(self)
        self._lblTitle = QLabel(self)
        self._lblTitle.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.layout().addWidget(self._scenePovIcon)
        self.layout().addWidget(self._sceneTypeIcon)
        self.layout().addWidget(self._lblTitle)

        self.refresh()
        self._reStyle()

    def scene(self) -> Scene:
        return self._scene

    def novel(self) -> Novel:
        return self._novel

    def refresh(self):
        if self._scene.type != SceneType.DEFAULT:
            self._sceneTypeIcon.setIcon(IconRegistry.scene_type_icon(self._scene))
        self._sceneTypeIcon.setVisible(self._scene.type != SceneType.DEFAULT)

        if self._scene.pov:
            avatar = avatars.avatar(self._scene.pov, fallback=False)
            if avatar:
                self._scenePovIcon.setIcon(avatar)
        else:
            avatar = None
        self._scenePovIcon.setVisible(avatar is not None)

        self._lblTitle.setText(self._scene.title_or_index(self._novel))

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._toggleSelection(not self._selected)
        self.selectionChanged.emit(self._selected)

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        if self._animation:
            qtanim.glow(self, radius=4, duration=100, color=Qt.GlobalColor.lightGray)

    def select(self):
        self._toggleSelection(True)

    def deselect(self):
        self._toggleSelection(False)

    def _toggleSelection(self, selected: bool):
        self._selected = selected
        bold(self._lblTitle, self._selected)
        self._reStyle()

    def _reStyle(self):
        if self._selected:
            self.setStyleSheet('''
                SceneWidget {
                    background-color: #D8D5D5;
                }
            ''')
        else:
            self.setStyleSheet('')


class ChapterWidget(QWidget):
    selectionChanged = pyqtSignal(bool)
    deleted = pyqtSignal()

    def __init__(self, chapter: Chapter, novel: Novel, parent=None):
        super(ChapterWidget, self).__init__(parent)
        self._chapter = chapter
        self._novel = novel
        vbox(self)

        self._wdgTitle = QWidget(self)
        hbox(self._wdgTitle, 0, 2)

        self._selected: bool = False
        self._chapterIcon = Icon(self._wdgTitle)
        self._chapterIcon.setIcon(IconRegistry.chapter_icon())
        self._btnSettings = QToolButton(self._wdgTitle)
        self._btnSettings.setIcon(IconRegistry.dots_icon(vertical=True))
        self._btnSettings.setProperty('transparent', True)
        menu = QMenu(self._btnSettings)
        menu.addAction(IconRegistry.trash_can_icon(), 'Delete', self.deleted.emit)
        btn_popup_menu(self._btnSettings, menu)
        self._lblTitle = QLabel(self._wdgTitle)
        self.refresh()
        self._wdgTitle.layout().addWidget(self._chapterIcon)
        self._wdgTitle.layout().addWidget(self._lblTitle)
        self._wdgTitle.layout().addWidget(self._btnSettings, alignment=Qt.AlignmentFlag.AlignRight)
        self._wdgTitle.installEventFilter(self)
        self._wdgTitle.installEventFilter(VisibilityToggleEventFilter(self._btnSettings, self._wdgTitle))

        self._scenesContainer = QWidget(self)
        vbox(self._scenesContainer)
        margins(self._scenesContainer, left=10)
        self.layout().addWidget(self._wdgTitle)
        self.layout().addWidget(self._scenesContainer)

        self._reStyle()

    def refresh(self):
        self._lblTitle.setText(self._chapter.title_index(self._novel))

    def chapter(self) -> Chapter:
        return self._chapter

    def novel(self) -> Novel:
        return self._novel

    def containerWidget(self) -> QWidget:
        return self._scenesContainer

    def titleWidget(self) -> QWidget:
        return self._wdgTitle

    def sceneWidgets(self) -> List[SceneWidget]:
        scenes_ = []
        for i in range(self._scenesContainer.layout().count()):
            item = self._scenesContainer.layout().itemAt(i)
            if item is None:
                continue
            if isinstance(item.widget(), SceneWidget):
                scenes_.append(item.widget())

        return scenes_

    def addSceneWidget(self, wdg: SceneWidget):
        self._scenesContainer.layout().addWidget(wdg)

    def insertSceneWidget(self, i: int, wdg: SceneWidget):
        self._scenesContainer.layout().insertWidget(i, wdg)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            qtanim.glow(self._wdgTitle, radius=4, duration=100, color=Qt.GlobalColor.lightGray)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self._toggleSelection(not self._selected)
            self.selectionChanged.emit(self._selected)
        return super(ChapterWidget, self).eventFilter(watched, event)

    def select(self):
        self._toggleSelection(True)

    def deselect(self):
        self._toggleSelection(False)

    def _toggleSelection(self, selected: bool):
        self._selected = selected
        bold(self._lblTitle, self._selected)
        self._reStyle()

    def _reStyle(self):
        if self._selected:
            self._wdgTitle.setStyleSheet('''
                QWidget {
                    background-color: #D8D5D5;
                }
            ''')
        else:
            self._wdgTitle.setStyleSheet('')


class ScenesTreeView(QScrollArea, EventListener):
    SCENE_MIME_TYPE = 'application/tree-scene-widget'
    CHAPTER_MIME_TYPE = 'application/tree-chapter-widget'
    sceneSelected = pyqtSignal(Scene)
    chapterSelected = pyqtSignal(Chapter)

    # noinspection PyTypeChecker
    def __init__(self, parent=None):
        super(ScenesTreeView, self).__init__(parent)
        self._novel: Optional[Novel] = None
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._centralWidget = QWidget(self)
        self.setWidget(self._centralWidget)
        vbox(self._centralWidget, spacing=0)
        # self.clicked.connect(self._on_chapter_clicked)

        self._chapters: Dict[Chapter, ChapterWidget] = {}
        self._scenes: Dict[Scene, SceneWidget] = {}
        self._selectedScenes: Set[Scene] = set()
        self._selectedChapters: Set[Chapter] = set()
        self.setStyleSheet('ScenesTreeView {background-color: rgb(244, 244, 244);}')

        self._dummyWdg: Optional[Union[SceneWidget, ChapterWidget]] = None
        self._toBeRemoved: Optional[Union[SceneWidget, ChapterWidget]] = None
        self._spacer: QWidget = vspacer()
        vbox(self._spacer)
        self._spacer.setAcceptDrops(True)
        self._spacer.installEventFilter(
            DropEventFilter(self, [self.SCENE_MIME_TYPE, self.CHAPTER_MIME_TYPE], enteredSlot=self._dragEnteredForEnd,
                            leftSlot=self._dragLeftFromEnd, droppedSlot=self._drop))

        self._centralWidget.setAcceptDrops(True)
        self._centralWidget.installEventFilter(DropEventFilter(self, [self.SCENE_MIME_TYPE, self.CHAPTER_MIME_TYPE],
                                                               leftSlot=lambda: self._dummyWdg.setHidden(True)))

        event_dispatcher.register(self, SceneSelectedEvent)
        event_dispatcher.register(self, SceneDeletedEvent)
        event_dispatcher.register(self, SceneChangedEvent)
        self.repo = RepositoryPersistenceManager.instance()

    def setNovel(self, novel: Novel):
        self._novel = novel
        self.refresh()

    def selectedScenes(self) -> List[Scene]:
        return list(self._selectedScenes)

    def selectedChapters(self) -> List[Chapter]:
        return list(self._selectedChapters)

    def refresh(self):
        self.clearSelection()
        clear_layout(self, auto_delete=False)

        for scene in self._novel.scenes:
            if scene not in self._scenes.keys():
                self.__initSceneWidget(scene)

            sceneWdg = self._scenes[scene]
            if scene.chapter:
                if scene.chapter not in self._chapters.keys():
                    chapter_wdg = self.__initChapterWidget(scene.chapter)
                    self._centralWidget.layout().addWidget(chapter_wdg)
                self._chapters[scene.chapter].addSceneWidget(sceneWdg)
            else:
                self._centralWidget.layout().addWidget(sceneWdg)

        chapter_index = 0
        for i, chapter in enumerate(self._novel.chapters):
            if chapter not in self._chapters.keys():
                chapter_wdg = self.__initChapterWidget(chapter)
                if i > 0:
                    prev_chapter_wdg = self._chapters[self._novel.chapters[i - 1]]
                    chapter_index = self._centralWidget.layout().indexOf(prev_chapter_wdg)
                    chapter_index += 1
                self._centralWidget.layout().insertWidget(chapter_index, chapter_wdg)

        self._centralWidget.layout().addWidget(self._spacer)

    def insertChapter(self):
        if self._novel.chapters:
            last_chapter = self._novel.chapters[-1]
            i = self._centralWidget.layout().indexOf(self._chapters[last_chapter]) + 1
        else:
            i = 0
        chapter = Chapter('')
        self._novel.chapters.append(chapter)
        wdg = self.__initChapterWidget(chapter)
        self._centralWidget.layout().insertWidget(i, wdg)

    def selectChapter(self, chapter: Chapter):
        self.clearSelection()
        self._chapters[chapter].select()
        if chapter not in self._selectedChapters:
            self._selectedChapters.add(chapter)

    def selectScene(self, scene: Scene):
        self.clearSelection()
        self._scenes[scene].select()
        if scene not in self._selectedScenes:
            self._selectedScenes.add(scene)

    def clearSelection(self):
        for scene in self._selectedScenes:
            self._scenes[scene].deselect()
        for chapter in self._selectedChapters:
            self._chapters[chapter].deselect()
        self._selectedScenes.clear()
        self._selectedChapters.clear()

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, SceneSelectedEvent):
            self.selectScene(event.scene)
        elif isinstance(event, SceneDeletedEvent):
            if event.scene in self._selectedScenes:
                self._selectedScenes.remove(event.scene)
            if event.scene in self._scenes.keys():
                wdg = self._scenes.pop(event.scene)
                wdg.parent().layout().removeWidget(wdg)
                gc(wdg)
        elif isinstance(event, SceneChangedEvent):
            wdg = self._scenes.get(event.scene)
            if wdg is not None:
                wdg.refresh()

    def _sceneSelectionChanged(self, sceneWdg: SceneWidget, selected: bool):
        if selected:
            self.clearSelection()
            self._selectedScenes.add(sceneWdg.scene())
            self.sceneSelected.emit(sceneWdg.scene())
        elif sceneWdg.scene() in self._selectedScenes:
            self._selectedScenes.remove(sceneWdg.scene())

    def _chapterSelectionChanged(self, chapterWdg: ChapterWidget, selected: bool):
        if selected:
            self.clearSelection()
            self._selectedChapters.add(chapterWdg.chapter())
            self.chapterSelected.emit(chapterWdg.chapter())
        elif chapterWdg.chapter() in self._selectedChapters:
            self._selectedChapters.remove(chapterWdg.chapter())

    def _deleteChapterWidget(self, chapterWdg: ChapterWidget):
        chapter = chapterWdg.chapter()
        if chapter in self._selectedChapters:
            self._selectedChapters.remove(chapter)
        self._chapters.pop(chapter)

        i = self._centralWidget.layout().indexOf(chapterWdg)
        for wdg in chapterWdg.sceneWidgets():
            chapterWdg.containerWidget().layout().removeWidget(wdg)
            wdg.setParent(self._centralWidget)
            self._centralWidget.layout().insertWidget(i, wdg)
            i += 1

            wdg.scene().chapter = None
            self.repo.update_scene(wdg.scene())

        chapterWdg.setHidden(True)
        gc(chapterWdg)

        self._novel.chapters.remove(chapter)
        self.repo.update_novel(self._novel)

        for wdg in self._chapters.values():
            wdg.refresh()

        emit_event(ChapterChangedEvent(self))

    def _dragStarted(self, wdg: QWidget):
        wdg.setHidden(True)
        if isinstance(wdg, SceneWidget):
            self._dummyWdg = SceneWidget(wdg.scene(), wdg.novel(), animation=False)
        elif isinstance(wdg, ChapterWidget):
            self._dummyWdg = ChapterWidget(wdg.chapter(), wdg.novel())
            for v in self._scenes.values():
                v.setDisabled(True)
        else:
            return

        translucent(self._dummyWdg)
        self._dummyWdg.setHidden(True)
        self._dummyWdg.setParent(self._centralWidget)
        self._dummyWdg.setAcceptDrops(True)
        self._dummyWdg.installEventFilter(
            DropEventFilter(self._dummyWdg, [self.SCENE_MIME_TYPE, self.CHAPTER_MIME_TYPE], droppedSlot=self._drop))

    def _dragStopped(self, wdg: QWidget):
        if self._dummyWdg:
            gc(self._dummyWdg)
            self._dummyWdg = None
        if self._toBeRemoved:
            gc(self._toBeRemoved)
            self._toBeRemoved = None

            self._reorderScenes()
        else:
            wdg.setVisible(True)

        for v in self._scenes.values():
            v.setEnabled(True)

    def _dragEnteredForEnd(self, _: QMimeData):
        self._spacer.layout().addWidget(self._dummyWdg, alignment=Qt.AlignmentFlag.AlignTop)
        self._dummyWdg.setVisible(True)

    def _dragLeftFromEnd(self):
        self._dummyWdg.setHidden(True)
        self._spacer.layout().removeWidget(self._dummyWdg)
        self._dummyWdg.setParent(self._centralWidget)

    def _dragMovedOnChapter(self, chapterWdg: ChapterWidget, edge: Qt.Edge, _: QPointF):
        i = self._centralWidget.layout().indexOf(chapterWdg)
        if edge == Qt.Edge.TopEdge:
            self._centralWidget.layout().insertWidget(i, self._dummyWdg)
        else:
            chapterWdg.insertSceneWidget(0, self._dummyWdg)
        self._dummyWdg.setVisible(True)

    def _drop(self, mimeData: QMimeData):
        self.clearSelection()

        ref = mimeData.reference()
        if self._dummyWdg.isHidden():
            return
        if isinstance(ref, Scene):
            sceneWdg = self._scenes[ref]
            self._toBeRemoved = sceneWdg
            new_widget = self.__initSceneWidget(ref)
            if self._dummyWdg.parent() is self._centralWidget:
                ref.chapter = None
                new_widget.setParent(self._centralWidget)
                i = self._centralWidget.layout().indexOf(self._dummyWdg)
                self._centralWidget.layout().insertWidget(i, new_widget)
            elif self._dummyWdg.parent() is self._spacer:
                ref.chapter = None
                new_widget.setParent(self._centralWidget)
                self._centralWidget.layout().insertWidget(self._centralWidget.layout().count() - 1, new_widget)
            elif isinstance(self._dummyWdg.parent().parent(), ChapterWidget):
                chapter_wdg: ChapterWidget = self._dummyWdg.parent().parent()
                ref.chapter = chapter_wdg.chapter()
                new_widget.setParent(chapter_wdg)
                i = chapter_wdg.containerWidget().layout().indexOf(self._dummyWdg)
                chapter_wdg.insertSceneWidget(i, new_widget)
            self.repo.update_scene(ref)
        elif isinstance(ref, Chapter):
            chapter_wdg = self._chapters[ref]
            self._toBeRemoved = chapter_wdg
            new_widget = self.__initChapterWidget(ref)

            for wdg in chapter_wdg.sceneWidgets():
                new_widget.addSceneWidget(self.__initSceneWidget(wdg.scene()))

            new_widget.setParent(self._centralWidget)
            i = self._centralWidget.layout().indexOf(self._dummyWdg)
            self._centralWidget.layout().insertWidget(i, new_widget)

        self._dummyWdg.setHidden(True)

    def _reorderScenes(self):
        self._novel.chapters.clear()
        self._novel.scenes.clear()

        for i in range(self._centralWidget.layout().count()):
            item = self._centralWidget.layout().itemAt(i)
            if item is None:
                continue
            wdg = item.widget()
            if isinstance(wdg, ChapterWidget):
                self._novel.chapters.append(wdg.chapter())
                for scene_wdg in wdg.sceneWidgets():
                    self._novel.scenes.append(scene_wdg.scene())
            elif isinstance(wdg, SceneWidget):
                self._novel.scenes.append(wdg.scene())

        for wdg in self._chapters.values():
            wdg.refresh()

        emit_event(SceneOrderChangedEvent(self))
        self.repo.update_novel(self._novel)

    def _dragMovedOnScene(self, sceneWdg: SceneWidget, edge: Qt.Edge, _: QPointF):
        i = sceneWdg.parent().layout().indexOf(sceneWdg)
        if edge == Qt.Edge.TopEdge:
            sceneWdg.parent().layout().insertWidget(i, self._dummyWdg)
        else:
            sceneWdg.parent().layout().insertWidget(i + 1, self._dummyWdg)
        self._dummyWdg.setVisible(True)

    # noinspection PyTypeChecker
    def __initChapterWidget(self, chapter):
        chapterWdg = ChapterWidget(chapter, self._novel)
        chapterWdg.selectionChanged.connect(partial(self._chapterSelectionChanged, chapterWdg))
        chapterWdg.deleted.connect(partial(self._deleteChapterWidget, chapterWdg))
        chapterWdg.installEventFilter(
            DragEventFilter(chapterWdg, self.CHAPTER_MIME_TYPE, dataFunc=lambda wdg: wdg.chapter(),
                            grabbed=chapterWdg.titleWidget(),
                            startedSlot=partial(self._dragStarted, chapterWdg),
                            finishedSlot=partial(self._dragStopped, chapterWdg)))
        chapterWdg.titleWidget().setAcceptDrops(True)
        chapterWdg.titleWidget().installEventFilter(
            DropEventFilter(chapterWdg, [self.SCENE_MIME_TYPE, self.CHAPTER_MIME_TYPE],
                            motionDetection=Qt.Orientation.Vertical,
                            motionSlot=partial(self._dragMovedOnChapter, chapterWdg),
                            droppedSlot=self._drop
                            )
        )
        self._chapters[chapter] = chapterWdg

        return chapterWdg

    # noinspection PyTypeChecker
    def __initSceneWidget(self, scene: Scene) -> SceneWidget:
        sceneWdg = SceneWidget(scene, self._novel)
        self._scenes[scene] = sceneWdg
        sceneWdg.selectionChanged.connect(partial(self._sceneSelectionChanged, sceneWdg))
        sceneWdg.installEventFilter(
            DragEventFilter(sceneWdg, self.SCENE_MIME_TYPE, dataFunc=lambda wdg: wdg.scene(),
                            startedSlot=partial(self._dragStarted, sceneWdg),
                            finishedSlot=partial(self._dragStopped, sceneWdg)))
        sceneWdg.setAcceptDrops(True)
        sceneWdg.installEventFilter(
            DropEventFilter(sceneWdg, [self.SCENE_MIME_TYPE],
                            motionDetection=Qt.Orientation.Vertical,
                            motionSlot=partial(self._dragMovedOnScene, sceneWdg),
                            droppedSlot=self._drop
                            )

        )
        return sceneWdg

    # def setModel(self, model: ChaptersTreeModel) -> None:
    #     return
    # super(ScenesTreeView, self).setModel(model)
    # self.expandAll()
    # self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    # self.setColumnWidth(ChaptersTreeModel.ColPlus, 24)
    # model.orderChanged.connect(self._on_scene_moved)
    # model.modelReset.connect(self.expandAll)

    # def insertChapter(self, index: int = -1):
    #     self.model().newChapter(index)
    #     self.repo.update_novel(app_env.novel)
    #     emit_event(ChapterChangedEvent(self))
    #
    # def insertSceneAfter(self, scene: Scene, chapter: Optional[Chapter] = None):
    #     new_scene = app_env.novel.insert_scene_after(scene, chapter)
    #     self.model().update()
    #     self.model().modelReset.emit()
    #     self.repo.insert_scene(app_env.novel, new_scene)
    #     emit_event(SceneChangedEvent(self))
    #
    # def selectedChapter(self) -> Optional[Chapter]:
    #     indexes = self.selectionModel().selectedIndexes()
    #     if indexes:
    #         node = indexes[0].data(ChaptersTreeModel.NodeRole)
    #         if isinstance(node, ChapterNode):
    #             return node.chapter
    #
    # def _on_chapter_clicked(self, index: QModelIndex):
    #     if index.column() == 0:
    #         return
    #
    #     indexes = self.selectionModel().selectedIndexes()
    #     if not indexes:
    #         return
    #     node = indexes[0].data(ChaptersTreeModel.NodeRole)
    #
    #     novel = app_env.novel
    #     if isinstance(node, ChapterNode):
    #         builder = PopupMenuBuilder.from_index(self, index)
    #
    #         scenes = novel.scenes_in_chapter(node.chapter)
    #         if scenes:
    #             builder.add_action('Add scene', IconRegistry.scene_icon(), lambda: self.insertSceneAfter(scenes[-1]))
    #             builder.add_separator()
    #
    #         builder.add_action('Add chapter before', IconRegistry.chapter_icon(),
    #                            slot=lambda: self.insertChapter(novel.chapters.index(node.chapter)))
    #         builder.add_action('Add chapter after', IconRegistry.chapter_icon(),
    #                            slot=lambda: self.insertChapter(novel.chapters.index(node.chapter) + 1))
    #         builder.popup()
    #     elif isinstance(node, SceneNode):
    #         if node.scene and node.scene.chapter:
    #             self.insertSceneAfter(node.scene)
    #
    # def _on_scene_moved(self):
    #     self.repo.update_novel(app_env.novel)
    #     emit_event(SceneChangedEvent(self))


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

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
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
        if event.type() == QEvent.Type.ToolTip:
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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
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
            painter.setPen(QPen(QColor(plot.icon_color), 4, Qt.PenStyle.SolidLine))
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
            painter.setPen(QPen(QColor(plot.icon_color), 4, Qt.PenStyle.SolidLine))
            painter.drawLine(0, y, last_sc_x.get(sl_i, 15), y)
            painter.setPen(QPen(Qt.GlobalColor.black, 5, Qt.PenStyle.SolidLine))
            painter.drawPixmap(0, y - 35, IconRegistry.from_name(plot.icon, plot.icon_color).pixmap(24, 24))
            painter.drawText(26, y - 15, plot.text)

            for sc_i, scene in enumerate(scenes):
                if plot in scene.plots():
                    self._draw_scene_ellipse(painter, scene, self._scene_x(sc_i), y)

        painter.end()

    def _draw_scene_ellipse(self, painter: QPainter, scene: Scene, x: int, y: int):
        if scene.plot_values:
            pen = Qt.GlobalColor.red if scene is self._clicked_scene else Qt.GlobalColor.black
            if len(scene.plot_values) == 1:
                painter.setPen(QPen(pen, 3, Qt.PenStyle.SolidLine))
                painter.setBrush(Qt.GlobalColor.black)
                painter.drawEllipse(x, y - 7, 14, 14)
            else:
                painter.setPen(QPen(pen, 3, Qt.PenStyle.SolidLine))
                painter.setBrush(Qt.GlobalColor.white)
                painter.drawEllipse(x, y - 10, 20, 20)
        else:
            pen = Qt.GlobalColor.red if scene is self._clicked_scene else Qt.GlobalColor.gray
            painter.setPen(QPen(pen, 3, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.GlobalColor.gray)
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
        transparent(btn)

        self.wdgTop = QWidget()
        hbox(self.wdgTop, 0)
        self.wdgTop.layout().addWidget(btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.textSynopsis = QTextEdit()
        self.textSynopsis.setFontPointSize(btn.label.font().pointSize())
        self.textSynopsis.setPlaceholderText('Scene synopsis...')
        self.textSynopsis.setTabChangesFocus(True)
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
            self.layout().addWidget(btnPlot, alignment=Qt.AlignmentFlag.AlignTop)

            line.setFixedWidth(self.LineSize)
            line.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
            hmax(self)
        else:
            vbox(self, 0, 0)
            hbox(self.wdgReferences, margin=0)
            btnPlot = QPushButton()
            self.layout().addWidget(btnPlot, alignment=Qt.AlignmentFlag.AlignLeft)

            line.setFixedHeight(self.LineSize)
            line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        btnPlot.setText(self.plot.text)
        incr_font(btnPlot)
        bold(btnPlot)
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
        self._orientation: int = Qt.Orientation.Horizontal
        self._acts_filter: Dict[int, bool] = {}
        vbox(self, spacing=0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

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
            if self._orientation == Qt.Orientation.Horizontal:
                vbox(wdgScenePlotParent, spacing=0)
            else:
                hbox(wdgScenePlotParent, spacing=0)

            wdgScenes = _ScenesLineWidget(self.novel, vertical=self._orientation == Qt.Orientation.Vertical)
            wdgScenePlotParent.layout().addWidget(wdgScenes)

            for plot in self.novel.plots:
                wdg = _ScenePlotAssociationsWidget(self.novel, plot, parent=self,
                                                   vertical=self._orientation == Qt.Orientation.Vertical)
                wdgScenePlotParent.layout().addWidget(wdg)

            if self._orientation == Qt.Orientation.Horizontal:
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
                titles.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
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


class SceneNotesEditor(DocumentTextEditor):

    def __init__(self, parent=None):
        super(SceneNotesEditor, self).__init__(parent)
        self._scene: Optional[Scene] = None
        self.setTitleVisible(False)
        self.setPlaceholderText('Scene notes')

        self.textEdit.textChanged.connect(self._save)

        self.repo = RepositoryPersistenceManager.instance()

    def setScene(self, scene: Scene):
        self._scene = scene
        if self._scene.document is None:
            self._scene.document = Document('', scene_id=self._scene.id)
            self._scene.document.loaded = True
        if not scene.document.loaded:
            json_client.load_document(app_env.novel, scene.document)

        self.setText(scene.document.content, '')

    def _save(self):
        if self._scene is None:
            return
        self._scene.document.content = self.textEdit.toHtml()
        self.repo.update_doc(app_env.novel, self._scene.document)


class SceneStageButton(QToolButton, EventListener):
    def __init__(self, parent=None):
        super(SceneStageButton, self).__init__(parent)
        self._scene: Optional[Scene] = None
        self._novel: Optional[Novel] = None
        self._stageOk: bool = False

        self.setStyleSheet('''
        QToolButton {
            border: 0px;
        }

        QToolButton::menu-indicator {
            width: 0px;
        }
        ''')
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        pointy(self)

        self.repo = RepositoryPersistenceManager.instance()

        event_dispatcher.register(self, ActiveSceneStageChanged)
        event_dispatcher.register(self, SceneStatusChangedEvent)
        event_dispatcher.register(self, AvailableSceneStagesChanged)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, (ActiveSceneStageChanged, AvailableSceneStagesChanged)):
            self.updateStage()
        elif isinstance(event, SceneStatusChangedEvent) and event.scene == self._scene:
            self.updateStage()

    def setScene(self, scene: Scene):
        self._scene = scene
        self._novel = app_env.novel
        self.updateStage()

    def stageOk(self) -> bool:
        return self._stageOk

    def updateStage(self):
        if self._scene is None:
            return
        self._stageOk = False
        active_stage = self._novel.active_stage
        if self._scene.stage and active_stage:
            active_stage_index = self._novel.stages.index(active_stage)
            scene_stage_index = self._novel.stages.index(self._scene.stage)

            if scene_stage_index >= active_stage_index:
                self._stageOk = True
                self.setIcon(IconRegistry.ok_icon())

        if not self._stageOk:
            self.setIcon(IconRegistry.progress_check_icon('grey'))

        menu = QMenu(self)
        for stage in self._novel.stages:
            act = action(stage.text, slot=partial(self._changeStage, stage), checkable=True, parent=menu)
            act.setChecked(self._scene.stage == stage)
            menu.addAction(act)

        btn_popup_menu(self, menu)

    def _changeStage(self, stage: SceneStage):
        self._scene.stage = stage
        self.updateStage()
        self.repo.update_scene(self._scene)

        emit_event(SceneStatusChangedEvent(self, self._scene))


class SceneDriveTrackingEditor(QWidget, Ui_SceneDriveTrackingEditor):
    def __init__(self, parent=None):
        super(SceneDriveTrackingEditor, self).__init__(parent)
        self.setupUi(self)
        self.scene: Optional[Scene] = None

        self.sliderWorld.valueChanged.connect(self._worldBuildingChanged)
        self.sliderTension.valueChanged.connect(self._tensionChanged)

        self.informationBtnGroup = FadeOutButtonGroup()
        self.informationBtnGroup.addButton(self.btnDiscovery)
        self.informationBtnGroup.addButton(self.btnRevelation)
        self.informationBtnGroup.buttonClicked.connect(self._informationClicked)

        self.readerPosBtnGroup = FadeOutButtonGroup()
        self.readerPosBtnGroup.addButton(self.btnReaderSuperior)
        self.readerPosBtnGroup.addButton(self.btnReaderInferior)
        self.readerPosBtnGroup.buttonClicked.connect(self._readerPosClicked)

        self.btnDeuxExMachina.clicked.connect(self._deusExClicked)

    def reset(self):
        self.scene = None
        self.sliderWorld.setValue(0)
        self.sliderTension.setValue(0)
        self.readerPosBtnGroup.reset()
        self.informationBtnGroup.reset()
        self.btnDeuxExMachina.setChecked(False)

    def setScene(self, scene: Scene):
        self.reset()
        self.scene = scene

        self.sliderWorld.setValue(self.scene.drive.worldbuilding)
        self.sliderTension.setValue(self.scene.drive.tension)
        self.btnDeuxExMachina.setChecked(self.scene.drive.deus_ex_machina)

        if self.scene.drive.new_information == InformationAcquisition.DISCOVERY:
            self.informationBtnGroup.toggle(self.btnDiscovery)
        elif self.scene.drive.new_information == InformationAcquisition.REVELATION:
            self.informationBtnGroup.toggle(self.btnRevelation)

        if self.scene.drive.reader_position == ReaderPosition.SUPERIOR:
            self.readerPosBtnGroup.toggle(self.btnReaderSuperior)
        elif self.scene.drive.reader_position == ReaderPosition.INFERIOR:
            self.readerPosBtnGroup.toggle(self.btnReaderInferior)

    def _worldBuildingChanged(self, value: int):
        if value > 0 and self.sliderWorld.isVisible():
            qtanim.glow(self.sliderWorld, radius=12, color=QColor('#40916c'))

        if self.scene:
            self.scene.drive.worldbuilding = value

    def _tensionChanged(self, value: int):
        if value > 0 and self.sliderTension.isVisible():
            qtanim.glow(self.sliderTension, radius=12, color=QColor('#d00000'))

        if self.scene:
            self.scene.drive.tension = value

    def _readerPosClicked(self):
        if self.readerPosBtnGroup.checkedButton() == self.btnReaderSuperior:
            self.scene.drive.reader_position = ReaderPosition.SUPERIOR
        elif self.readerPosBtnGroup.checkedButton() == self.btnReaderInferior:
            self.scene.drive.reader_position = ReaderPosition.INFERIOR

    def _informationClicked(self):
        if self.informationBtnGroup.checkedButton() == self.btnDiscovery:
            self.scene.drive.new_information = InformationAcquisition.DISCOVERY
        elif self.informationBtnGroup.checkedButton() == self.btnRevelation:
            self.scene.drive.new_information = InformationAcquisition.REVELATION

    def _deusExClicked(self, checked: bool):
        self.scene.drive.deus_ex_machina = checked
