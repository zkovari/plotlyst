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
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF, QEvent, QPoint, QMimeData
from PyQt6.QtGui import QIcon, QColor, QPainter, QPen, \
    QPainterPath, QPaintEvent, QAction, QResizeEvent, QEnterEvent, QDragEnterEvent
from PyQt6.QtWidgets import QWidget, QToolButton, QPushButton, QSizePolicy, QTextEdit
from overrides import overrides
from qtanim import fade_in
from qthandy import pointy, gc, translucent, bold, clear_layout, decr_font, \
    margins, spacer, sp, curved_flow, incr_icon, vbox
from qthandy.filter import OpacityEventFilter, ObjectReferenceMimeData, DragEventFilter, DropEventFilter
from qtmenu import ScrollableMenuWidget, ActionTooltipDisplayMode, GridMenuWidget, MenuWidget

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Novel, Scene, SceneStructureItemType, SceneType, \
    SceneStructureItem, SceneOutcome, SceneStructureAgenda
from src.main.python.plotlyst.view.common import action, fade_out_and_gc, ButtonPressResizeEventFilter
from src.main.python.plotlyst.view.generated.scene_structure_editor_widget_ui import Ui_SceneStructureWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.style.base import apply_white_menu
from src.main.python.plotlyst.view.widget.input import RemovalButton
from src.main.python.plotlyst.view.widget.list import ListView, ListItemWidget
from src.main.python.plotlyst.view.widget.scenes import SceneOutcomeSelector

