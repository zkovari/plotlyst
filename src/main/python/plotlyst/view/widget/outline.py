"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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
from functools import partial
from typing import Optional, List

import qtanim
from PyQt6.QtCore import pyqtSignal, QRectF, QPoint, Qt, QSize, QEvent, QMimeData
from PyQt6.QtGui import QPainterPath, QColor, QPen, QPainter, QPaintEvent, QResizeEvent, QEnterEvent, QIcon
from PyQt6.QtWidgets import QWidget, QPushButton, QToolButton, QTextEdit, QFrame
from overrides import overrides
from qtanim import fade_in
from qthandy import sp, curved_flow, clear_layout, vbox, bold, decr_font, gc, pointy, margins, translucent, transparent, \
    hbox
from qthandy.filter import DragEventFilter, OpacityEventFilter

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Novel, OutlineItem, LayoutType
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.view.common import fade_out_and_gc, to_rgba_str, shadow
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.input import RemovalButton


class OutlineItemWidget(QWidget):
    dragStarted = pyqtSignal()
    dragStopped = pyqtSignal()
    removed = pyqtSignal(object)
    iconFixedSize: int = 36

    def __init__(self, item: OutlineItem, parent=None, readOnly: bool = False, colorfulShadow: bool = False):
        super().__init__(parent)
        self.item = item
        self._readOnly = readOnly
        vbox(self, 5, 2)
        self._colorAlpha: int = 175

        self._btnName = QPushButton(self)
        bold(self._btnName)
        if app_env.is_mac():
            self._btnName.setFixedHeight(max(self._btnName.sizeHint().height() - 8, 24))
        transparent(self._btnName)
        translucent(self._btnName, 0.7)

        self._btnIcon = QToolButton(self)
        self._btnIcon.setIconSize(QSize(24, 24))
        self._btnIcon.setFixedSize(self.iconFixedSize, self.iconFixedSize)

        self._text = QTextEdit(self)
        if not app_env.is_mac():
            decr_font(self._text)
        self._text.setProperty('rounded', True)
        self._text.setProperty('white-bg', True)
        self._text.setReadOnly(self._readOnly)
        if colorfulShadow:
            qcolor = QColor(self._color())
            qcolor.setAlpha(125)
            shadow(self._text, color=qcolor)
        else:
            shadow(self._text)
        self._text.setMinimumSize(170, 100)
        self._text.setMaximumSize(210, 100)
        self._text.setTabChangesFocus(True)
        self._text.setText(self.item.text)
        self._text.textChanged.connect(self._textChanged)

        self._btnRemove = RemovalButton(self)
        self._btnRemove.setHidden(True)
        self._btnRemove.clicked.connect(self._remove)

        self.layout().addWidget(self._btnIcon, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._btnName, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._text)

        if not self._readOnly:
            self._btnIcon.setCursor(Qt.CursorShape.OpenHandCursor)
            self._dragEventFilter = DragEventFilter(self, self.mimeType(), self._beatDataFunc,
                                                    grabbed=self._btnIcon, startedSlot=self.dragStarted.emit,
                                                    finishedSlot=self.dragStopped.emit)
            self._btnIcon.installEventFilter(self._dragEventFilter)
            self.setAcceptDrops(True)

    def mimeType(self) -> str:
        raise ValueError('Mimetype is not provided')

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        y = self.iconFixedSize if not self._btnIcon.isHidden() else 5
        self._btnRemove.setGeometry(self.width() - 15, y, 15, 15)
        self._btnRemove.raise_()

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        if not self._readOnly:
            self._btnRemove.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        self._btnRemove.setHidden(True)

    def activate(self):
        if self.graphicsEffect():
            self.setGraphicsEffect(None)
        if self.isVisible():
            self._text.setFocus()

    def _remove(self):
        self.removed.emit(self)

    def _beatDataFunc(self, btn):
        return id(self)

    def _initStyle(self, name: Optional[str] = None, desc: Optional[str] = None):
        color = self._color()
        color_translucent = to_rgba_str(QColor(color), self._colorAlpha)
        self._btnIcon.setStyleSheet(f'''
                    QToolButton {{
                                    background-color: {RELAXED_WHITE_COLOR};
                                    border: 2px solid {color_translucent};
                                    border-radius: 18px; padding: 4px;
                                }}
                    QToolButton:menu-indicator {{
                        width: 0;
                    }}
                    ''')

        if desc is None:
            desc = self._descriptions()[self.item.type]
        self._text.setPlaceholderText(desc)
        self._btnName.setToolTip(desc)
        self._text.setToolTip(desc)
        self._btnIcon.setToolTip(desc)

        if name is None:
            name = self.item.type.name
        self._btnName.setText(name.lower().capitalize().replace('_', ' '))

        self._btnIcon.setIcon(self._icon())

    def _color(self) -> str:
        return 'black'

    def _icon(self) -> QIcon:
        return QIcon()

    def _descriptions(self) -> dict:
        pass

    def _glow(self) -> QColor:
        color = QColor(self._color())
        qtanim.glow(self._btnName, color=color)
        qtanim.glow(self._text, color=color)

        return color

    def _textChanged(self):
        self.item.text = self._text.toPlainText()


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


