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
from abc import abstractmethod
from dataclasses import dataclass
from functools import partial
from typing import Optional, List, Dict

import qtanim
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF, QEvent, QPoint, QMimeData, QTimer
from PyQt6.QtGui import QIcon, QColor, QPainter, QPen, \
    QPainterPath, QPaintEvent, QAction, QResizeEvent, QEnterEvent, QDragEnterEvent
from PyQt6.QtWidgets import QWidget, QToolButton, QPushButton, QTextEdit, QDialog, QApplication
from overrides import overrides
from qtanim import fade_in
from qthandy import pointy, gc, translucent, bold, clear_layout, decr_font, \
    margins, spacer, sp, curved_flow, incr_icon, vbox, vspacer, transparent
from qthandy.filter import OpacityEventFilter, ObjectReferenceMimeData, DragEventFilter, DropEventFilter
from qtmenu import ScrollableMenuWidget, ActionTooltipDisplayMode, MenuWidget, TabularGridMenuWidget

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Novel, Scene, SceneStructureItemType, SceneStructureItem, SceneOutcome, \
    SceneStructureAgenda, ScenePurposeType
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.view.common import action, fade_out_and_gc, ButtonPressResizeEventFilter
from src.main.python.plotlyst.view.generated.scene_structure_editor_widget_ui import Ui_SceneStructureWidget
from src.main.python.plotlyst.view.generated.scene_structure_template_selector_dialog_ui import \
    Ui_SceneStructuteTemplateSelector
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.style.base import apply_white_menu
from src.main.python.plotlyst.view.widget.button import DotsMenuButton
from src.main.python.plotlyst.view.widget.input import RemovalButton
from src.main.python.plotlyst.view.widget.list import ListView, ListItemWidget
from src.main.python.plotlyst.view.widget.scenes import SceneOutcomeSelector

beat_descriptions = {SceneStructureItemType.BEAT: 'New action, reaction, thought, or emotion',
                     SceneStructureItemType.ACTION: 'Character takes an action to achieve their goal',
                     SceneStructureItemType.CONFLICT: "Conflict hinders the character's goals",
                     SceneStructureItemType.CLIMAX: 'Outcome of the scene, typically ending with disaster',
                     SceneStructureItemType.REACTION: "Initial reaction to a prior scene's outcome",
                     SceneStructureItemType.EMOTION: "The character's emotional state",
                     SceneStructureItemType.DILEMMA: 'Dilemma throughout the scene. What to do next?',
                     SceneStructureItemType.DECISION: 'Character makes a decision and may act right away',
                     SceneStructureItemType.HOOK: "Initial hook to raise readers' curiosity",
                     SceneStructureItemType.INCITING_INCIDENT: 'Triggers events in this scene',
                     SceneStructureItemType.TICKING_CLOCK: 'Ticking clock is activated to add urgency',
                     SceneStructureItemType.RISING_ACTION: 'Increasing progress or setback throughout the scene',
                     SceneStructureItemType.PROGRESS: 'Increasing progress throughout the scene',
                     SceneStructureItemType.SETBACK: 'Increasing setback throughout the scene',
                     SceneStructureItemType.CHOICE: 'Impossible choice between two equally good or bad outcomes',
                     SceneStructureItemType.EXPOSITION: 'Description, explanation, or introduction of normal world',
                     SceneStructureItemType.SUMMARY: 'A summary of events to quicken the pace',
                     SceneStructureItemType.TURN: 'Shift in plot arc: small victory or setback',
                     SceneStructureItemType.MYSTERY: "An unanswered question raises reader's curiosity",
                     SceneStructureItemType.REVELATION: 'Key information is revealed or discovered',
                     SceneStructureItemType.SETUP: 'Event that sets up a later payoff. May put the scene in motion',
                     SceneStructureItemType.RESOLUTION: "Provides closure. May reinforce the climax's outcome or its consequences",
                     SceneStructureItemType.BUILDUP: "Escalates tension or anticipation leading toward a climactic moment",
                     SceneStructureItemType.DISTURBANCE: "Introduces conflict or tension that sets the scene in motion",
                     SceneStructureItemType.FALSE_VICTORY: "A deceptive false victory moment that leads to a disaster outcome",
                     }


def beat_icon(beat_type: SceneStructureItemType, resolved: bool = False, trade_off: bool = False) -> QIcon:
    if beat_type == SceneStructureItemType.ACTION:
        return IconRegistry.goal_icon()
    elif beat_type == SceneStructureItemType.CONFLICT:
        return IconRegistry.conflict_icon()
    elif beat_type == SceneStructureItemType.CLIMAX:
        return IconRegistry.action_scene_icon(resolved, trade_off)
    elif beat_type == SceneStructureItemType.REACTION:
        return IconRegistry.reaction_icon()
    elif beat_type == SceneStructureItemType.EMOTION:
        return IconRegistry.emotion_icon()
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
    elif beat_type == SceneStructureItemType.PROGRESS:
        return IconRegistry.rising_action_icon()
    elif beat_type == SceneStructureItemType.SETBACK:
        return IconRegistry.setback_icon()
    elif beat_type == SceneStructureItemType.CHOICE:
        return IconRegistry.crisis_icon()
    elif beat_type == SceneStructureItemType.EXPOSITION:
        return IconRegistry.exposition_icon()
    elif beat_type == SceneStructureItemType.SUMMARY:
        return IconRegistry.summary_scene_icon()
    elif beat_type == SceneStructureItemType.BEAT:
        return IconRegistry.beat_icon()
    elif beat_type == SceneStructureItemType.TURN:
        return IconRegistry.from_name('mdi.boom-gate-up-outline', '#8338ec')
    elif beat_type == SceneStructureItemType.MYSTERY:
        return IconRegistry.from_name('ri.question-mark', '#b8c0ff')
    elif beat_type == SceneStructureItemType.REVELATION:
        return IconRegistry.from_name('fa5s.binoculars', '#588157')
    elif beat_type == SceneStructureItemType.SETUP:
        return IconRegistry.from_name('mdi.motion', '#ddbea9')
    elif beat_type == SceneStructureItemType.RESOLUTION:
        return IconRegistry.from_name('fa5s.water', '#7192be')
    elif beat_type == SceneStructureItemType.BUILDUP:
        return IconRegistry.from_name('mdi6.progress-upload', '#e76f51')
    elif beat_type == SceneStructureItemType.DISTURBANCE:
        return IconRegistry.from_name('mdi.chemical-weapon', '#e63946')
    elif beat_type == SceneStructureItemType.FALSE_VICTORY:
        return IconRegistry.from_name('mdi.trophy-broken', '#b5838d')
    else:
        return IconRegistry.circle_icon()