BeatDescriptions = {SceneStructureItemType.BEAT: 'New action, reaction, thought, or emotion',
                    SceneStructureItemType.ACTION: 'Character takes an action to achieve their goal',
                    SceneStructureItemType.CONFLICT: "Conflict hinders the character's goals",
                    SceneStructureItemType.OUTCOME: 'Outcome of the scene, typically ending with disaster',
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
    else:
        return IconRegistry.circle_icon()


HAPPENING_BEATS = (SceneStructureItemType.BEAT, SceneStructureItemType.EXPOSITION, SceneStructureItemType.SETUP,
                   SceneStructureItemType.HOOK, SceneStructureItemType.MYSTERY, SceneStructureItemType.EXPOSITION)


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
        elif type == SceneType.REACTION:
            bgColor = '#bee1e6'
            borderColor = '#168aad'
            bgColorChecked = '#89c2d9'
            borderColorChecked = '#1a759f'
            self.setText('Sequel (reaction)')
            self.setIcon(IconRegistry.reaction_scene_icon())
        else:
            bgColor = 'lightgrey'
            borderColor = 'grey'
            bgColorChecked = 'darkGrey'
            borderColorChecked = 'grey'
            self.setText(type.name.capitalize())
        if type == SceneType.EXPOSITION:
            self.setIcon(IconRegistry.exposition_scene_icon())
        elif type == SceneType.SUMMARY:
            self.setIcon(IconRegistry.summary_scene_icon())
        elif type == SceneType.HAPPENING:
            self.setIcon(IconRegistry.happening_scene_icon())

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


class BeatSelectorMenu(GridMenuWidget):
    selected = pyqtSignal(SceneStructureItemType)

    def __init__(self, parent=None):
        super(BeatSelectorMenu, self).__init__(parent)

        self._actions: Dict[SceneStructureItemType, QAction] = {}
        self._outcomeEnabled: bool = True

        self.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
        self.setSearchEnabled(True)
        apply_white_menu(self)

        self.addSection('Scene beats', 0, 0, icon=IconRegistry.action_scene_icon())
        self.addSeparator(1, 0, colSpan=2)
        self._addAction('Action', SceneStructureItemType.ACTION, 2, 0)
        self._addAction('Hook', SceneStructureItemType.HOOK, 2, 1)
        self._addAction('Inciting incident', SceneStructureItemType.INCITING_INCIDENT, 3, 0)
        self._addAction('Mystery', SceneStructureItemType.MYSTERY, 3, 1)
        self._addAction('Conflict', SceneStructureItemType.CONFLICT, 4, 0)
        self._addAction('Rising action', SceneStructureItemType.RISING_ACTION, 4, 1)
        self._addAction('Turn', SceneStructureItemType.TURN, 5, 0)
        self._addAction('Choice', SceneStructureItemType.CHOICE, 5, 1)
        self._addAction('Revelation', SceneStructureItemType.REVELATION, 6, 0)
        self._addAction('Outcome', SceneStructureItemType.OUTCOME, 6, 1)
        self.addSection('Sequel beats', 7, 0, icon=IconRegistry.reaction_scene_icon())
        self.addSeparator(8, 0)
        self._addAction('Reaction', SceneStructureItemType.REACTION, 9, 0)
        self._addAction('Emotion', SceneStructureItemType.EMOTION, 10, 0)
        self._addAction('Dilemma', SceneStructureItemType.DILEMMA, 11, 0)
        self._addAction('Decision', SceneStructureItemType.DECISION, 12, 0)
        self.addSection('General beats', 7, 1)
        self.addSeparator(8, 1)
        self._addAction('Beat', SceneStructureItemType.BEAT, 9, 1)
        self._addAction('Exposition', SceneStructureItemType.EXPOSITION, 10, 1)
        self._addAction('Summary', SceneStructureItemType.SUMMARY, 11, 1)
        self._addAction('Setup', SceneStructureItemType.SETUP, 12, 1)

    def _addAction(self, text: str, beat_type: SceneStructureItemType, row: int, column: int):
        description = BeatDescriptions[beat_type]
        action_ = action(text, beat_icon(beat_type), slot=lambda: self.selected.emit(beat_type), tooltip=description)
        self._actions[beat_type] = action_
        self.addAction(action_, row, column)

    def setOutcomeEnabled(self, enabled: bool):
        self._outcomeEnabled = enabled
        self._actions[SceneStructureItemType.OUTCOME].setEnabled(enabled)

    def toggleSceneType(self, sceneType: SceneType):
        for action_ in self._actions.values():
            action_.setEnabled(True)
        self._actions[SceneStructureItemType.OUTCOME].setEnabled(self._outcomeEnabled)
        if sceneType == SceneType.REACTION:
            for type_ in [SceneStructureItemType.ACTION, SceneStructureItemType.HOOK,
                          SceneStructureItemType.RISING_ACTION, SceneStructureItemType.INCITING_INCIDENT,
                          SceneStructureItemType.CONFLICT, SceneStructureItemType.OUTCOME, SceneStructureItemType.TURN]:
                self._actions[type_].setEnabled(False)
        elif sceneType == SceneType.HAPPENING:
            for type_ in [SceneStructureItemType.ACTION, SceneStructureItemType.HOOK,
                          SceneStructureItemType.RISING_ACTION, SceneStructureItemType.INCITING_INCIDENT,
                          SceneStructureItemType.CONFLICT, SceneStructureItemType.OUTCOME, SceneStructureItemType.TURN,
                          SceneStructureItemType.CHOICE, SceneStructureItemType.REACTION,
                          SceneStructureItemType.DILEMMA, SceneStructureItemType.DECISION]:
                self._actions[type_].setEnabled(False)


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

    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneStructureItemWidget, self).__init__(parent)
        self.novel = novel
        self.beat = scene_structure_item
        vbox(self, 0, 0)

        self._btnName = QPushButton()
        bold(self._btnName)

        self._btnIcon = QToolButton(self)
        pointy(self._btnIcon)
        self._btnIcon.setIconSize(QSize(24, 24))
        self._btnIcon.setCursor(Qt.CursorShape.OpenHandCursor)
        self._btnIcon.setFixedSize(self.iconFixedSize, self.iconFixedSize)

        self._btnRemove = RemovalButton(self)
        self._btnRemove.setHidden(True)
        self._btnRemove.clicked.connect(self._remove)

        self.layout().addWidget(self._btnIcon, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._btnName, alignment=Qt.AlignmentFlag.AlignCenter)

        self._btnIcon.installEventFilter(DragEventFilter(self, self.SceneBeatMimeType, self._beatDataFunc,
                                                         grabbed=self._btnIcon, startedSlot=self.dragStarted.emit,
                                                         finishedSlot=self.dragStopped.emit))

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
        elif self.beat.type == SceneStructureItemType.OUTCOME:
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
        else:
            return '#343a40'

    def _glow(self) -> QColor:
        color = QColor(self._color())
        qtanim.glow(self._btnName, color=color)

        return color


