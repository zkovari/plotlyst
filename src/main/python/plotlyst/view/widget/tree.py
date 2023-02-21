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

from PyQt6.QtCore import Qt, pyqtSignal, QObject, QEvent
from PyQt6.QtGui import QIcon, QMouseEvent, QEnterEvent
from PyQt6.QtWidgets import QScrollArea, QFrame, QSizePolicy, QToolButton, QMenu
from PyQt6.QtWidgets import QWidget, QLabel
from overrides import overrides
from qthandy import vbox, hbox, bold, margins, clear_layout, transparent, btn_popup_menu

from src.main.python.plotlyst.view.common import ButtonPressResizeEventFilter
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.display import Icon


class BaseTreeWidget(QWidget):
    selectionChanged = pyqtSignal(bool)
    deleted = pyqtSignal()

    def __init__(self, title: str, icon: Optional[QIcon] = None, parent=None):
        super(BaseTreeWidget, self).__init__(parent)
        self._menuEnabled: bool = True

        self._selected: bool = False
        self._wdgTitle = QWidget(self)
        hbox(self._wdgTitle, 0, 2)

        self._lblTitle = QLabel(title)
        self._lblTitle.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._icon = Icon(self._wdgTitle)
        if icon:
            self._icon.setIcon(icon)
        else:
            self._icon.setHidden(True)

        self._btnMenu = QToolButton()
        transparent(self._btnMenu)
        self._btnMenu.setIcon(IconRegistry.dots_icon('grey', vertical=True))
        self._btnMenu.installEventFilter(ButtonPressResizeEventFilter(self._btnMenu))
        self._btnMenu.setHidden(True)
        self._initMenu()

        self._wdgTitle.layout().addWidget(self._icon)
        self._wdgTitle.layout().addWidget(self._lblTitle)
        self._wdgTitle.layout().addWidget(self._btnMenu)

    def _initMenu(self):
        menu = QMenu(self._btnMenu)
        menu.addAction(IconRegistry.trash_can_icon(), 'Delete', self.deleted.emit)
        menu.aboutToHide.connect(lambda: self._btnMenu.setHidden(True))
        btn_popup_menu(self._btnMenu, menu)

    def titleWidget(self) -> QWidget:
        return self._wdgTitle

    def titleLabel(self) -> QLabel:
        return self._lblTitle

    def select(self):
        self._toggleSelection(True)

    def deselect(self):
        self._toggleSelection(False)

    def setMenuEnabled(self, enabled: bool):
        self._menuEnabled = enabled

    def _toggleSelection(self, selected: bool):
        self._selected = selected
        bold(self._lblTitle, self._selected)
        self._reStyle()

    def _reStyle(self):
        if self._selected:
            self._wdgTitle.setStyleSheet('''
                    .QWidget {
                        background-color: #D8D5D5;
                    }
                ''')
        else:
            self._wdgTitle.setStyleSheet('')


class ChildNode(BaseTreeWidget):

    def __init__(self, title: str, icon: Optional[QIcon] = None, parent=None):
        super(ChildNode, self).__init__(title, icon, parent)
        hbox(self)
        self.layout().addWidget(self._wdgTitle)

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        if self._menuEnabled:
            self._btnMenu.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        if self._menuEnabled and not self._btnMenu.menu().isVisible():
            self._btnMenu.setHidden(True)

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._toggleSelection(not self._selected)
        self.selectionChanged.emit(self._selected)


class ContainerNode(BaseTreeWidget):

    def __init__(self, title: str, icon: Optional[QIcon] = None, parent=None):
        super(ContainerNode, self).__init__(title, icon, parent)
        vbox(self, margin=1, spacing=3)

        self._container = QWidget(self)
        self._container.setHidden(True)
        vbox(self._container, 1)
        margins(self._container, left=10)
        self.layout().addWidget(self._wdgTitle)
        self.layout().addWidget(self._container)

        self._wdgTitle.installEventFilter(self)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter and self._menuEnabled:
            self._btnMenu.setVisible(True)
        elif event.type() == QEvent.Type.Leave and self._menuEnabled and not self._btnMenu.menu().isVisible():
            self._btnMenu.setHidden(True)
        elif event.type() == QEvent.Type.MouseButtonRelease and self.isEnabled():
            self._toggleSelection(not self._selected)
            self.selectionChanged.emit(self._selected)
        return super(ContainerNode, self).eventFilter(watched, event)

    def containerWidget(self) -> QWidget:
        return self._container

    def addChild(self, wdg: QWidget):
        self._container.setVisible(True)
        self._container.layout().addWidget(wdg)

    def insertChild(self, i: int, wdg: QWidget):
        self._container.setVisible(True)
        self._container.layout().insertWidget(i, wdg)

    def clearChildren(self):
        clear_layout(self._container)
        self._container.setHidden(True)


class TreeView(QScrollArea):

    def __init__(self, parent=None):
        super(TreeView, self).__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self._centralWidget = QWidget(self)
        self.setWidget(self._centralWidget)
        vbox(self._centralWidget, spacing=0)