@dataclass
class Emotion:
    name: str
    color: str
    weight: int

    @overrides
    def __hash__(self):
        return hash(self.name)


emotions: Dict[str, Emotion] = {'Admiration': Emotion('Admiration', '#008744', 4),
                                'Adoration': Emotion('Adoration', '#7048e8', 4),
                                'Amusement': Emotion('Amusement', '#ff6961', 4),
                                'Anger': Emotion('Anger', '#ff3333', 1),
                                'Anxiety': Emotion('Anxiety', '#ffbf00', 2), 'Awe': Emotion('Awe', '#87ceeb', 4),
                                'Awkwardness': Emotion('Awkwardness', '#ff69b4', 2),
                                'Boredom': Emotion('Boredom', '#778899', 3),
                                'Calmness': Emotion('Calmness', '#1e90ff', 4),
                                'Confusion': Emotion('Confusion', '#ffc107', 3),
                                'Craving': Emotion('Craving', '#ffdb58', 3),
                                'Disgust': Emotion('Disgust', '#ffa500', 2),
                                'Empathic': Emotion('Empathic', '#4da6ff', 3), 'Pain': Emotion('Pain', '#ff5050', 2),
                                'Entrancement': Emotion('Entrancement', '#00bfff', 4),
                                'Excitement': Emotion('Excitement', '#ff5c5c', 4),
                                'Fear': Emotion('Fear', '#1f1f1f', 2),
                                'Horror': Emotion('Horror', '#ff4d4d', 1),
                                'Interest': Emotion('Interest', '#3cb371', 4),
                                'Joy': Emotion('Joy', '#00ff7f', 5), 'Nostalgia': Emotion('Nostalgia', '#ffb347', 3),
                                'Relief': Emotion('Relief', '#00ff00', 4),
                                'Sadness': Emotion('Sadness', '#999999', 2),
                                'Satisfaction': Emotion('Satisfaction', '#228b22', 5),
                                'Surprise': Emotion('Surprise', '#ff69b4', 5)}


class EmotionSelectorMenu(ScrollableMenuWidget):
    emotionSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super(EmotionSelectorMenu, self).__init__(parent)
        self.setMaximumHeight(300)
        for emotion in ['Admiration', 'Adoration', 'Amusement', 'Anger', 'Anxiety', 'Awe', 'Awkwardness', 'Boredom',
                        'Calmness', 'Confusion',
                        'Craving', 'Disgust', 'Empathic', 'Pain', 'Entrancement', 'Excitement', 'Fear', 'Horror',
                        'Interest', 'Joy', 'Nostalgia', 'Relief', 'Sadness', 'Satisfaction', 'Surprise']:
            self.addAction(action(emotion, slot=partial(self.emotionSelected.emit, emotion)))


class EmotionSelectorButton(QToolButton):

    def __init__(self, parent=None):
        super(EmotionSelectorButton, self).__init__(parent)
        self.setIcon(IconRegistry.from_name('ri.emotion-sad-line'))
        self.setProperty('transparent', True)
        pointy(self)
        incr_icon(self, 2)
        self.menuEmotions = EmotionSelectorMenu(self)
        # menuEmotions.setMaximumHeight(300)
        # for emotion in ['Admiration', 'Adoration', 'Amusement', 'Anger', 'Anxiety', 'Awe', 'Awkwardness', 'Boredom',
        #                 'Calmness', 'Confusion',
        #                 'Craving', 'Disgust', 'Empathic', 'Pain', 'Entrancement', 'Excitement', 'Fear', 'Horror',
        #                 'Interest', 'Joy', 'Nostalgia', 'Relief', 'Sadness', 'Satisfaction', 'Surprise']:
        #     menuEmotions.addAction(action(emotion, slot=partial(self.emotionSelected.emit, emotion)))

        self.installEventFilter(ButtonPressResizeEventFilter(self))