class SceneStructureBeatWidget(SceneStructureItemWidget):
    emotionChanged = pyqtSignal()

    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneStructureBeatWidget, self).__init__(novel, scene_structure_item, parent)
        self.setFixedWidth(210)

        self._outcome = SceneOutcomeSelector(self.beat)
        self._outcome.selected.connect(self._outcomeChanged)

        self._text = QTextEdit()
        decr_font(self._text)
        self._text.setProperty('rounded', True)
        self._text.setFixedHeight(100)
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

    def outcomeVisible(self) -> bool:
        return self._outcome.isVisible()

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
            if self.beat.type == SceneStructureItemType.OUTCOME:
                if self.beat.outcome is None:
                    self.beat.outcome = SceneOutcome.DISASTER
                self._outcome.refresh()
            self._initStyle()
        self._glow()

    @overrides
    def _initStyle(self):
        super(SceneStructureBeatWidget, self)._initStyle()

        self._outcome.setVisible(self.beat.type == SceneStructureItemType.OUTCOME)
        if self.isEmotion():
            desc = "How is the character's emotion shown?"
        else:
            desc = BeatDescriptions[self.beat.type]
        self._text.setPlaceholderText(desc)
        self._btnName.setToolTip(desc)
        self._text.setToolTip(desc)
        self._btnIcon.setToolTip(desc)

        self._text.setHidden(self.isEmotion())
        if self.beat.type == SceneStructureItemType.OUTCOME:
            if self.beat.outcome is None:
                self.beat.outcome = SceneOutcome.DISASTER
            name = SceneOutcome.to_str(self.beat.outcome)
            self._outcome.refresh()
        elif self.isEmotion():
            name = self.beat.emotion
        else:
            name = self.beat.type.name
        self._btnName.setText(name.lower().capitalize().replace('_', ' '))
        self._btnIcon.setIcon(beat_icon(self.beat.type, resolved=self.beat.outcome == SceneOutcome.RESOLUTION,
                                        trade_off=self.beat.outcome == SceneOutcome.TRADE_OFF))

    def _textChanged(self):
        self.beat.text = self._text.toPlainText()

    def _outcomeChanged(self):
        self._initStyle()
        self._glow()

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

    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneStructureEmotionWidget, self).__init__(novel, scene_structure_item, parent)

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
    timelineChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(SceneStructureTimeline, self).__init__(parent)
        self._novel: Optional[Novel] = None
        sp(self).h_exp().v_exp()
        curved_flow(self, margin=10, spacing=10)

        self._agenda: Optional[SceneStructureAgenda] = None
        self._sceneType: Optional[SceneType] = None
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

    def clear(self):
        clear_layout(self)
        for wdg in self._beatWidgets:
            gc(wdg)
        self._beatWidgets.clear()
        self._selectorMenu.setOutcomeEnabled(True)
        self.update()

    def setSceneType(self, sceneType: SceneType):
        self._sceneType = sceneType
        self._selectorMenu.toggleSceneType(sceneType)
        self.update()

    def setAgenda(self, agenda: SceneStructureAgenda, sceneType: SceneType):
        self.clear()

        self._agenda = agenda
        for item in agenda.items:
            self._addBeatWidget(item)
        if not agenda.items:
            self.layout().addWidget(self._newPlaceholderWidget(displayText=True))

        self.setSceneType(sceneType)

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
        if beatType == SceneStructureItemType.OUTCOME:
            item.outcome = SceneOutcome.DISASTER
        self._agenda.items.append(item)
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
        self._agenda.items.insert(beat_index, item)
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
        widget = clazz(self._novel, item, parent=self)
        widget.removed.connect(self._beatRemoved)
        if item.type == SceneStructureItemType.OUTCOME:
            self._selectorMenu.setOutcomeEnabled(False)
        widget.dragStarted.connect(partial(self._dragStarted, widget))
        widget.dragStopped.connect(self._dragFinished)

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

        return parent

    def _showBeatMenu(self, placeholder: QWidget):
        self._currentPlaceholder = placeholder
        self._selectorMenu.exec(self.mapToGlobal(self._currentPlaceholder.pos()))

    def _beatRemoved(self, wdg: SceneStructureBeatWidget):
        i = self.layout().indexOf(wdg)
        self._agenda.items.remove(wdg.beat)
        self._beatWidgets.remove(wdg)
        if wdg.beat.type == SceneStructureItemType.OUTCOME:
            self._selectorMenu.setOutcomeEnabled(True)
        placeholder_prev = self.layout().takeAt(i - 1).widget()
        gc(placeholder_prev)
        fade_out_and_gc(self, wdg)
        self.update()

        self.timelineChanged.emit()

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
        self._dragPlaceholder.setVisible(True)
        i = self.layout().indexOf(widget)
        if edge == Qt.Edge.LeftEdge:
            new_index = i - 1
        else:
            new_index = i + 2

        if self._dragPlaceholderIndex != new_index:
            self._dragPlaceholderIndex = new_index
            self.layout().insertWidget(self._dragPlaceholderIndex, self._dragPlaceholder)
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
        self._agenda.items[:] = [x.beat for x in self._beatWidgets]
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


