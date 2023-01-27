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
from functools import partial
from typing import Optional, List

import qtanim
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF, QPoint, QEvent
from PyQt6.QtGui import QIcon, QColor, QDropEvent, QDragEnterEvent, QDragMoveEvent, QMouseEvent, QPainter, QResizeEvent, \
    QPen, QPainterPath, QPaintEvent, QLinearGradient, QEnterEvent
from PyQt6.QtWidgets import QWidget, QToolButton, QPushButton, QSizePolicy
from overrides import overrides
from qthandy import pointy, gc, translucent, bold, transparent, btn_popup_menu, \
    retain_when_hidden, flow, clear_layout, decr_font
from qthandy.filter import OpacityEventFilter, VisibilityToggleEventFilter, DragEventFilter, DisabledClickEventFilter

from src.main.python.plotlyst.common import emotion_color, RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Character, Novel, Scene, SceneStructureItemType, SceneType, \
    SceneStructureItem, SceneOutcome, SceneStructureAgenda, CharacterGoal, GoalReference, Conflict, ConflictReference
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.view.common import action
from src.main.python.plotlyst.view.generated.scene_beat_item_widget_ui import Ui_SceneBeatItemWidget
from src.main.python.plotlyst.view.generated.scene_structure_editor_widget_ui import Ui_SceneStructureWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterEmotionButton, CharacterGoalSelector, \
    CharacterConflictSelector
from src.main.python.plotlyst.view.widget.input import MenuWithDescription
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
        return IconRegistry.from_name('ri.question-mark')
    elif beat_type == SceneStructureItemType.REVELATION:
        return IconRegistry.from_name('fa5s.binoculars')
    elif beat_type == SceneStructureItemType.SETUP:
        return IconRegistry.from_name('mdi.motion')
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
        self.installEventFilter(OpacityEventFilter(self))
        self.setIconSize(QSize(24, 24))
        transparent(self)
        pointy(self)
        self.setToolTip('Insert new beat')

        self._menu = MenuWithDescription(self)
        self._addAction('Action', SceneStructureItemType.ACTION)
        self._addAction('Conflict', SceneStructureItemType.CONFLICT)
        self._addAction('Outcome', SceneStructureItemType.OUTCOME)
        self._addAction('Reaction', SceneStructureItemType.REACTION)
        self._addAction('Dilemma', SceneStructureItemType.DILEMMA)
        self._addAction('Decision', SceneStructureItemType.DECISION)
        self._addAction('Hook', SceneStructureItemType.HOOK)
        self._addAction('Inciting incident', SceneStructureItemType.INCITING_INCIDENT)
        self._addAction('Rising action', SceneStructureItemType.RISING_ACTION)
        self._addAction('Choice', SceneStructureItemType.CHOICE)
        self._addAction('Exposition', SceneStructureItemType.EXPOSITION)
        self._addAction('Beat', SceneStructureItemType.BEAT)
        self._addAction('Turn', SceneStructureItemType.TURN)
        self._addAction('Mystery', SceneStructureItemType.MYSTERY)
        self._addAction('Revelation', SceneStructureItemType.REVELATION)
        self._addAction('Setup', SceneStructureItemType.SETUP)

        btn_popup_menu(self, self._menu)

    def _addAction(self, text: str, beat_type: SceneStructureItemType):
        description = BeatDescriptions[beat_type]
        self._menu.addAction(action(text, beat_icon(beat_type), slot=lambda: self.selected.emit(beat_type)),
                             description)


class SceneStructureItemWidget(QWidget, Ui_SceneBeatItemWidget):
    entered = pyqtSignal()
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
        elif self.beat.type == SceneStructureItemType.CHOICE:
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
        self._topMargin = 20
        self._margin = 80
        self._lineDistance = 140
        self._arcWidth = 80
        self._beatWidth: int = 180
        self._emotionSize: int = 32
        self._penSize: int = 10
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
        if event.pos().y() > (self._curves() * 2 + 1) * self._lineDistance or event.pos().y() < self._topMargin:
            if self._placeholder.isVisible():
                self._placeholder.setVisible(False)
                self.update()
                # if QApplication.overrideCursor():
                #     QApplication.restoreOverrideCursor()
            return

        # if not QApplication.overrideCursor():
        #     QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

        self._placeholder.setVisible(True)
        vertical_index = (event.pos().y() - self._topMargin) // self._lineDistance
        self._placeholder.setGeometry(event.pos().x() - 12,
                                      vertical_index * self._lineDistance + self._lineDistance / 2 + self._penSize, 24,
                                      24)
        self.update()

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        self._placeholder.setVisible(False)

    # def _contains(self, pos: QPoint) -> bool:
    #     if not self._path:
    #         return False
    #     return self._path.intersects(QRectF(pos.x(), pos.y(), 1, 1))

    def _intersects(self, pos: QPoint) -> bool:
        for i in range(self._path.elementCount()):
            el = self._path.elementAt(i)
            if el.y - 10 < pos.y() < el.y + 10:
                if el.isLineTo():
                    return True
        return False

    def _percentage(self, pos: QPoint) -> float:
        length = 0
        vertical_index = (pos.y() - self._topMargin) // self._lineDistance
        y_pos = vertical_index * self._lineDistance + self._topMargin
        for i in range(self._path.elementCount()):
            el = self._path.elementAt(i)
            if i > 0:
                prev_el = self._path.elementAt(i - 1)
                if prev_el.y == el.y:
                    length += abs(el.x - prev_el.x)
                elif prev_el.isCurveTo():
                    length += self._lineDistance / 2
            if el.y - 10 < y_pos < el.y + 10:
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
        placeholder_size = 24
        return max(sum([x.maximumWidth() + placeholder_size for x in self._beatWidgets]) // w, 0)

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

        y = self._topMargin
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
        widget.entered.connect(lambda: self._placeholder.setHidden(True))
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
