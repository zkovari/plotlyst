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
from dataclasses import dataclass
from typing import Optional, List

from PyQt6.QtCore import Qt, pyqtSignal, QObject, QEvent, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QScrollArea, QFrame, QSizePolicy, QToolButton
from PyQt6.QtWidgets import QWidget, QLabel
from overrides import overrides
from qthandy import vbox, hbox, bold, margins, clear_layout, transparent, retain_when_hidden, incr_font
from qtmenu import MenuWidget

from src.main.python.plotlyst.view.common import ButtonPressResizeEventFilter, action
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.display import Icon


@dataclass
class TreeSettings:
    font_incr: int = 0


class BaseTreeWidget(QWidget):
    selectionChanged = pyqtSignal(bool)
    deleted = pyqtSignal()
    iconChanged = pyqtSignal()

    def __init__(self, title: str, icon: Optional[QIcon] = None, parent=None):
        super(BaseTreeWidget, self).__init__(parent)
        self._menuEnabled: bool = True
        self._plusEnabled: bool = True

        self._selectionEnabled: bool = True
        self._selected: bool = False
        self._wdgTitle = QWidget(self)
        self._wdgTitle.setObjectName('wdgTitle')
        hbox(self._wdgTitle)

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
        self._btnMenu.setIconSize(QSize(18, 18))
        self._btnMenu.setHidden(True)
        retain_when_hidden(self._btnMenu)

        self._btnAdd = QToolButton()
        transparent(self._btnAdd)
        self._btnAdd.setIcon(IconRegistry.plus_icon('grey'))
        self._btnAddPressFilter = ButtonPressResizeEventFilter(self._btnAdd)
        self._btnAdd.installEventFilter(self._btnAddPressFilter)
        self._btnAdd.setHidden(True)

        self._actionChangeIcon = action('Change icon', IconRegistry.icons_icon(), self._changeIcon)
        self._actionDelete = action('Delete', IconRegistry.trash_can_icon(), self.deleted.emit)
        self._initMenu()

        self._wdgTitle.layout().addWidget(self._icon)
        self._wdgTitle.layout().addWidget(self._lblTitle)
        self._wdgTitle.layout().addWidget(self._btnMenu)
        self._wdgTitle.layout().addWidget(self._btnAdd)

    def _initMenu(self):
        menu = MenuWidget(self._btnMenu)
        self._initMenuActions(menu)
        menu.aboutToHide.connect(self._hideAll)

        self._actionChangeIcon.setVisible(False)

        self._btnMenu.installEventFilter(ButtonPressResizeEventFilter(self._btnMenu))

    def _initMenuActions(self, menu: MenuWidget):
        menu.addAction(self._actionChangeIcon)
        menu.addSeparator()
        menu.addAction(self._actionDelete)

    def titleWidget(self) -> QWidget:
        return self._wdgTitle

    def titleLabel(self) -> QLabel:
        return self._lblTitle

    def select(self):
        self._toggleSelection(True)

    def deselect(self):
        self._toggleSelection(False)

    def isSelected(self) -> bool:
        return self._selected

    def setSelectionEnabled(self, enabled: bool):
        self._selectionEnabled = enabled

    def isSelectionEnabled(self) -> bool:
        return self._selectionEnabled

    def setMenuEnabled(self, enabled: bool):
        self._menuEnabled = enabled

    def setPlusButtonEnabled(self, enabled: bool):
        self._plusEnabled = enabled

    def setPlusMenu(self, menu: MenuWidget):
        menu.aboutToHide.connect(self._hideAll)
        self._btnAdd.removeEventFilter(self._btnAddPressFilter)
        self._btnAddPressFilter = ButtonPressResizeEventFilter(self._btnAdd)
        self._btnAdd.installEventFilter(self._btnAddPressFilter)

    def _toggleSelection(self, selected: bool):
        if not self._selectionEnabled:
            return
        self._selected = selected
        bold(self._lblTitle, self._selected)
        self._reStyle()

    def _changeIcon(self):
        result = IconSelectorDialog().display()
        if result:
            self._icon.setIcon(IconRegistry.from_name(result[0], result[1].name()))
            self._icon.setVisible(True)
            self._iconChanged(result[0], result[1].name())
            self.iconChanged.emit()

    def _iconChanged(self, iconName: str, iconColor: str):
        pass

    def _hideAll(self):
        self._btnMenu.setHidden(True)
        self._btnAdd.setHidden(True)

    def _reStyle(self):
        if self._selected:
            self._wdgTitle.setStyleSheet('''
                    #wdgTitle {
                        background-color: #D8D5D5;
                    }
                ''')
        else:
            self._wdgTitle.setStyleSheet('')


class ContainerNode(BaseTreeWidget):

    def __init__(self, title: str, icon: Optional[QIcon] = None, parent=None, settings: Optional[TreeSettings] = None):
        super(ContainerNode, self).__init__(title, icon, parent)
        vbox(self, 0, 0)

        self._container = QWidget(self)
        self._container.setHidden(True)
        vbox(self._container, 1, spacing=0)
        margins(self._container, left=20)
        margins(self._wdgTitle, left=15)
        self.layout().addWidget(self._wdgTitle)
        self.layout().addWidget(self._container)

        if settings:
            incr_font(self._lblTitle, settings.font_incr)

        self._icon.installEventFilter(self)
        self._wdgTitle.installEventFilter(self)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self._wdgTitle:
            if event.type() == QEvent.Type.Enter:
                if self._menuEnabled and self.isEnabled():
                    self._btnMenu.setVisible(True)
                if self._plusEnabled and self.isEnabled():
                    self._btnAdd.setVisible(True)
                if not self._selected and self.isEnabled():
                    self._wdgTitle.setStyleSheet('#wdgTitle {background-color: #E9E7E7;}')
            elif event.type() == QEvent.Type.Leave:
                if (self._menuEnabled and self._btnMenu.menu().isVisible()) or \
                        (self._plusEnabled and self._btnAdd.menu() and self._btnAdd.menu().isVisible()):
                    return super(ContainerNode, self).eventFilter(watched, event)
                self._btnMenu.setHidden(True)
                self._btnAdd.setHidden(True)
                if not self._selected:
                    self._wdgTitle.setStyleSheet('')
        if event.type() == QEvent.Type.MouseButtonRelease and self.isEnabled() and self.isSelectionEnabled():
            if not self._selected:
                self.select()
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

    def childrenWidgets(self) -> List[QWidget]:
        widgets = []
        for i in range(self._container.layout().count()):
            item = self._container.layout().itemAt(i)
            if item is None:
                continue
            widgets.append(item.widget())

        return widgets


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

    def centralWidget(self) -> QWidget:
        return self._centralWidget