# class _SceneStructureTimeline(QWidget):
#     emotionChanged = pyqtSignal()
#     timelineChanged = pyqtSignal()
#
#     def __init__(self, parent=None):
#         super(_SceneStructureTimeline, self).__init__(parent)
#         self._topMargin = 20
#         self._margin = 80
#         self._lineDistance = 170
#         self._arcWidth = 80
#         self._beatWidth: int = 180
#         self._emotionSize: int = 32
#         self._penSize: int = 10
#         self._path: Optional[QPainterPath] = None
#
#         self._dragPlaceholder: Optional[SceneStructureBeatWidget] = None
#
#         self.setMouseTracking(True)
#
#
#     @overrides
#     def mouseMoveEvent(self, event: QMouseEvent) -> None:
#         if not self._intersects(event.pos()):
#             if self._placeholder.isVisible():
#                 self._placeholder.setVisible(False)
#                 self.update()
#             return
#
#         self._placeholder.setVisible(True)
#         vertical_index = self._verticalTimelineIndex(event.pos())
#         self._placeholder.setGeometry(event.pos().x() - self._placeholder.width() / 2,
#                                       vertical_index * self._lineDistance + self._lineDistance / 2 + self._penSize,
#                                       self._placeholder.width(),
#                                       self._placeholder.height())
#         self.update()
#
#     def _initDragPlaceholder(self, widget: SceneStructureBeatWidget):
#         self._dragPlaceholder = SceneStructureBeatWidget(self.novel, widget.sceneStructureItem(), parent=self)
#         self._dragPlaceholder.setDisabled(True)
#         translucent(self._dragPlaceholder)
#         self._dragPlaceholder.setHidden(True)
#
#     def _resetDragPlaceholder(self):
#         if self._dragPlaceholder is not None:
#             self._dragPlaceholder.setHidden(True)
#             gc(self._dragPlaceholder)
#             self._dragPlaceholder = None


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

    def setAgenda(self, agenda: SceneStructureAgenda, sceneType: SceneType):
        self._agenda = agenda
        self.refresh(sceneType)

    def refresh(self, sceneType: SceneType):
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
        self.timeline.clear()

        self.timeline.setAgenda(scene.agendas[0], self.scene.type)
        self.listEvents.setAgenda(scene.agendas[0], self.scene.type)
        self._initEditor(self.scene.type)

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

    def _initEditor(self, type: SceneType):
        if type == SceneType.EXPOSITION:
            self.stackStructure.setCurrentWidget(self.pageList)
            self.lblSummary.setHidden(True)
            self.lblExposition.setVisible(True)
            self.listEvents.refresh(type)
        elif type == SceneType.SUMMARY:
            self.stackStructure.setCurrentWidget(self.pageList)
            self.lblSummary.setVisible(True)
            self.lblExposition.setHidden(True)
            self.listEvents.refresh(type)
        else:
            self.stackStructure.setCurrentWidget(self.pageTimetilne)
            self.timeline.setSceneType(self.scene.type)
