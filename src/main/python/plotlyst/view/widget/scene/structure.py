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
import pickle
import sys
from functools import partial
from typing import Optional, List, Dict

import qtanim
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF
from PyQt6.QtGui import QIcon, QColor, QDropEvent, QDragEnterEvent, QDragMoveEvent, QMouseEvent, QPainter, QResizeEvent, \
    QPen, QPainterPath, QPaintEvent, QLinearGradient, QEnterEvent
from PyQt6.QtWidgets import QWidget, QToolButton, QPushButton, QSizePolicy, QMainWindow, QApplication
from overrides import overrides
from qtanim import fade_in
from qthandy import pointy, gc, translucent, bold, retain_when_hidden, flow, clear_layout, decr_font, \
    margins, spacer, sp, curved_flow, incr_icon
from qthandy.filter import OpacityEventFilter, DragEventFilter, DisabledClickEventFilter, \
    ObjectReferenceMimeData, VisibilityToggleEventFilter
from qtmenu import ScrollableMenuWidget, ActionTooltipDisplayMode, GridMenuWidget

from src.main.python.plotlyst.common import emotion_color, RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Character, Novel, Scene, SceneStructureItemType, SceneType, \
    SceneStructureItem, SceneOutcome, SceneStructureAgenda, CharacterGoal, GoalReference, Conflict, ConflictReference
from src.main.python.plotlyst.view.common import action, wrap, fade_out_and_gc, ButtonPressResizeEventFilter
from src.main.python.plotlyst.view.generated.scene_beat_item_widget_ui import Ui_SceneBeatItemWidget
from src.main.python.plotlyst.view.generated.scene_structure_editor_widget_ui import Ui_SceneStructureWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import FadeOutButtonGroup
from src.main.python.plotlyst.view.widget.characters import CharacterEmotionButton, CharacterGoalSelector, \
    CharacterConflictSelector
from src.main.python.plotlyst.view.widget.labels import EmotionLabel
from src.main.python.plotlyst.view.widget.list import ListView, ListItemWidget
from src.main.python.plotlyst.view.widget.scenes import SceneOutcomeSelector