class BeatSelectorMenu(TabularGridMenuWidget):
    selected = pyqtSignal(SceneStructureItemType)

    def __init__(self, parent=None):
        super(BeatSelectorMenu, self).__init__(parent)

        self._actions: Dict[SceneStructureItemType, QAction] = {}
        self._outcomeEnabled: bool = True

        self.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
        apply_white_menu(self)

        self._tabDrive = self.addTab('Drive', IconRegistry.action_scene_icon())
        self._tabReaction = self.addTab('Reaction', IconRegistry.reaction_scene_icon())
        self._tabGeneral = self.addTab('General', IconRegistry.beat_icon())
        self._tabMisc = self.addTab('Misc', IconRegistry.from_name('mdi.dots-horizontal-circle-outline'))

        self.addSection(self._tabDrive, 'Beats that often advance the scene while creating narrative drive', 0, 0)
        self.addSeparator(self._tabDrive, 1, 0, colSpan=2)
        self._addAction(self._tabDrive, 'Action', SceneStructureItemType.ACTION, 2, 0)
        self._addAction(self._tabDrive, 'Hook', SceneStructureItemType.HOOK, 2, 1)
        self._addAction(self._tabDrive, 'Disturbance', SceneStructureItemType.DISTURBANCE, 3, 1)
        self._addAction(self._tabDrive, 'Inciting incident', SceneStructureItemType.INCITING_INCIDENT, 4, 1)
        self._addAction(self._tabDrive, 'Conflict', SceneStructureItemType.CONFLICT, 3, 0)
        self._addAction(self._tabDrive, 'Mystery', SceneStructureItemType.MYSTERY, 4, 0)
        self._addAction(self._tabDrive, 'Rising action', SceneStructureItemType.RISING_ACTION, 5, 0)
        self._addAction(self._tabDrive, 'Build-up', SceneStructureItemType.BUILDUP, 5, 1)
        self._addAction(self._tabDrive, 'Turn', SceneStructureItemType.TURN, 6, 0)
        self._addAction(self._tabDrive, 'Revelation', SceneStructureItemType.REVELATION, 6, 1)
        self._addAction(self._tabDrive, 'Choice', SceneStructureItemType.CHOICE, 7, 0)
        self._addAction(self._tabDrive, 'Outcome', SceneStructureItemType.CLIMAX, 7, 1)

        self.addSection(self._tabReaction, 'Common reaction beats', 0, 0)
        self.addSeparator(self._tabReaction, 1, 0)
        self._addAction(self._tabReaction, 'Reaction', SceneStructureItemType.REACTION, 2, 0)
        self._addAction(self._tabReaction, 'Emotion', SceneStructureItemType.EMOTION, 3, 0)
        self._addAction(self._tabReaction, 'Dilemma', SceneStructureItemType.DILEMMA, 4, 0)
        self._addAction(self._tabReaction, 'Decision', SceneStructureItemType.DECISION, 5, 0)
        self.addWidget(self._tabReaction, vspacer(), 6, 0)

        self.addSection(self._tabGeneral, 'General beats', 0, 0)
        self.addSeparator(self._tabGeneral, 1, 0, colSpan=2)
        self._addAction(self._tabGeneral, 'Beat', SceneStructureItemType.BEAT, 2, 0)
        self._addAction(self._tabGeneral, 'Exposition', SceneStructureItemType.EXPOSITION, 3, 0)
        self._addAction(self._tabGeneral, 'Summary', SceneStructureItemType.SUMMARY, 4, 0)
        self._addAction(self._tabGeneral, 'Setup', SceneStructureItemType.SETUP, 5, 0)
        self._addAction(self._tabGeneral, 'Resolution', SceneStructureItemType.RESOLUTION, 2, 1)
        self.addWidget(self._tabGeneral, vspacer(), 6, 0)

        self.addSection(self._tabMisc, 'Miscellaneous', 0, 0)
        self.addSeparator(self._tabMisc, 1, 0)
        self._addAction(self._tabMisc, 'False victory', SceneStructureItemType.FALSE_VICTORY, 2, 0)
        self.addWidget(self._tabMisc, vspacer(), 6, 0)

    def _addAction(self, tabWidget: QWidget, text: str, beat_type: SceneStructureItemType, row: int, column: int):
        description = beat_descriptions[beat_type]
        action_ = action(text, beat_icon(beat_type), slot=lambda: self.selected.emit(beat_type), tooltip=description)
        self._actions[beat_type] = action_
        self.addAction(tabWidget, action_, row, column)

    def setOutcomeEnabled(self, enabled: bool):
        self._outcomeEnabled = enabled
        self._actions[SceneStructureItemType.CLIMAX].setEnabled(enabled)

    # def toggleSceneType(self, sceneType: SceneType):
    #     for action_ in self._actions.values():
    #         action_.setEnabled(True)
    #     self._actions[SceneStructureItemType.CLIMAX].setEnabled(self._outcomeEnabled)
    #     if sceneType == SceneType.REACTION:
    #         for type_ in [SceneStructureItemType.ACTION, SceneStructureItemType.HOOK,
    #                       SceneStructureItemType.RISING_ACTION, SceneStructureItemType.INCITING_INCIDENT,
    #                       SceneStructureItemType.CONFLICT, SceneStructureItemType.CLIMAX, SceneStructureItemType.TURN]:
    #             self._actions[type_].setEnabled(False)
    #     elif sceneType == SceneType.HAPPENING:
    #         for type_ in [SceneStructureItemType.ACTION, SceneStructureItemType.HOOK,
    #                       SceneStructureItemType.RISING_ACTION, SceneStructureItemType.INCITING_INCIDENT,
    #                       SceneStructureItemType.CONFLICT, SceneStructureItemType.CLIMAX, SceneStructureItemType.TURN,
    #                       SceneStructureItemType.CHOICE, SceneStructureItemType.REACTION,
    #                       SceneStructureItemType.DILEMMA, SceneStructureItemType.DECISION]:
    #             self._actions[type_].setEnabled(False)


class _SceneBeatPlaceholderButton(QPushButton):

    def __init__(self, parent=None):
        super(_SceneBeatPlaceholderButton, self).__init__(parent)
        self.setProperty('transparent', True)
        self.setIcon(IconRegistry.plus_circle_icon('grey'))
        self.installEventFilter(OpacityEventFilter(self, leaveOpacity=0.3))
        self.setIconSize(QSize(20, 20))
        pointy(self)
        self.setToolTip('Insert new beat')


class _PlaceholderWidget(QWidget):
    def __init__(self, parent=None):
        super(_PlaceholderWidget, self).__init__(parent)
        self.btn = _SceneBeatPlaceholderButton(self)
        vbox(self, 0, 0)
        margins(self, top=80)
        self.layout().addWidget(self.btn)


