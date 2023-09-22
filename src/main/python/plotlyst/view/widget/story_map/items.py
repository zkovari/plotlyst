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
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QTimer
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget, QStyleOptionGraphicsItem, \
    QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent, QGraphicsItem
from overrides import overrides

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR, RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Node, DiagramNodeType
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.graphics import NodeItem


class MindMapNode(NodeItem):
    def mindMapScene(self) -> 'EventsMindMapScene':
        return self.scene()

    def linkMode(self) -> bool:
        return self.mindMapScene().linkMode()


class StickerItem(MindMapNode):
    displayMessage = pyqtSignal()

    def __init__(self, node: Node, parent=None):
        super().__init__(node, parent)
        self._size = 28
        if type == DiagramNodeType.COMMENT:
            self._icon = IconRegistry.from_name('mdi.comment-text', PLOTLYST_SECONDARY_COLOR)
        elif type == DiagramNodeType.TOOL:
            self._icon = IconRegistry.tool_icon()
        if type == DiagramNodeType.COST:
            self._icon = IconRegistry.cost_icon()

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size, self._size)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(RELAXED_WHITE_COLOR))
        painter.drawRect(3, 3, self._size - 6, self._size - 10)
        self._icon.paint(painter, 0, 0, self._size, self._size)

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self.mindMapScene().displayStickerMessage(self)

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        QTimer.singleShot(300, self.mindMapScene().hideStickerMessage)

    @overrides
    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.mindMapScene().hideStickerMessage()
