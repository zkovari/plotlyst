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
from typing import Optional, List

import qtanim
from PyQt6.QtCore import pyqtSignal, QRectF, QPoint, Qt, QSize, QEvent
from PyQt6.QtGui import QPainterPath, QColor, QPen, QPainter, QPaintEvent, QResizeEvent, QEnterEvent, QIcon
from PyQt6.QtWidgets import QWidget, QPushButton, QToolButton, QTextEdit
from overrides import overrides
from qthandy import sp, curved_flow, clear_layout, vbox, bold, decr_font
from qthandy.filter import DragEventFilter

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Novel, OutlineItem
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.view.widget.input import RemovalButton


class OutlineItemWidget(QWidget):
    dragStarted = pyqtSignal()
    dragStopped = pyqtSignal()
    removed = pyqtSignal(object)
    iconFixedSize: int = 36

    def __init__(self, item: OutlineItem, parent=None, readOnly: bool = False):
        super().__init__(parent)
        self.item = item
        self._readOnly = readOnly
        vbox(self, 0, 2)

        self._btnName = QPushButton(self)
        bold(self._btnName)
        if app_env.is_mac():
            self._btnName.setFixedHeight(max(self._btnName.sizeHint().height() - 8, 24))

        self._btnIcon = QToolButton(self)
        self._btnIcon.setIconSize(QSize(24, 24))
        self._btnIcon.setFixedSize(self.iconFixedSize, self.iconFixedSize)

        self._text = QTextEdit(self)
        if not app_env.is_mac():
            decr_font(self._text)
        self._text.setProperty('rounded', True)
        self._text.setProperty('white-bg', True)
        self._text.setReadOnly(self._readOnly)
        self._text.setMaximumHeight(100)
        self._text.setTabChangesFocus(True)
        self._text.setText(self.item.text)
        self._text.textChanged.connect(self._textChanged)

        self._btnRemove = RemovalButton(self)
        self._btnRemove.setHidden(True)
        self._btnRemove.clicked.connect(self._remove)

        self.layout().addWidget(self._btnIcon, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._btnName, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._text)

        self.setFixedWidth(210)

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
        self._btnRemove.setGeometry(self.width() - 15, self.iconFixedSize, 15, 15)
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
        anim = qtanim.fade_out(self, duration=150)
        anim.finished.connect(lambda: self.removed.emit(self))

    def _beatDataFunc(self, btn):
        return id(self)

    def _initStyle(self, name: Optional[str] = None, desc: Optional[str] = None):
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


class OutlineTimelineWidget(QWidget):
    timelineChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._novel: Optional[Novel] = None
        self._readOnly: bool = False

        sp(self).h_exp().v_exp()
        curved_flow(self, margin=10, spacing=10)

        self._structure: List[OutlineItem] = []
        self._beatWidgets: List[OutlineItemWidget] = []

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

    @abstractmethod
    def _newBeatWidget(self, item: OutlineItem) -> OutlineItemWidget:
        pass

    @abstractmethod
    def _newPlaceholderWidget(self):
        pass

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