class SceneStructureItemWidget(QWidget):
    SceneBeatMimeType: str = 'application/scene-beat'
    dragStarted = pyqtSignal()
    dragStopped = pyqtSignal()
    removed = pyqtSignal(object)
    iconFixedSize: int = 36

    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None, readOnly: bool = False):
        super(SceneStructureItemWidget, self).__init__(parent)
        self.novel = novel
        self._readOnly = readOnly
        self.beat = scene_structure_item
        vbox(self, 0, 2)

        self._btnName = QPushButton(self)
        bold(self._btnName)
        if app_env.is_mac():
            self._btnName.setFixedHeight(max(self._btnName.sizeHint().height() - 8, 24))

        self._btnIcon = QToolButton(self)
        self._btnIcon.setIconSize(QSize(24, 24))
        self._btnIcon.setFixedSize(self.iconFixedSize, self.iconFixedSize)

        self._btnRemove = RemovalButton(self)
        self._btnRemove.setHidden(True)
        self._btnRemove.clicked.connect(self._remove)

        self.layout().addWidget(self._btnIcon, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._btnName, alignment=Qt.AlignmentFlag.AlignCenter)

        if not self._readOnly:
            self._btnIcon.setCursor(Qt.CursorShape.OpenHandCursor)
            self._dragEventFilter = DragEventFilter(self, self.SceneBeatMimeType, self._beatDataFunc,
                                                    grabbed=self._btnIcon, startedSlot=self.dragStarted.emit,
                                                    finishedSlot=self.dragStopped.emit)
            self._btnIcon.installEventFilter(self._dragEventFilter)
            self.setAcceptDrops(True)

    def isEmotion(self) -> bool:
        return self.beat.type == SceneStructureItemType.EMOTION

    def sceneStructureItem(self) -> SceneStructureItem:
        return self.beat

    def activate(self):
        if self.graphicsEffect():
            self.setGraphicsEffect(None)

    @abstractmethod
    def copy(self) -> 'SceneStructureItemWidget':
        pass

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        self._btnRemove.setGeometry(self.width() - 15, self.iconFixedSize, 15, 15)
        self._btnRemove.raise_()

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        if not self._readOnly:
            self._btnRemove.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        self._btnRemove.setHidden(True)

    def _remove(self):
        anim = qtanim.fade_out(self, duration=150)
        anim.finished.connect(lambda: self.removed.emit(self))

    def _initStyle(self):
        color = self._color()
        self._btnIcon.setStyleSheet(f'''
                    QToolButton {{
                                    background-color: {RELAXED_WHITE_COLOR};
                                    border: 2px solid {color};
                                    border-radius: 18px; padding: 4px;
                                }}
                    QToolButton:menu-indicator {{
                        width: 0;
                    }}
                    ''')
        self._btnName.setStyleSheet(f'''QPushButton {{
            border: 0px; background-color: rgba(0, 0, 0, 0); color: {color};
            padding-left: 15px;
            padding-right: 15px;
        }}''')

    def _beatDataFunc(self, btn):
        return id(self)

    def _color(self) -> str:
        if self.beat.type == SceneStructureItemType.ACTION:
            return 'darkBlue'
        elif self.beat.type == SceneStructureItemType.CONFLICT:
            return '#f3a712'
        elif self.beat.type == SceneStructureItemType.CLIMAX:
            if self.beat.outcome == SceneOutcome.TRADE_OFF:
                return '#832161'
            elif self.beat.outcome == SceneOutcome.RESOLUTION:
                return '#0b6e4f'
            else:
                return '#fe4a49'
        elif self.beat.type == SceneStructureItemType.DECISION:
            return '#219ebc'
        elif self.beat.type == SceneStructureItemType.HOOK:
            return '#829399'
        elif self.beat.type == SceneStructureItemType.INCITING_INCIDENT:
            return '#a2ad59'
        elif self.beat.type == SceneStructureItemType.TICKING_CLOCK:
            return '#f7cb15'
        elif self.beat.type == SceneStructureItemType.RISING_ACTION:
            return '#08605f'
        elif self.beat.type == SceneStructureItemType.PROGRESS:
            return '#08605f'
        elif self.beat.type == SceneStructureItemType.SETBACK:
            return '#FD4D21'
        elif self.beat.type == SceneStructureItemType.CHOICE:
            return '#ce2d4f'
        elif self.beat.type == SceneStructureItemType.EXPOSITION:
            return '#1ea896'
        elif self.beat.type == SceneStructureItemType.SUMMARY:
            return 'grey'
        elif self.beat.type == SceneStructureItemType.TURN:
            return '#8338ec'
        elif self.beat.type == SceneStructureItemType.MYSTERY:
            return '#b8c0ff'
        elif self.beat.type == SceneStructureItemType.REVELATION:
            return '#588157'
        elif self.beat.type == SceneStructureItemType.EMOTION:
            return emotions[self.beat.emotion].color
        elif self.beat.type == SceneStructureItemType.DILEMMA:
            return '#ba6f4d'
        elif self.beat.type == SceneStructureItemType.SETUP:
            return '#ddbea9'
        elif self.beat.type == SceneStructureItemType.RESOLUTION:
            return '#7192be'
        elif self.beat.type == SceneStructureItemType.BUILDUP:
            return '#e76f51'
        elif self.beat.type == SceneStructureItemType.DISTURBANCE:
            return '#e63946'
        elif self.beat.type == SceneStructureItemType.FALSE_VICTORY:
            return '#b5838d'
        else:
            return '#343a40'

    def _glow(self) -> QColor:
        color = QColor(self._color())
        qtanim.glow(self._btnName, color=color)

        return color


