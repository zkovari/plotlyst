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
from typing import Optional, Dict

from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QPoint
from PyQt6.QtGui import QTransform, \
    QKeyEvent, QKeySequence, QCursor
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsSceneMouseEvent
from overrides import overrides

from src.main.python.plotlyst.core.domain import Node, Diagram, DiagramNodeType, Connector
from src.main.python.plotlyst.view.widget.graphics import NodeItem, CharacterItem, PlaceholderSocketItem, ConnectorItem, \
    SelectorRectItem, AbstractSocketItem


@dataclass
class ItemDescriptor:
    mode: DiagramNodeType
    subType: str = ''


class NetworkScene(QGraphicsScene):
    cancelItemAddition = pyqtSignal()
    itemAdded = pyqtSignal(DiagramNodeType, NodeItem)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._diagram: Optional[Diagram] = None
        self._linkMode: bool = False
        self._additionDescriptor: Optional[ItemDescriptor] = None
        self._copyDescriptor: Optional[ItemDescriptor] = None

        self._placeholder: Optional[PlaceholderSocketItem] = None
        self._connectorPlaceholder: Optional[ConnectorItem] = None

        self._selectionMode = False
        self._selectionRect = SelectorRectItem()
        self._selectionRect.setVisible(False)

    def setDiagram(self, diagram: Diagram):
        self._diagram = diagram
        self.clear()
        self.addItem(self._selectionRect)
        if not self._diagram.loaded:
            self._load()

        nodes: Dict[str, NodeItem] = {}
        for node in self._diagram.data.nodes:
            nodeItem = self._addNode(node)
            nodes[str(node.id)] = nodeItem
        for connector in self._diagram.data.connectors:
            source = nodes.get(str(connector.source_id), None)
            target = nodes.get(str(connector.target_id), None)
            if source and target:
                self._addConnector(connector, source, target)

    def isAdditionMode(self) -> bool:
        return self._additionDescriptor is not None

    def startAdditionMode(self, itemType: DiagramNodeType, subType: str = ''):
        self._additionDescriptor = ItemDescriptor(itemType, subType)

    def endAdditionMode(self):
        self._additionDescriptor = None

    def linkMode(self) -> bool:
        return self._linkMode

    def linkSource(self) -> Optional[AbstractSocketItem]:
        if self._connectorPlaceholder is not None:
            return self._connectorPlaceholder.source()

    def startLink(self, source: AbstractSocketItem):
        self._linkMode = True
        self._placeholder = PlaceholderSocketItem()
        self._placeholder.setVisible(False)
        self._placeholder.setEnabled(False)
        self.addItem(self._placeholder)
        self._connectorPlaceholder = ConnectorItem(source, self._placeholder)
        self.addItem(self._connectorPlaceholder)

        self._placeholder.setPos(source.scenePos())
        self._connectorPlaceholder.rearrange()

    def endLink(self):
        self._linkMode = False
        self.removeItem(self._connectorPlaceholder)
        self.removeItem(self._placeholder)
        self._connectorPlaceholder = None
        self._placeholder = None

    def link(self, target: AbstractSocketItem):
        sourceNode: NodeItem = self._connectorPlaceholder.source().parentItem()
        targetNode: NodeItem = target.parentItem()

        self._onLink(sourceNode, self._connectorPlaceholder.source(), targetNode, target)
        connectorItem = ConnectorItem(self._connectorPlaceholder.source(), target)
        self._connectorPlaceholder.source().addConnector(connectorItem)
        target.addConnector(connectorItem)

        connector = Connector(
            sourceNode.node().id,
            targetNode.node().id,
            self._connectorPlaceholder.source().angle(), target.angle(),
            pen=connectorItem.penStyle(), width=connectorItem.penWidth(), color=connectorItem.color().name()
        )
        if connectorItem.icon():
            connector.icon = connectorItem.icon()
        connectorItem.setConnector(connector)
        self._diagram.data.connectors.append(connector)
        self._save()

        self.addItem(connectorItem)
        self.endLink()

    @overrides
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            if self.linkMode():
                self.endLink()
            elif self.isAdditionMode():
                self.cancelItemAddition.emit()
                self.endAdditionMode()
            else:
                self.clearSelection()
        elif event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            for item in self.selectedItems():
                self._removeItem(item)
        elif event.matches(QKeySequence.StandardKey.Copy) and len(self.selectedItems()) == 1:
            self._copy(self.selectedItems()[0])
        elif event.matches(QKeySequence.StandardKey.Paste):
            self._paste()

    @overrides
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if (not self.isAdditionMode() and not self.linkMode() and
                event.button() & Qt.MouseButton.LeftButton and not self.itemAt(event.scenePos(), QTransform())):
            pass
            # self._selectionRect.start(event.scenePos())
            # self._selectionMode = True
        elif event.button() & Qt.MouseButton.RightButton or event.button() & Qt.MouseButton.MiddleButton:
            # disallow view movement to clear item selection
            return
        super().mousePressEvent(event)

    @overrides
    def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self.linkMode():
            self._placeholder.setPos(event.scenePos())
            self._connectorPlaceholder.rearrange()
        elif self._selectionMode:
            self._selectionRect.adjust(event.scenePos())
            self._selectionRect.setVisible(True)
            self._updateSelection()
        super().mouseMoveEvent(event)

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self.linkMode():
            if event.button() & Qt.MouseButton.RightButton:
                self.endLink()
        elif self.isAdditionMode() and event.button() & Qt.MouseButton.RightButton:
            self.cancelItemAddition.emit()
            self.endAdditionMode()
        elif self._selectionMode and event.button() & Qt.MouseButton.LeftButton:
            self._selectionMode = False
            self._selectionRect.setVisible(False)
            self._updateSelection()
        elif self._additionDescriptor is not None:
            item = self._addNewItem(event.scenePos(), self._additionDescriptor.mode, self._additionDescriptor.subType)
            self._diagram.data.nodes.append(item.node())
            self._save()

        super().mouseReleaseEvent(event)

    def itemChangedEvent(self, item: NodeItem):
        self._save()

    def connectorChangedEvent(self, connector: ConnectorItem):
        self._save()

    def _removeItem(self, item: QGraphicsItem):
        if isinstance(item, NodeItem):
            for connectorItem in item.connectors():
                self._diagram.data.connectors.remove(connectorItem.connector())
                self.removeItem(connectorItem)
            item.clearConnectors()
            self._diagram.data.nodes.remove(item.node())
        elif isinstance(item, ConnectorItem):
            self._diagram.data.connectors.remove(item.connector())
            item.source().removeConnector(item)
            item.target().removeConnector(item)

        self.removeItem(item)
        self._save()

    def _addConnector(self, connector: Connector, source: NodeItem, target: NodeItem):
        sourceSocket = source.socket(connector.source_angle)
        targetSocket = target.socket(connector.target_angle)
        connectorItem = ConnectorItem(sourceSocket, targetSocket)

        sourceSocket.addConnector(connectorItem)
        targetSocket.addConnector(connectorItem)

        self.addItem(connectorItem)
        connectorItem.setConnector(connector)

        self._onLink(source, sourceSocket, target, targetSocket)

    def _copy(self, item: NodeItem):
        self._copyDescriptor = ItemDescriptor(item.node().type, item.node().subtype)

    def _paste(self):
        if self._copyDescriptor:
            view = self.views()[0]
            viewPos: QPoint = view.mapFromGlobal(QCursor.pos())
            scenePos: QPointF = view.mapToScene(viewPos)

            self._addNewItem(scenePos, self._copyDescriptor.mode, self._copyDescriptor.subType)

    @abstractmethod
    def _addNewItem(self, scenePos: QPointF, itemType: DiagramNodeType, subType: str = '') -> NodeItem:
        pass

    @abstractmethod
    def _addNode(self, node: Node) -> NodeItem:
        pass

    @abstractmethod
    def _load(self):
        pass

    @abstractmethod
    def _save(self):
        pass

    def _onLink(self, sourceNode: NodeItem, sourceSocket: AbstractSocketItem, targetNode: NodeItem,
                targetSocket: AbstractSocketItem):
        if isinstance(sourceNode, CharacterItem):
            sourceNode.addSocket(sourceSocket)
        if isinstance(targetNode, CharacterItem):
            targetNode.addSocket(targetSocket)

    def _updateSelection(self):
        if not self._selectionRect.rect().isValid():
            return
        self.clearSelection()
        items_in_rect = self.items(self._selectionRect.rect(), Qt.ItemSelectionMode.IntersectsItemBoundingRect)
        for item in items_in_rect:
            item.setSelected(True)