class OutlineTimelineWidget(QFrame):
    timelineChanged = pyqtSignal()

    def __init__(self, parent=None, paintTimeline: bool = True, layout: LayoutType = LayoutType.CURVED_FLOW,
                 framed: bool = False, frameColor=Qt.GlobalColor.black):
        super().__init__(parent)
        self._novel: Optional[Novel] = None
        self._readOnly: bool = False
        self._currentPlaceholder: Optional[QWidget] = None
        self._paintTimeline = paintTimeline

        if framed:
            self.setFrameShape(QFrame.Shape.StyledPanel)
            self.setLineWidth(1)
            # self.setProperty('relaxed-white-bg', True)
            # self.setProperty('large-rounded', True)
            shadow(self, color=QColor(frameColor))

        sp(self).h_exp().v_exp()
        if layout == LayoutType.CURVED_FLOW:
            curved_flow(self, margin=10, spacing=10)
        elif layout == LayoutType.HORIZONTAL:
            hbox(self, 10, 10)
        elif layout == LayoutType.VERTICAL:
            vbox(self, 10, 10)

        self._structure: List[OutlineItem] = []
        self._beatWidgets: List[OutlineItemWidget] = []

        self._dragPlaceholder: Optional[OutlineItemWidget] = None
        self._dragPlaceholderIndex: int = -1
        self._dragged: Optional[OutlineItemWidget] = None
        self._wasDropped: bool = False

        self.setAcceptDrops(True)

    def setNovel(self, novel: Novel):
        self._novel = novel

    def setReadnOnly(self, readOnly: bool):
        self._readOnly = readOnly

    def clear(self):
        self._beatWidgets.clear()
        clear_layout(self)

    def setStructure(self, items: List[OutlineItem]):
        self.clear()

        self._structure = items

        for item in items:
            self._addBeatWidget(item)
        if not items:
            self.layout().addWidget(self._newPlaceholderWidget(displayText=True))

        self.update()

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        if not self._paintTimeline:
            return
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
            if isinstance(wdg, OutlineItemWidget):
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

    def _addBeatWidget(self, item: OutlineItem):
        widget = self._newBeatWidget(item)
        self._beatWidgets.append(widget)
        if self.layout().count() == 0:
            self.layout().addWidget(self._newPlaceholderWidget())
        self.layout().addWidget(widget)
        self.layout().addWidget(self._newPlaceholderWidget())
        widget.activate()
        self.timelineChanged.emit()

    def _insertWidget(self, item: OutlineItem, widget: OutlineItemWidget):
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

    def _beatRemoved(self, wdg: OutlineItemWidget):
        self._structure.remove(wdg.item)
        self._beatWidgetRemoved(wdg)

    def _beatWidgetRemoved(self, wdg: OutlineItemWidget):
        i = self.layout().indexOf(wdg)
        self._beatWidgets.remove(wdg)
        placeholder_prev = self.layout().takeAt(i - 1).widget()
        gc(placeholder_prev)
        fade_out_and_gc(self, wdg)
        self.update()

        self.timelineChanged.emit()

    @abstractmethod
    def _newBeatWidget(self, item: OutlineItem) -> OutlineItemWidget:
        pass

    @abstractmethod
    def _placeholderClicked(self, placeholder: QWidget):
        pass

    def _newPlaceholderWidget(self, displayText: bool = False) -> QWidget:
        parent = _PlaceholderWidget()
        if displayText:
            parent.btn.setText('Insert beat')
        parent.btn.clicked.connect(partial(self._placeholderClicked, parent))

        if self._readOnly:
            parent.setHidden(True)

        return parent

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
        wdg = self._newBeatWidget(self._dragged.item)
        i = self.layout().indexOf(self._dragPlaceholder)
        self.layout().insertWidget(i, wdg)

        self.layout().removeWidget(self._dragPlaceholder)
        gc(self._dragPlaceholder)
        self._dragPlaceholder = None
        self._dragPlaceholderIndex = -1

        beats: List[OutlineItemWidget] = []
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
        self._structure[:] = [x.item for x in self._beatWidgets]
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
    # def _newBeatWidget(self, item: SceneStructureItem) -> SceneStructureBeatWidget:
    #     if item.type == OutlineItemType.EMOTION:
    #         clazz = SceneStructureEmotionWidget
    #     else:
    #         clazz = SceneStructureBeatWidget
    #     widget = clazz(self._novel, item, parent=self, readOnly=self._readOnly)
    #     widget.removed.connect(self._beatRemoved)
    #     if item.type == OutlineItemType.CLIMAX:
    #         self._selectorMenu.setOutcomeEnabled(False)
    #         widget.setOutcome(self._scene.outcome)
    #         widget.outcomeChanged.connect(self._outcomeChanged)
    #     widget.dragStarted.connect(partial(self._dragStarted, widget))
    #     widget.dragStopped.connect(self._dragFinished)
    #
    #     if not self._readOnly:
    #         widget.installEventFilter(DropEventFilter(widget, [SceneStructureItemWidget.SceneBeatMimeType],
    #                                                   motionDetection=Qt.Orientation.Horizontal,
    #                                                   motionSlot=partial(self._dragMoved, widget),
    #                                                   droppedSlot=self._dropped))
    #
    #     return widget

    # def _newPlaceholderWidget(self, displayText: bool = False) -> QWidget:
    #     parent = _PlaceholderWidget()
    #     if displayText:
    #         parent.btn.setText('Insert beat')
    #     parent.btn.clicked.connect(partial(self._showBeatMenu, parent))
    #
    #     if self._readOnly:
    #         parent.setHidden(True)
    #
    #     return parent