class SceneStructureBeatWidget(SceneStructureItemWidget):
    emotionChanged = pyqtSignal()
    outcomeChanged = pyqtSignal(SceneOutcome)

    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None, readOnly: bool = False):
        super(SceneStructureBeatWidget, self).__init__(novel, scene_structure_item, parent, readOnly)
        self.setFixedWidth(210)

        self._outcome = SceneOutcomeSelector()
        self._outcome.selected.connect(self._outcomeChanged)

        self._text = QTextEdit(self)
        if not app_env.is_mac():
            decr_font(self._text)
        self._text.setProperty('rounded', True)
        self._text.setProperty('white-bg', True)
        self._text.setReadOnly(self._readOnly)
        self._text.setMaximumHeight(100)
        self._text.setTabChangesFocus(True)
        self._text.setText(self.beat.text)
        self._text.textChanged.connect(self._textChanged)

        self._btnProgressSwitch = QToolButton(self)
        self._btnProgressSwitch.setIcon(IconRegistry.from_name('mdi.chevron-double-up', 'grey'))
        self._btnProgressSwitch.setProperty('transparent', True)
        self._progressMenu = MenuWidget(self._btnProgressSwitch)
        self._progressMenu.addAction(
            action('Progress', IconRegistry.charge_icon(2), lambda: self._changeProgress(True)))
        self._progressMenu.addAction(
            action('Setback', IconRegistry.charge_icon(-2), lambda: self._changeProgress(False)))
        pointy(self._btnProgressSwitch)
        self._btnProgressSwitch.setHidden(True)

        self.layout().addWidget(self._text)
        self.layout().addWidget(self._outcome, alignment=Qt.AlignmentFlag.AlignCenter)

        self._initStyle()

    def hasOutcome(self) -> bool:
        return self.beat.type == SceneStructureItemType.CLIMAX

    def setOutcome(self, outcome: SceneOutcome):
        self.beat.outcome = outcome
        self._outcome.refresh(outcome)
        self._initStyle()

    def activate(self):
        super(SceneStructureBeatWidget, self).activate()
        if self.isVisible():
            self._text.setFocus()

    @overrides
    def copy(self) -> 'SceneStructureItemWidget':
        return SceneStructureBeatWidget(self.novel, self.beat)

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        super(SceneStructureBeatWidget, self).enterEvent(event)
        if self.beat.type in [SceneStructureItemType.RISING_ACTION, SceneStructureItemType.PROGRESS,
                              SceneStructureItemType.SETBACK]:
            self._btnProgressSwitch.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        super(SceneStructureBeatWidget, self).leaveEvent(event)
        if not self._btnProgressSwitch.menu().isVisible():
            self._btnProgressSwitch.setHidden(True)

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        super(SceneStructureBeatWidget, self).resizeEvent(event)
        self._btnProgressSwitch.setGeometry(5, self.iconFixedSize, 18, 18)

    def swap(self, beatType: SceneStructureItemType):
        if self.beat.type != beatType:
            self.beat.type = beatType
            if self.beat.type == SceneStructureItemType.CLIMAX:
                if self.beat.outcome is None:
                    self.beat.outcome = SceneOutcome.DISASTER
                self._outcome.refresh()
            self._initStyle()
        self._glow()

    def _descriptions(self) -> dict:
        return beat_descriptions

    @overrides
    def _initStyle(self):
        super(SceneStructureBeatWidget, self)._initStyle()

        self._outcome.setVisible(self.beat.type == SceneStructureItemType.CLIMAX)
        if self.isEmotion():
            desc = "How is the character's emotion shown?"
        else:
            desc = self._descriptions()[self.beat.type]
        self._text.setPlaceholderText(desc)
        self._btnName.setToolTip(desc)
        self._text.setToolTip(desc)
        self._btnIcon.setToolTip(desc)

        self._text.setHidden(self.isEmotion())
        if self.beat.type == SceneStructureItemType.CLIMAX:
            if self.beat.outcome is None:
                self.beat.outcome = SceneOutcome.DISASTER
            name = SceneOutcome.to_str(self.beat.outcome)
            self._outcome.refresh(self.beat.outcome)
        elif self.isEmotion():
            name = self.beat.emotion
        else:
            name = self.beat.type.name
        self._btnName.setText(name.lower().capitalize().replace('_', ' '))
        self._btnIcon.setIcon(self._icon())

    def _icon(self) -> QIcon:
        return beat_icon(self.beat.type, resolved=self.beat.outcome == SceneOutcome.RESOLUTION,
                         trade_off=self.beat.outcome == SceneOutcome.TRADE_OFF)

    def _textChanged(self):
        self.beat.text = self._text.toPlainText()

    def _outcomeChanged(self, outcome: SceneOutcome):
        self.beat.outcome = outcome
        self._initStyle()
        self._glow()
        self.outcomeChanged.emit(outcome)

    def _changeProgress(self, progress: bool):
        if progress:
            self.swap(SceneStructureItemType.PROGRESS)
        else:
            self.swap(SceneStructureItemType.SETBACK)

    @overrides
    def _glow(self) -> QColor:
        color = super(SceneStructureBeatWidget, self)._glow()
        qtanim.glow(self._text, color=color)

        return color


class SceneStructureEmotionWidget(SceneStructureItemWidget):

    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None, readOnly: bool = False):
        super(SceneStructureEmotionWidget, self).__init__(novel, scene_structure_item, parent, readOnly)

        self._initStyle()

    @overrides
    def copy(self) -> 'SceneStructureItemWidget':
        return SceneStructureEmotionWidget(self.novel, self.beat)

    @overrides
    def _initStyle(self):
        super(SceneStructureEmotionWidget, self)._initStyle()

        self._btnName.setText(self.beat.emotion.lower().capitalize().replace('_', ' '))
        emotion = emotions[self.beat.emotion]
        color = self._color()
        if emotion.weight == 1:
            icon = IconRegistry.from_name('fa5s.sad-cry', color)
        elif emotion.weight == 2:
            icon = IconRegistry.from_name('mdi.emoticon-sad', color)
        elif emotion.weight == 4:
            icon = IconRegistry.from_name('fa5s.smile', color)
        elif emotion.weight == 5:
            icon = IconRegistry.from_name('fa5s.smile-beam', color)
        else:
            icon = IconRegistry.from_name('mdi.emoticon-neutral', color)

        self._btnIcon.setIcon(icon)


