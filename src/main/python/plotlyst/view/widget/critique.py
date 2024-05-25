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
from typing import Optional

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont, QTextDocument, QPainter, QTransform, QColor
from PyQt6.QtWidgets import QWidget, QStackedWidget, QTextEdit, QTabWidget, QAbstractGraphicsShapeItem, \
    QStyleOptionGraphicsItem, QGraphicsSceneMouseEvent
from overrides import overrides
from qthandy import vbox
from qttextedit import RichTextEditor

from plotlyst.common import RELAXED_WHITE_COLOR
from plotlyst.core.domain import Node
from plotlyst.view.common import spawn, push_btn, link_editor_to_btn
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.graphics import NetworkScene, NetworkGraphicsView
from plotlyst.view.widget.graphics.items import TextItem


class ExcerptItem(QAbstractGraphicsShapeItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text: str = ''
        self._document: Optional[QTextDocument] = None
        self._width: int = 500
        self._height: int = 10

    def setDocument(self, doc: QTextDocument):
        self._document = doc

    def refresh(self):
        self._width = self._document.size().width()
        self._height = self._document.size().height()
        print(f'size {self._width} {self._height}')
        self.prepareGeometryChange()
        self.update()

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)

    @overrides
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        if self._document:
            self._document.drawContents(painter, self.boundingRect())


class CritiqueItem(TextItem):
    Margin: int = 20
    Padding: int = 5

    def __init__(self, node: Node, parent=None):
        super().__init__(node, parent)


class CritiqueScene(NetworkScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.excerptItem = ExcerptItem()
        self.addItem(self.excerptItem)

    @overrides
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if (not self.isAdditionMode() and not self.linkMode() and
                event.button() & Qt.MouseButton.LeftButton):
            itemAt = self.itemAt(event.scenePos(), QTransform())
            if itemAt is None or itemAt == self.excerptItem:
                pos = self._cursorScenePos()
                if pos:
                    node = self.toNoteNode(pos)
                    node.size = 14
                    item = CritiqueItem(node)
                    self.addItem(item)
                    self.editItem.emit(item)
            else:
                super().mouseDoubleClickEvent(event)
        else:
            super().mouseDoubleClickEvent(event)


class CritiqueView(NetworkGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QColor(RELAXED_WHITE_COLOR))

    @overrides
    def _initScene(self) -> NetworkScene:
        return CritiqueScene()


@spawn
class CritiqueWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stack = QStackedWidget()
        vbox(self).addWidget(self.stack)

        self.pageInput = QWidget()
        self.pageEditor = QWidget()

        self.stack.addWidget(self.pageInput)
        self.stack.addWidget(self.pageEditor)

        vbox(self.pageInput)
        self.textInput = QTextEdit()
        self.textInput.setProperty('rounded', True)
        self.textInput.setPlaceholderText('Insert an excerpt for critique')
        self.pageInput.layout().addWidget(self.textInput)
        self.btnNext = push_btn(IconRegistry.from_name('fa5s.arrow-alt-circle-right', RELAXED_WHITE_COLOR), 'Next',
                                properties=['base', 'positive'])
        self.btnNext.clicked.connect(lambda: self.stack.setCurrentWidget(self.pageEditor))
        link_editor_to_btn(self.textInput, self.btnNext, True)
        self.pageInput.layout().addWidget(self.btnNext, alignment=Qt.AlignmentFlag.AlignRight)

        vbox(self.pageEditor)
        self.tabWidgetEditor = QTabWidget()
        self.pageEditor.layout().addWidget(self.tabWidgetEditor)

        self.tabEditor = QWidget()
        self.tabVisual = QWidget()
        self.tabWidgetEditor.addTab(self.tabEditor, 'Text editor')
        self.tabWidgetEditor.addTab(self.tabVisual, 'Visual editor')

        vbox(self.tabEditor)
        self.richtextEditor = RichTextEditor()
        self.richtextEditor.setFixedWidth(900)
        font: QFont = self.richtextEditor.textEdit.font()
        font.setPointSize(11)
        font.setFamily('Sans-serif')
        self.richtextEditor.textEdit.setFont(font)
        self.richtextEditor.textEdit.setTextColor(QColor('#4a4e69'))
        self.richtextEditor.textEdit.setSidebarEnabled(False)
        self.richtextEditor.textEdit.setContentsMargins(0, 0, 0, 0)
        self.tabEditor.layout().addWidget(self.richtextEditor)

        vbox(self.tabVisual)
        self.visual = CritiqueView()
        self.tabVisual.layout().addWidget(self.visual)

        # scene = CritiqueScene()
        # self.visual.setScene(scene)
        # self.item = ExcerptItem()
        self.visual.scene().excerptItem.setDocument(self.richtextEditor.textEdit.document())
        self.richtextEditor.textEdit.textChanged.connect(self.visual.scene().excerptItem.refresh)
        # scene.addItem(self.item)
        self.visual.centerOn(self.visual.scene().excerptItem.sceneBoundingRect().center())
        self.richtextEditor.textEdit.setText('''When twenty-four-year-old Nerissa Avon realizes her best friend Alicen Delaris has been abducted by an invading Fae warband, she knows immediately what she must do: infiltrate the war camp and rescue her.
        Far from home and stranded on the other side of the continent, Nerissa must fight to convince the Knights of the Human Kingdom to believe her story and send aid, despite their famed prejudice against Nerissa’s people.
        A common fisherfolk from the lowly island of Lasgair, Nerissa knows she won’t stand a chance against the ruthless, bloodthirsty Fae from the fables of her childhood. But Nerissa’s about had enough of being underestimated, abandoned, and discarded: though she may never recover, Nerissa is willing to sell her soul to save her best friend.
        As Nerissa continues to sacrifice everything she is for her goal, she finds herself alienating the very people who she will need to secure Alicen’s freedom, and uncover the truth: the Fae have no intentions of leaving the Human Kingdom alive – and Nerissa has just been caught in the middle of it.
''')
        self.richtextEditor.textEdit.setBlockFormat(220)

        self.stack.setCurrentWidget(self.pageEditor)  # TODO change later
        self.tabWidgetEditor.setCurrentWidget(self.tabEditor)
        self.richtextEditor.textEdit.setFocus()