BeatDescriptions = {SceneStructureItemType.BEAT: 'New action, reaction, thought, or emotion',
                    SceneStructureItemType.ACTION: 'Character takes an action to achieve their goal',
                    SceneStructureItemType.CONFLICT: "Conflict hinders the character's goals",
                    SceneStructureItemType.OUTCOME: 'Outcome of the scene, typically ending with disaster',
                    SceneStructureItemType.REACTION: "Initial reaction to a prior scene's outcome",
                    SceneStructureItemType.DILEMMA: 'Dilemma throughout the scene. What to do next?',
                    SceneStructureItemType.DECISION: 'Character makes a decision and may act right away',
                    SceneStructureItemType.HOOK: "Initial hook to raise readers' curiosity",
                    SceneStructureItemType.INCITING_INCIDENT: 'Triggers events in this scene',
                    SceneStructureItemType.TICKING_CLOCK: 'Ticking clock is activated to add urgency',
                    SceneStructureItemType.RISING_ACTION: 'Increasing progress or setback throughout the scene',
                    SceneStructureItemType.CHOICE: 'Impossible choice between two equally good or bad outcomes',
                    SceneStructureItemType.EXPOSITION: 'Description, explanation, or introduction of normal world',
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
    elif beat_type == SceneStructureItemType.CHOICE:
        return IconRegistry.crisis_icon()
    elif beat_type == SceneStructureItemType.EXPOSITION:
        return IconRegistry.exposition_icon()
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

emotions: Dict[str, str] = {'Admiration': '#008744', 'Adoration': '#7048e8', 'Amusement': '#ff6961', 'Anger': '#ff3333',
                            'Anxiety': '#ffbf00', 'Awe': '#87ceeb', 'Awkwardness': '#ff69b4', 'Boredom': '#778899',
                            'Calmness': '#1e90ff', 'Confusion': '#ffc107', 'Craving': '#ffdb58', 'Disgust': '#ffa500',
                            'Empathic': '#4da6ff', 'Pain': '#ff5050', 'Entrancement': '#00bfff',
                            'Excitement': '#ff5c5c', 'Fear': '#1f1f1f', 'Horror': '#ff4d4d', 'Interest': '#3cb371',
                            'Joy': '#00ff7f', 'Nostalgia': '#ffb347', 'Relief': '#00ff00', 'Sadness': '#999999',
                            'Satisfaction': '#228b22', 'Surprise': '#ff69b4'}


class EmotionSelectorButton(QToolButton):
    emotionSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super(EmotionSelectorButton, self).__init__(parent)
        self.setIcon(IconRegistry.from_name('ri.emotion-sad-line'))
        self.setProperty('transparent', True)
        pointy(self)
        incr_icon(self, 2)
        menuEmotions = ScrollableMenuWidget(self)
        menuEmotions.setMaximumHeight(300)
        for emotion in ['Admiration', 'Adoration', 'Amusement', 'Anger', 'Anxiety', 'Awe', 'Awkwardness', 'Boredom',
                        'Calmness', 'Confusion',
                        'Craving', 'Disgust', 'Empathic', 'Pain', 'Entrancement', 'Excitement', 'Fear', 'Horror',
                        'Interest', 'Joy', 'Nostalgia', 'Relief', 'Sadness', 'Satisfaction', 'Surprise']:
            menuEmotions.addAction(action(emotion, slot=partial(self.emotionSelected.emit, emotion)))

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


class _SceneBeatPlaceholderButton(QToolButton):
    selected = pyqtSignal(SceneStructureItemType)

    def __init__(self, parent=None):
        super(_SceneBeatPlaceholderButton, self).__init__(parent)
        self.setProperty('transparent', True)
        self.setIcon(IconRegistry.plus_circle_icon('grey'))
        self.installEventFilter(OpacityEventFilter(self))
        self.setIconSize(QSize(24, 24))
        # transparent(self)
        pointy(self)
        self.setToolTip('Insert new beat')

        self._menu = GridMenuWidget(self)
        self._menu.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
        self._menu.setStyleSheet(f'''
                MenuWidget {{
                    background-color: {RELAXED_WHITE_COLOR};
                }}
                QFrame {{
                    background-color: {RELAXED_WHITE_COLOR};
                    padding-left: 2px;
                    padding-right: 2px;
                    border-radius: 5px;
                }}
                MenuItemWidget:hover {{
                    background-color: #EDEDED;
                }}
                MenuItemWidget[pressed=true] {{
                    background-color: #DCDCDC;
                }}
                QLabel[description=true] {{
                    color: grey;
                }}
                ''')
        self._menu.addSection('Scene', 0, 0, icon=IconRegistry.action_scene_icon())
        self._menu.addSeparator(1, 0, colSpan=2)
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
        self._menu.addSection('Sequel', 7, 0, icon=IconRegistry.reaction_scene_icon())
        self._menu.addSeparator(8, 0)
        self._addAction('Reaction', SceneStructureItemType.REACTION, 9, 0)
        self._addAction('Dilemma', SceneStructureItemType.DILEMMA, 10, 0)
        self._addAction('Decision', SceneStructureItemType.DECISION, 11, 0)
        self._menu.addSection('General', 7, 1)
        self._menu.addSeparator(8, 1)
        self._addAction('Beat', SceneStructureItemType.BEAT, 9, 1)
        self._addAction('Exposition', SceneStructureItemType.EXPOSITION, 10, 1)
        self._addAction('Setup', SceneStructureItemType.SETUP, 11, 1)

    def _addAction(self, text: str, beat_type: SceneStructureItemType, row: int, column: int):
        description = BeatDescriptions[beat_type]
        self._menu.addAction(
            action(text, beat_icon(beat_type), slot=lambda: self.selected.emit(beat_type), tooltip=description), row,
            column)


BEAT_MIN_HEIGHT = 190


class SceneStructureItemWidget(QWidget, Ui_SceneBeatItemWidget):
    entered = pyqtSignal()
    removed = pyqtSignal(object)
    dragStarted = pyqtSignal()
    dragStopped = pyqtSignal()
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
        self.btnIcon.setCursor(Qt.CursorShape.OpenHandCursor)

        bold(self.btnName)

        decr_font(self.text)
        self.text.setText(self.beat.text)
        self.text.textChanged.connect(self._textChanged)

        self.lblEmotion = EmotionLabel()
        decr_font(self.lblEmotion)
        if self.beat.emotion:
            self.lblEmotion.setEmotion(self.beat.emotion, color=emotions.get(self.beat.emotion, 'red'))
        else:
            self.lblEmotion.setHidden(True)
        self.wdgEmotion.layout().addWidget(self.lblEmotion, alignment=Qt.AlignmentFlag.AlignLeft)
        self._btnEmotionSelector = EmotionSelectorButton(self)
        self._btnEmotionSelector.setIconSize(QSize(15, 15))
        self._btnEmotionSelector.emotionSelected.connect(self._emotionSelected)
        self.wdgEmotion.layout().addWidget(self._btnEmotionSelector, alignment=Qt.AlignmentFlag.AlignLeft)

        self._initStyle()

        self.btnDelete.clicked.connect(self._remove)
        self.installEventFilter(VisibilityToggleEventFilter(self.btnDelete, parent=self))
        self.installEventFilter(VisibilityToggleEventFilter(self._btnEmotionSelector, parent=self))
        self.installEventFilter(VisibilityToggleEventFilter(self.btnTag, parent=self))
        self.btnIcon.installEventFilter(DragEventFilter(self, self.SceneBeatMimeType, self._beatDataFunc,
                                                        grabbed=self.btnIcon, startedSlot=self.dragStarted.emit,
                                                        finishedSlot=self.dragStopped.emit,
                                                        hideTarget=True))
        retain_when_hidden(self.btnDelete)
        self.btnTag.setHidden(True)
        retain_when_hidden(self.btnTag)
        retain_when_hidden(self._btnEmotionSelector)

    def outcomeVisible(self) -> bool:
        return self._outcome.isVisible()

    def sceneStructureItem(self) -> SceneStructureItem:
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

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        self.entered.emit()

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
            if self.beat.outcome is None:
                self.beat.outcome = SceneOutcome.DISASTER
            name = SceneOutcome.to_str(self.beat.outcome)
        else:
            name = self.beat.type.name
        self.wdgEmotion.setHidden(self.beat.type == SceneStructureItemType.OUTCOME)
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
            return '#219ebc'
        elif self.beat.type == SceneStructureItemType.HOOK:
            return '#829399'
        elif self.beat.type == SceneStructureItemType.INCITING_INCIDENT:
            return '#a2ad59'
        elif self.beat.type == SceneStructureItemType.TICKING_CLOCK:
            return '#f7cb15'
        elif self.beat.type == SceneStructureItemType.RISING_ACTION:
            return '#08605f'
        elif self.beat.type == SceneStructureItemType.CHOICE:
            return '#ce2d4f'
        elif self.beat.type == SceneStructureItemType.EXPOSITION:
            return '#1ea896'
        elif self.beat.type == SceneStructureItemType.TURN:
            return '#8338ec'
        elif self.beat.type == SceneStructureItemType.MYSTERY:
            return '#b8c0ff'
        elif self.beat.type == SceneStructureItemType.REVELATION:
            return '#588157'
        elif self.beat.type == SceneStructureItemType.SETUP:
            return '#ddbea9'
        else:
            return 'black'

    def _remove(self):
        if self.parent():
            anim = qtanim.fade_out(self, duration=150)
            anim.finished.connect(lambda: self.removed.emit(self))

    def _textChanged(self):
        self.beat.text = self.text.toPlainText()

    def _outcomeChanged(self):
        self._initStyle()
        self._glow()

    def _emotionSelected(self, emotion: str):
        self.lblEmotion.setEmotion(emotion, color=emotions.get(emotion, 'red'))
        self.lblEmotion.setVisible(True)
        self.beat.emotion = emotion

    def _glow(self):
        color = QColor(self._color())
        qtanim.glow(self.btnName, color=color)
        qtanim.glow(self.text, color=color)


class SceneStructureTimeline(QWidget):
    emotionChanged = pyqtSignal()
    timelineChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(SceneStructureTimeline, self).__init__(parent)
        self._novel: Optional[Novel] = None
        sp(self).h_exp().v_exp()
        curved_flow(self, margin=10, spacing=10)

        self._agenda: Optional[SceneStructureAgenda] = None
        self._beatWidgets: List[SceneStructureItemWidget] = []

        self._emotionStart = CharacterEmotionButton(self)
        self._emotionStart.setToolTip('Beginning emotion')
        self._emotionStart.setVisible(False)
        self._emotionEnd = CharacterEmotionButton(self)
        self._emotionEnd.setToolTip('Ending emotion')
        self._emotionEnd.setVisible(False)
        self._emotionStart.emotionChanged.connect(self._emotionChanged)
        self._emotionEnd.emotionChanged.connect(self._emotionChanged)

        self.setAcceptDrops(True)

    def setNovel(self, novel: Novel):
        self._novel = novel

    def clear(self):
        clear_layout(self)
        for wdg in self._beatWidgets:
            gc(wdg)
        self._beatWidgets.clear()
        self.update()

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

    def setAgenda(self, agenda: SceneStructureAgenda, sceneTyoe: SceneType):
        self.clear()

        self._agenda = agenda
        for item in agenda.items:
            self._addBeatWidget(item)
        self._emotionStart.setValue(agenda.beginning_emotion)
        self._emotionStart.setVisible(True)
        self._emotionEnd.setValue(agenda.ending_emotion)
        self._emotionEnd.setVisible(True)

        if not agenda.items:
            self._initBeatsFromType(sceneTyoe)

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(0.7)

        pen = QPen()
        pen.setColor(QColor('darkBlue'))
        pen.setWidth(3)
        painter.setPen(pen)

        path = QPainterPath()

        forward = True
        y = 0
        for i, wdg in enumerate(self._beatWidgets):
            pos = wdg.pos().toPointF()
            pos.setY(pos.y() + wdg.layout().contentsMargins().top())
            if isinstance(wdg, SceneStructureItemWidget):
                pos.setY(pos.y() + wdg.btnIcon.height() // 2)
            pos.setX(pos.x() + wdg.layout().contentsMargins().left())
            if i == 0:
                y = pos.y()
                path.moveTo(pos)
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
            path.lineTo(pos)

        painter.drawPath(path)

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
        widget.setVisible(True)
        self.timelineChanged.emit()

    def _insertBeatWidget(self, placeholder: QWidget, beatType: SceneStructureItemType):
        item = SceneStructureItem(beatType)
        widget = self._newBeatWidget(item)

        i = self.layout().indexOf(placeholder)
        self.layout().removeWidget(placeholder)
        gc(placeholder)

        beat_index = i // 2
        self._beatWidgets.insert(beat_index, widget)
        self._agenda.items.insert(beat_index, item)
        self.layout().insertWidget(i, widget)
        self.layout().insertWidget(i + 1, self._newPlaceholderWidget())
        self.layout().insertWidget(i, self._newPlaceholderWidget())
        fade_in(widget, teardown=widget.activate)
        self.update()
        self.timelineChanged.emit()

    def _newBeatWidget(self, item: SceneStructureItem) -> SceneStructureItemWidget:
        widget = SceneStructureItemWidget(self._novel, item, parent=self)
        widget.removed.connect(self._beatRemoved)
        widget.emotionChanged.connect(self.emotionChanged.emit)
        # widget.dragStarted.connect(partial(self._initDragPlaceholder, widget))
        # widget.dragStopped.connect(self._resetDragPlaceholder)

        return widget

    def _newPlaceholderWidget(self) -> QWidget:
        btn = _SceneBeatPlaceholderButton()
        parent = wrap(btn, margin_top=BEAT_MIN_HEIGHT // 2 - 10)
        btn.selected.connect(partial(self._insertBeatWidget, parent))
        return parent

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
        i = self.layout().indexOf(wdg)
        self._agenda.items.remove(wdg.beat)
        self._beatWidgets.remove(wdg)
        placeholder_prev = self.layout().takeAt(i - 1).widget()
        gc(placeholder_prev)
        fade_out_and_gc(self, wdg)
        self.update()

        self.timelineChanged.emit()


class _SceneStructureTimeline(QWidget):
    emotionChanged = pyqtSignal()
    timelineChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(_SceneStructureTimeline, self).__init__(parent)
        self._topMargin = 20
        self._margin = 80
        self._lineDistance = 170
        self._arcWidth = 80
        self._beatWidth: int = 180
        self._emotionSize: int = 32
        self._penSize: int = 10
        self._path: Optional[QPainterPath] = None

        self._dragPlaceholder: Optional[SceneStructureItemWidget] = None

        self.setMouseTracking(True)

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
        pen = QPen(gradient, self._penSize, Qt.PenStyle.SolidLine)
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
            if self._dragPlaceholder:
                vertical_index = self._verticalTimelineIndex(event.position())
                self._dragPlaceholder.setGeometry(event.position().x() - self._dragPlaceholder.width() / 2,
                                                  vertical_index * self._lineDistance,
                                                  self._dragPlaceholder.width(),
                                                  self._dragPlaceholder.height())
                self._dragPlaceholder.setVisible(True)
        else:
            event.ignore()

    @overrides
    def dropEvent(self, event: QDropEvent) -> None:
        id_ = pickle.loads(event.mimeData().data(SceneStructureItemWidget.SceneBeatMimeType))

        for wdg in self._beatWidgets:
            if id(wdg) == id_:
                break

        event.accept()

        self.update()

    @overrides
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._intersects(event.pos()):
            if self._placeholder.isVisible():
                self._placeholder.setVisible(False)
                self.update()
            return

        self._placeholder.setVisible(True)
        vertical_index = self._verticalTimelineIndex(event.pos())
        self._placeholder.setGeometry(event.pos().x() - self._placeholder.width() / 2,
                                      vertical_index * self._lineDistance + self._lineDistance / 2 + self._penSize,
                                      self._placeholder.width(),
                                      self._placeholder.height())
        self.update()

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

    def _initDragPlaceholder(self, widget: SceneStructureItemWidget):
        self._dragPlaceholder = SceneStructureItemWidget(self.novel, widget.sceneStructureItem(), parent=self)
        self._dragPlaceholder.setDisabled(True)
        translucent(self._dragPlaceholder)
        self._dragPlaceholder.setHidden(True)

    def _resetDragPlaceholder(self):
        if self._dragPlaceholder is not None:
            self._dragPlaceholder.setHidden(True)
            gc(self._dragPlaceholder)
            self._dragPlaceholder = None


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

        self.btnScene = _SceneTypeButton(SceneType.ACTION)
        self.btnSequel = _SceneTypeButton(SceneType.REACTION)
        self.btnHappening = _SceneTypeButton(SceneType.HAPPENING)
        self.btnExposition = _SceneTypeButton(SceneType.EXPOSITION)
        self.btnSummary = _SceneTypeButton(SceneType.SUMMARY)

        self.wdgTypes.layout().addWidget(self.btnScene)
        self.wdgTypes.layout().addWidget(self.btnSequel)
        self.wdgTypes.layout().addWidget(self.btnSummary)
        self.wdgTypes.layout().addWidget(self.btnHappening)
        self.wdgTypes.layout().addWidget(self.btnExposition)

        flow(self.wdgGoalConflictContainer)
        margins(self.wdgGoalConflictContainer, left=40)

        self.timeline = SceneStructureTimeline(self)
        self.scrollAreaTimeline.layout().addWidget(self.timeline)

        self.listEvents = SceneStructureList()
        self.pageList.layout().addWidget(self.listEvents)

        self.btnScene.installEventFilter(OpacityEventFilter(parent=self.btnScene, ignoreCheckedButton=True))
        self.btnSequel.installEventFilter(OpacityEventFilter(parent=self.btnSequel, ignoreCheckedButton=True))
        self.btnScene.clicked.connect(partial(self._typeClicked, SceneType.ACTION))
        self.btnSequel.clicked.connect(partial(self._typeClicked, SceneType.REACTION))
        self.btnHappening.clicked.connect(partial(self._typeClicked, SceneType.HAPPENING))
        self.btnExposition.clicked.connect(partial(self._typeClicked, SceneType.EXPOSITION))
        self.btnSummary.clicked.connect(partial(self._typeClicked, SceneType.SUMMARY))

        self._btnGroupType = FadeOutButtonGroup()
        self._btnGroupType.addButton(self.btnScene)
        self._btnGroupType.addButton(self.btnSequel)
        self._btnGroupType.addButton(self.btnHappening)
        self._btnGroupType.addButton(self.btnExposition)
        self._btnGroupType.addButton(self.btnSummary)

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

        self.timeline.setNovel(novel)
        self.timeline.clear()
        self._initSelectors()

        self._checkSceneType()

        self.timeline.setAgenda(scene.agendas[0], self.scene.type)
        self.listEvents.setAgenda(scene.agendas[0], self.scene.type)
        self._initEditor(self.scene.type)

    def updateAvailableAgendaCharacters(self):
        chars = []
        chars.extend(self.scene.characters)
        if self.scene.pov:
            chars.insert(0, self.scene.pov)
        self.wdgAgendaCharacter.setAvailableCharacters(chars)

    def updateAgendaCharacter(self):
        self._toggleCharacterStatus()
        self._initSelectors()

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
            self._btnGroupType.toggle(self.btnScene)
        elif self.scene.type == SceneType.REACTION:
            self._btnGroupType.toggle(self.btnSequel)
        elif self.scene.type == SceneType.HAPPENING:
            self._btnGroupType.toggle(self.btnHappening)
        elif self.scene.type == SceneType.EXPOSITION:
            self._btnGroupType.toggle(self.btnExposition)
        elif self.scene.type == SceneType.SUMMARY:
            self._btnGroupType.toggle(self.btnSummary)
        else:
            self._btnGroupType.reset()

    def _typeClicked(self, type: SceneType, checked: bool):
        if not checked:
            if type in [SceneType.EXPOSITION, SceneType.SUMMARY]:
                self.timeline.setAgenda(self.scene.agendas[0], self.scene.type)
            self.scene.type = SceneType.DEFAULT
            self._initEditor(SceneType.DEFAULT)
            return

        self.scene.type = type
        self._initEditor(type)

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

        self.wdgAgenda.setHidden(type == SceneType.EXPOSITION)

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

            self._addConfictSelector()
        else:
            self._addConfictSelector()

    def _addGoalSelector(self, goal: Optional[CharacterGoal] = None, goalRef: Optional[GoalReference] = None):
        simplified = len(self.scene.agendas[0].goal_references) > 0
        selector = CharacterGoalSelector(self.novel, self.scene, simplified=simplified)
        self.wdgGoalConflictContainer.layout().addWidget(selector)
        selector.goalSelected.connect(self._initSelectors)
        # if goal and goalRef:
        #     selector.setGoal(goal, goalRef)

    def _addConfictSelector(self, conflict: Optional[Conflict] = None,
                            conflict_ref: Optional[ConflictReference] = None):
        simplified = len(self.scene.agendas[0].conflict_references) > 0
        conflict_selector = CharacterConflictSelector(self.novel, self.scene, simplified=simplified,
                                                      parent=self.wdgGoalConflictContainer)
        if conflict and conflict_ref:
            conflict_selector.setConflict(conflict, conflict_ref)
        self.wdgGoalConflictContainer.layout().addWidget(conflict_selector)
        conflict_selector.conflictSelected.connect(self._initSelectors)


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)

            self.resize(500, 500)

            self.widget = SceneStructureWidget(self)
            self.setCentralWidget(self.widget)

            novel = Novel('Novel')
            agenda = SceneStructureAgenda()
            scene = Scene('Scene', agendas=[agenda])
            self.widget.setScene(novel, scene)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