class SceneStructureTimeline(QWidget):
    emotionChanged = pyqtSignal()
    outcomeChanged = pyqtSignal()
    timelineChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._novel: Optional[Novel] = None
        self._scene: Optional[Scene] = None
        self._readOnly: bool = False
        sp(self).h_exp().v_exp()
        curved_flow(self, margin=10, spacing=10)

        self._agenda: Optional[SceneStructureAgenda] = None
        self._structure: List[SceneStructureItem] = []
        self._beatWidgets: List[SceneStructureItemWidget] = []

        self._currentPlaceholder: Optional[QWidget] = None
        self._menuEmotions = EmotionSelectorMenu()
        self._menuEmotions.emotionSelected.connect(self._insertEmotion)

        self._selectorMenu = BeatSelectorMenu(self)
        self._selectorMenu.selected.connect(self._insertBeat)

        self._dragPlaceholder: Optional[SceneStructureItemWidget] = None
        self._dragPlaceholderIndex: int = -1
        self._dragged: Optional[SceneStructureItemWidget] = None
        self._wasDropped: bool = False

        self.setAcceptDrops(True)

    def setNovel(self, novel: Novel):
        self._novel = novel

    def setScene(self, scene: Scene):
        self._scene = scene

    def setReadnOnly(self, readOnly: bool):
        self._readOnly = readOnly

    def clear(self):
        self._beatWidgets.clear()
        clear_layout(self)
        self._selectorMenu.setOutcomeEnabled(True)

    def setStructure(self, items: List[SceneStructureItem]):
        self.clear()

        self._structure = items

        for item in items:
            self._addBeatWidget(item)
        if not items:
            self.layout().addWidget(self._newPlaceholderWidget(displayText=True))

        self.update()

    def refreshOutcome(self):
        for wdg in self._beatWidgets:
            if isinstance(wdg, SceneStructureBeatWidget):
                if wdg.hasOutcome():
                    wdg.setOutcome(self._scene.outcome)

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(0.5)

        pen = QPen()
        pen.setColor(QColor('grey'))

        pen.setWidth(3)
        painter.setPen(pen)

        path = QPainterPath()

        forward = True
        y = 0
        for i, wdg in enumerate(self._beatWidgets):
            pos: QPoint = wdg.pos()
            pos.setY(pos.y() + wdg.layout().contentsMargins().top())
            if isinstance(wdg, SceneStructureItemWidget):
                pos.setY(pos.y() + wdg.iconFixedSize // 2)
            pos.setX(pos.x() + wdg.layout().contentsMargins().left())
            if i == 0:
                y = pos.y()
                path.moveTo(pos.toPointF())
                painter.drawLine(pos.x(), y - 10, pos.x(), y + 10)
            else:
                if pos.y() > y:
                    if forward:
                        path.arcTo(QRectF(pos.x() + wdg.width(), y, 60, pos.y() - y),
                                   90, -180)
                    else:
                        path.arcTo(QRectF(pos.x(), y, 60, pos.y() - y), -270, 180)
                    forward = not forward
                    y = pos.y()

            if forward:
                pos.setX(pos.x() + wdg.width())
            path.lineTo(pos.toPointF())

        painter.drawPath(path)
        if self._beatWidgets:
            if forward:
                x_arrow_diff = -10
            else:
                x_arrow_diff = 10
            painter.drawLine(pos.x(), y, pos.x() + x_arrow_diff, y + 10)
            painter.drawLine(pos.x(), y, pos.x() + x_arrow_diff, y - 10)

    def _addBeat(self, beatType: SceneStructureItemType):
        item = SceneStructureItem(beatType)
        if beatType == SceneStructureItemType.CLIMAX:
            item.outcome = SceneOutcome.DISASTER
        self._structure.append(item)
        self._addBeatWidget(item)

    def _addBeatWidget(self, item: SceneStructureItem):
        widget = self._newBeatWidget(item)
        self._beatWidgets.append(widget)
        if self.layout().count() == 0:
            self.layout().addWidget(self._newPlaceholderWidget())
        self.layout().addWidget(widget)
        self.layout().addWidget(self._newPlaceholderWidget())
        widget.activate()
        self.timelineChanged.emit()

    def _insertBeat(self, beatType: SceneStructureItemType):
        if beatType == SceneStructureItemType.EMOTION:
            self._menuEmotions.exec(self.mapToGlobal(self._currentPlaceholder.pos()))
            return

        item = SceneStructureItem(beatType)
        widget = self._newBeatWidget(item)
        self._insertWidget(item, widget)

    def _insertEmotion(self, emotion: str):
        item = SceneStructureItem(SceneStructureItemType.EMOTION, emotion=emotion)
        widget = self._newBeatWidget(item)
        self._insertWidget(item, widget)

    def _insertWidget(self, item: SceneStructureItem, widget: SceneStructureItemWidget):
        i = self.layout().indexOf(self._currentPlaceholder)
        self.layout().removeWidget(self._currentPlaceholder)
        gc(self._currentPlaceholder)
        self._currentPlaceholder = None

        beat_index = i // 2
        self._beatWidgets.insert(beat_index, widget)
        self._structure.insert(beat_index, item)
        self.layout().insertWidget(i, widget)
        self.layout().insertWidget(i + 1, self._newPlaceholderWidget())
        self.layout().insertWidget(i, self._newPlaceholderWidget())
        fade_in(widget, teardown=widget.activate)
        self.update()
        self.timelineChanged.emit()

    def _newBeatWidget(self, item: SceneStructureItem) -> SceneStructureBeatWidget:
        if item.type == SceneStructureItemType.EMOTION:
            clazz = SceneStructureEmotionWidget
        else:
            clazz = SceneStructureBeatWidget
        widget = clazz(self._novel, item, parent=self, readOnly=self._readOnly)
        widget.removed.connect(self._beatRemoved)
        if item.type == SceneStructureItemType.CLIMAX:
            self._selectorMenu.setOutcomeEnabled(False)
            widget.setOutcome(self._scene.outcome)
            widget.outcomeChanged.connect(self._outcomeChanged)
        widget.dragStarted.connect(partial(self._dragStarted, widget))
        widget.dragStopped.connect(self._dragFinished)

        if not self._readOnly:
            widget.installEventFilter(DropEventFilter(widget, [SceneStructureItemWidget.SceneBeatMimeType],
                                                      motionDetection=Qt.Orientation.Horizontal,
                                                      motionSlot=partial(self._dragMoved, widget),
                                                      droppedSlot=self._dropped))

        return widget

    def _newPlaceholderWidget(self, displayText: bool = False) -> QWidget:
        parent = _PlaceholderWidget()
        if displayText:
            parent.btn.setText('Insert beat')
        parent.btn.clicked.connect(partial(self._showBeatMenu, parent))

        if self._readOnly:
            parent.setHidden(True)

        return parent

    def _showBeatMenu(self, placeholder: QWidget):
        self._currentPlaceholder = placeholder
        self._selectorMenu.exec(self.mapToGlobal(self._currentPlaceholder.pos()))

    def _beatRemoved(self, wdg: SceneStructureBeatWidget):
        i = self.layout().indexOf(wdg)
        self._structure.remove(wdg.beat)
        self._beatWidgets.remove(wdg)
        if wdg.beat.type == SceneStructureItemType.CLIMAX:
            self._selectorMenu.setOutcomeEnabled(True)
        placeholder_prev = self.layout().takeAt(i - 1).widget()
        gc(placeholder_prev)
        fade_out_and_gc(self, wdg)
        self.update()

        self.timelineChanged.emit()

    def _outcomeChanged(self, outcome: SceneOutcome):
        self._scene.outcome = outcome
        self.outcomeChanged.emit()

    @overrides
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(SceneStructureItemWidget.SceneBeatMimeType):
            event.accept()
        else:
            event.ignore()

    def _dragStarted(self, widget: SceneStructureBeatWidget):
        self._dragPlaceholder = widget.copy()
        self._dragged = widget
        self._dragged.setHidden(True)
        translucent(self._dragPlaceholder)
        self._dragPlaceholder.setHidden(True)
        self._dragPlaceholder.setAcceptDrops(True)
        self._dragPlaceholder.installEventFilter(
            DropEventFilter(self._dragPlaceholder, mimeTypes=[SceneStructureItemWidget.SceneBeatMimeType],
                            droppedSlot=self._dropped))

    def _dragMoved(self, widget: QWidget, edge: Qt.Edge, _: QPoint):
        i = self.layout().indexOf(widget)
        if edge == Qt.Edge.LeftEdge:
            new_index = i - 1
        else:
            new_index = i + 2

        if self._dragPlaceholderIndex != new_index:
            self._dragPlaceholderIndex = new_index
            self.layout().insertWidget(self._dragPlaceholderIndex, self._dragPlaceholder)
            self._dragPlaceholder.setVisible(True)
            self.update()

    def _dropped(self, _: QMimeData):
        wdg = self._newBeatWidget(self._dragged.beat)
        i = self.layout().indexOf(self._dragPlaceholder)
        self.layout().insertWidget(i, wdg)

        self.layout().removeWidget(self._dragPlaceholder)
        gc(self._dragPlaceholder)
        self._dragPlaceholder = None
        self._dragPlaceholderIndex = -1

        beats: List[SceneStructureItemWidget] = []
        is_placeholder = False
        is_beat = True
        i = 0
        while i < self.layout().count():
            item = self.layout().itemAt(i)
            if item.widget() and isinstance(item.widget(), _PlaceholderWidget):
                if is_placeholder:
                    gc(item.widget())
                    continue
                is_placeholder = True
                is_beat = False
            elif item.widget() is not self._dragged:
                beats.append(item.widget())
                is_placeholder = False
                if is_beat:
                    self.layout().insertWidget(i, self._newPlaceholderWidget())
                    is_beat = False
                    i += 1
                else:
                    is_beat = True

            i += 1

        self._beatWidgets[:] = beats
        self._structure[:] = [x.beat for x in self._beatWidgets]
        self._wasDropped = True

    def _dragFinished(self):
        if self._dragPlaceholder is not None:
            self._dragPlaceholder.setHidden(True)
            gc(self._dragPlaceholder)

        if self._wasDropped:
            self._dragged.setHidden(True)
            self.layout().removeWidget(self._dragged)
            gc(self._dragged)
        else:
            self._dragged.setVisible(True)

        self._dragPlaceholder = None
        self._dragPlaceholderIndex = -1
        self._dragged = None
        self._wasDropped = False
        self.update()


class BeatListItemWidget(ListItemWidget):
    def __init__(self, beat: SceneStructureItem, parent=None):
        super(BeatListItemWidget, self).__init__(beat, parent)
        self._beat = beat
        self._lineEdit.setMaximumWidth(600)
        self.layout().addWidget(spacer())
        self.refresh()

    def refresh(self):
        self._lineEdit.setText(self._beat.text)

    @overrides
    def _textChanged(self, text: str):
        super(BeatListItemWidget, self)._textChanged(text)
        self._beat.text = text


class SceneStructureList(ListView):
    def __init__(self, parent=None):
        super(SceneStructureList, self).__init__(parent)
        self._agenda: Optional[SceneStructureAgenda] = None
        self._centralWidget.setProperty('relaxed-white-bg', True)

    def setAgenda(self, agenda: SceneStructureAgenda, purpose: Optional[ScenePurposeType] = None):
        self._agenda = agenda
        self.refresh()

    def refresh(self):
        self.clear()

        for beat in self._agenda.items:
            self.addItem(beat)

    @overrides
    def _addNewItem(self):
        beat = SceneStructureItem(SceneStructureItemType.EXPOSITION)
        self._agenda.items.append(beat)
        self.addItem(beat)

    @overrides
    def _listItemWidgetClass(self):
        return BeatListItemWidget

    @overrides
    def _deleteItemWidget(self, widget: ListItemWidget):
        super(SceneStructureList, self)._deleteItemWidget(widget)
        self._agenda.items.remove(widget.item())

    @overrides
    def _dropped(self, mimeData: ObjectReferenceMimeData):
        super(SceneStructureList, self)._dropped(mimeData)
        self._agenda.items.clear()

        for wdg in self.widgets():
            self._agenda.items.append(wdg.item())


class SceneStructureWidget(QWidget, Ui_SceneStructureWidget):

    def __init__(self, parent=None):
        super(SceneStructureWidget, self).__init__(parent)
        self.setupUi(self)

        self._btnTemplates = QPushButton('Apply template', self)
        self._btnTemplates.setIcon(IconRegistry.from_name('ei.magic'))
        transparent(self._btnTemplates)
        pointy(self._btnTemplates)
        self._btnTemplates.installEventFilter(ButtonPressResizeEventFilter(self._btnTemplates))
        self._btnTemplates.installEventFilter(OpacityEventFilter(self._btnTemplates))
        self._btnTemplates.clicked.connect(self._showTemplates)

        self._btnMenu = DotsMenuButton(self)
        self._contextMenu = MenuWidget(self._btnMenu)
        self._contextMenu.addAction(
            action('Apply template', IconRegistry.from_name('ei.magic'), slot=self._showTemplates))
        self._contextMenu.addSeparator()
        self._contextMenu.addAction(action('Reset structure', IconRegistry.trash_can_icon(), slot=self._reset))

        margins(self.wdgTimelineHeader, top=5, left=10)
        self.wdgTimelineHeader.layout().addWidget(self._btnTemplates)
        self.wdgTimelineHeader.layout().addWidget(spacer())
        self.wdgTimelineHeader.layout().addWidget(self._btnMenu)

        self.novel: Optional[Novel] = None
        self.scene: Optional[Scene] = None

        self.timeline = SceneStructureTimeline(self)
        self.scrollAreaTimeline.layout().addWidget(self.timeline)

        self.listEvents = SceneStructureList()
        self.pageList.layout().addWidget(self.listEvents)

        # self._disabledAgendaEventFilter = None

    def setUnsetCharacterSlot(self, unsetCharacterSlot):
        pass
        # if self._disabledAgendaEventFilter:
        #     self.wdgAgendaCharacter.btnLinkCharacter.removeEventFilter(self._disabledAgendaEventFilter)
        #
        # self._disabledAgendaEventFilter = DisabledClickEventFilter(self, unsetCharacterSlot)
        # self.wdgAgendaCharacter.btnLinkCharacter.installEventFilter(self._disabledAgendaEventFilter)

    def setScene(self, novel: Novel, scene: Scene):
        self.novel = novel
        self.scene = scene

        self.timeline.setNovel(novel)
        self.timeline.setScene(scene)
        self.timeline.clear()

        self.timeline.setStructure(scene.agendas[0].items)
        self.listEvents.setAgenda(scene.agendas[0], self.scene.purpose)
        self._initEditor(self.scene.purpose)

    def refreshOutcome(self):
        self.timeline.refreshOutcome()

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        if not any([x for x in self.scene.agendas[0].items if x.text]):
            self._btnTemplates.setVisible(True)

        self._btnMenu.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        if not self._btnMenu.menu().isVisible():
            self._btnMenu.setHidden(True)
        self._btnTemplates.setHidden(True)

    def updateAvailableAgendaCharacters(self):
        pass
        # chars = []
        # chars.extend(self.scene.characters)
        # if self.scene.pov:
        #     chars.insert(0, self.scene.pov)
        # self.wdgAgendaCharacter.setAvailableCharacters(chars)

    def updateAgendaCharacter(self):
        pass
        # self._toggleCharacterStatus()
        # self._initSelectors()

    def _initEditor(self, purpose: ScenePurposeType):
        if purpose == ScenePurposeType.Exposition:
            self.stackStructure.setCurrentWidget(self.pageList)
            self.lblSummary.setHidden(True)
            self.lblExposition.setVisible(True)
            self.listEvents.refresh()
        # elif purpose == SceneType.SUMMARY:
        #     self.stackStructure.setCurrentWidget(self.pageList)
        #     self.lblSummary.setVisible(True)
        #     self.lblExposition.setHidden(True)
        #     self.listEvents.refresh()
        else:
            self.stackStructure.setCurrentWidget(self.pageTimetilne)

    def _showTemplates(self):
        selector = SceneStructureTemplateSelector()
        structure = selector.display()
        if structure:
            self.scene.agendas[0].items.clear()
            self.scene.agendas[0].items.extend(structure)
            self.timeline.setStructure(structure)

    def _reset(self):
        pass


class SceneStructureTemplateSelector(QDialog, Ui_SceneStructuteTemplateSelector):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self._structure: SceneStructureAgenda = SceneStructureAgenda()

        self._timeline = SceneStructureTimeline()
        self._timeline.setReadnOnly(True)
        self.scrollAreaTimeline.layout().addWidget(self._timeline)

        sp(self.btnScene).v_fixed()
        sp(self.btnSequel).v_fixed()

        self.buttonGroup.buttonToggled.connect(self._templateToggled)

    def display(self) -> List[SceneStructureItem]:
        self.btnScene.setChecked(True)

        screen = QApplication.screenAt(self.pos())
        if screen:
            self.resize(int(screen.size().width() * 0.7), int(screen.size().height() * 0.5))
        else:
            self.resize(600, 500)

        result = self.exec()
        if result == QDialog.DialogCode.Accepted:
            return self._structure.items
        else:
            return []

    def _templateToggled(self):
        if self.btnScene.isChecked():
            self._fillInSceneTemplate()
        elif self.btnSequel.isChecked():
            self._fillInSequelTemplate()

        self._timeline.setStructure(self._structure.items)

        QTimer.singleShot(10, self._timeline.update)

    def _fillInSceneTemplate(self):
        self._structure.items.clear()
        self._structure.items.extend([
            SceneStructureItem(SceneStructureItemType.ACTION),
            SceneStructureItem(SceneStructureItemType.CONFLICT),
            SceneStructureItem(SceneStructureItemType.CLIMAX)
        ])

        self.textBrowser.setText('Scene template')

    def _fillInSequelTemplate(self):
        self._structure.items.clear()
        self._structure.items.extend([
            SceneStructureItem(SceneStructureItemType.REACTION),
            SceneStructureItem(SceneStructureItemType.DILEMMA),
            SceneStructureItem(SceneStructureItemType.DECISION)
        ])

        self.textBrowser.setText('Sequel template')
