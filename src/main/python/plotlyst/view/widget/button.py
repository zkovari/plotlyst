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
from functools import partial
from typing import Optional

import qtanim
from PyQt6.QtCore import pyqtSignal, Qt, pyqtProperty, QTimer, QEvent
from PyQt6.QtGui import QColor, QIcon, QMouseEvent
from PyQt6.QtWidgets import QPushButton, QSizePolicy, QToolButton, QAbstractButton, QLabel, QButtonGroup, QMenu, QWidget
from overrides import overrides
from qtanim import fade_in
from qthandy import hbox, translucent, bold, incr_font, transparent, retain_when_hidden, underline, vbox, decr_icon
from qthandy.filter import OpacityEventFilter, VisibilityToggleEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import PLOTLYST_TERTIARY_COLOR
from src.main.python.plotlyst.core.domain import SelectionItem, Novel
from src.main.python.plotlyst.service.importer import SyncImporter
from src.main.python.plotlyst.view.common import pointy, ButtonPressResizeEventFilter, tool_btn, spin
from src.main.python.plotlyst.view.icons import IconRegistry


class SelectionItemPushButton(QPushButton):
    itemDoubleClicked = pyqtSignal(SelectionItem)

    def __init__(self, parent=None):
        super(SelectionItemPushButton, self).__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._item: Optional[SelectionItem] = None
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.clicked.connect(self._checkDoubleClick)

    def selectionItem(self) -> Optional[SelectionItem]:
        return self._item

    def setSelectionItem(self, item: SelectionItem):
        self.setText(item.text)
        if item.icon:
            self.setIcon(IconRegistry.from_name(item.icon, item.icon_color))

        if self._item is None:
            self._item = item
            self.toggled.connect(self._toggled)
        else:
            self._item = item

    def _toggled(self, checked: bool):
        bold(self, checked)

    def _checkDoubleClick(self):
        if not self._item:
            return
        if self.timer.isActive():
            self.itemDoubleClicked.emit(self._item)
            self.timer.stop()
        else:
            self.timer.start(250)


class _SecondaryActionButton(QAbstractButton):
    def __init__(self, parent=None):
        super(_SecondaryActionButton, self).__init__(parent)
        self._iconName: str = ''
        self._iconColor: str = 'black'
        self._checkedColor: str = 'black'
        self._padding: int = 2
        self.initStyleSheet()
        pointy(self)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
        self.installEventFilter(OpacityEventFilter(self, leaveOpacity=0.7))

    def initStyleSheet(self, border_color: str = 'grey', border_style: str = 'dashed', color: str = 'grey'):
        self.setStyleSheet(f'''
                {self.__class__.__name__} {{
                    border: 2px {border_style} {border_color};
                    border-radius: 6px;
                    color: {color};
                    padding: {self._padding}px;
                }}
                {self.__class__.__name__}:pressed {{
                    border: 2px solid {border_color};
                }}
                {self.__class__.__name__}:checked {{
                    border: 2px solid {self._checkedColor};
                }}
                {self.__class__.__name__}::menu-indicator {{width:0px;}}
            ''')

    def setBorderColor(self, color_name: str):
        self.initStyleSheet(color_name)
        self.update()

    def setPadding(self, value: int):
        if not value:
            return
        self._padding = value
        self.initStyleSheet()
        self.update()

    def _setIcon(self):
        if self._iconName:
            self.setIcon(IconRegistry.from_name(self._iconName, self._iconColor, color_on=self._checkedColor))


class SecondaryActionToolButton(QToolButton, _SecondaryActionButton):
    @pyqtProperty(str)
    def iconName(self):
        return self._iconName

    @iconName.setter
    def iconName(self, value):
        self._iconName = value
        self._setIcon()

    @pyqtProperty(str)
    def iconColor(self):
        return self._iconColor

    @iconColor.setter
    def iconColor(self, value):
        self._iconColor = value
        self._setIcon()

    @pyqtProperty(str)
    def checkedColor(self):
        return self._checkedColor

    @checkedColor.setter
    def checkedColor(self, value):
        self._checkedColor = value
        self.initStyleSheet()
        self._setIcon()


class SecondaryActionPushButton(QPushButton, _SecondaryActionButton):
    @pyqtProperty(str)
    def iconName(self):
        return self._iconName

    @iconName.setter
    def iconName(self, value):
        self._iconName = value
        self._setIcon()

    @pyqtProperty(str)
    def iconColor(self):
        return self._iconColor

    @iconColor.setter
    def iconColor(self, value):
        self._iconColor = value
        self._setIcon()

    @pyqtProperty(str)
    def checkedColor(self):
        return self._checkedColor

    @checkedColor.setter
    def checkedColor(self, value):
        self._checkedColor = value
        self.initStyleSheet()
        self._setIcon()


class WordWrappedPushButton(QPushButton):
    def __init__(self, parent=None):
        super(WordWrappedPushButton, self).__init__(parent)
        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox(self, 0, 0).addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)

    @overrides
    def setText(self, text: str):
        self.label.setText(text)
        self.setFixedHeight(self.label.height() + 5)


class FadeOutButtonGroup(QButtonGroup):
    def __init__(self, parent=None):
        super(FadeOutButtonGroup, self).__init__(parent)
        self.buttonClicked.connect(self._clicked)
        self.setExclusive(False)
        self._opacity = 0.7
        self._fadeInDuration = 250

    def setButtonOpacity(self, opacity: float):
        self._opacity = opacity

    def setFadeInDuration(self, duration: int):
        self._fadeInDuration = duration

    def toggle(self, btn: QAbstractButton):
        btn.setVisible(True)
        btn.setEnabled(True)
        btn.setChecked(not btn.isChecked())
        self._toggled(btn, animated=False)

    def setButtonChecked(self, btn: QAbstractButton, checked: bool):
        btn.setVisible(True)
        btn.setEnabled(True)
        btn.setChecked(checked)
        self._toggled(btn, animated=False)

    def reset(self):
        for btn in self.buttons():
            btn.setEnabled(True)
            btn.setChecked(False)
            btn.setVisible(True)
            translucent(btn, self._opacity)

    def _clicked(self, btn: QAbstractButton):
        self._toggled(btn)

    def _toggled(self, btn: QAbstractButton, animated: bool = True):
        for other_btn in self.buttons():
            if other_btn is btn:
                continue

            if btn.isChecked():
                other_btn.setChecked(False)
                other_btn.setDisabled(True)
                if animated:
                    qtanim.fade_out(other_btn)
                else:
                    other_btn.setHidden(True)
            else:
                other_btn.setEnabled(True)
                if animated:
                    anim = qtanim.fade_in(other_btn, duration=self._fadeInDuration)
                    anim.finished.connect(partial(translucent, other_btn, self._opacity))
                else:
                    other_btn.setVisible(True)


class ToolbarButton(QToolButton):
    def __init__(self, parent=None):
        super(ToolbarButton, self).__init__(parent)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setCheckable(True)
        pointy(self)

        self.toggled.connect(lambda x: bold(self, x))

        self.setStyleSheet(f'''
            QToolButton:checked {{
                color: #240046;
                background-color: {PLOTLYST_TERTIARY_COLOR};
            }}
        ''')

        incr_font(self, 1)

    @overrides
    def enterEvent(self, event: QEvent) -> None:
        qtanim.colorize(self, color=QColor('#7B2CBF'))


class CollapseButton(QPushButton):
    def __init__(self, idle: Qt.Edge, checked: Qt.Edge, parent=None):
        super(CollapseButton, self).__init__(parent)
        self._idleIcon = self._icon(idle)
        self._checkedIcon = self._icon(checked)
        self.setIcon(self._idleIcon)
        self.setCheckable(True)

        pointy(self)
        transparent(self)

        self.toggled.connect(self._toggled)

    def _toggled(self, checked: bool):
        if checked:
            self.setIcon(self._checkedIcon)
        else:
            self.setIcon(self._idleIcon)

    def _icon(self, direction: Qt.Edge) -> QIcon:
        if direction == Qt.Edge.TopEdge:
            return IconRegistry.from_name('fa5s.chevron-up')
        elif direction == Qt.Edge.LeftEdge:
            return IconRegistry.from_name('fa5s.chevron-left')
        elif direction == Qt.Edge.RightEdge:
            return IconRegistry.from_name('fa5s.chevron-right')
        else:
            return IconRegistry.from_name('fa5s.chevron-down')


class DotsMenuButton(QToolButton):
    def __init__(self, parent=None):
        super(DotsMenuButton, self).__init__(parent)
        transparent(self)
        retain_when_hidden(self)
        pointy(self)
        self.setIcon(IconRegistry.dots_icon('grey', vertical=True))
        self._pressFilter: Optional[ButtonPressResizeEventFilter] = None

    @overrides
    def setMenu(self, menu: QMenu):
        super(DotsMenuButton, self).setMenu(menu)
        if self._pressFilter is None:
            self._pressFilter = ButtonPressResizeEventFilter(self)
            self.installEventFilter(self._pressFilter)


class ReturnButton(QPushButton):
    def __init__(self, parent=None):
        super(ReturnButton, self).__init__(parent)
        self.setIcon(IconRegistry.return_icon())
        self.setText('Back')
        self.setProperty('return', True)
        underline(self)
        bold(self)
        self.installEventFilter(ButtonPressResizeEventFilter(self))

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        translucent(self, 0.8)
        super(ReturnButton, self).mousePressEvent(event)

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        translucent(self, 1)
        super(ReturnButton, self).mouseReleaseEvent(event)


class _NovelSyncWidget(QWidget):
    def __init__(self, parent=None):
        super(_NovelSyncWidget, self).__init__(parent)
        self.setProperty('relaxed-white-bg', True)

        self._wdgTop = QWidget()
        hbox(self._wdgTop)
        self._wdgCenter = QWidget()
        hbox(self._wdgCenter)
        self._wdgBottom = QWidget()
        hbox(self._wdgBottom)

        self.lblTitle = QLabel('Novel synchronization')
        underline(self.lblTitle)
        bold(self.lblTitle)

        self.btnChangeLocation = tool_btn(IconRegistry.from_name('fa5.folder-open'))
        transparent(self.btnChangeLocation)
        decr_icon(self.btnChangeLocation, 4)
        retain_when_hidden(self.btnChangeLocation)
        self.btnChangeLocation.installEventFilter(OpacityEventFilter(self.btnChangeLocation))
        self._wdgTop.layout().addWidget(self.lblTitle, alignment=Qt.AlignmentFlag.AlignCenter)
        self._wdgTop.layout().addWidget(self.btnChangeLocation, alignment=Qt.AlignmentFlag.AlignRight)

        self.lblUpdateMessage = QLabel()
        self.lblUpdateMessage.setProperty('description', True)
        self._wdgCenter.layout().addWidget(self.lblUpdateMessage, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lblErrorNotFoundMessage = QLabel('Project not found.')
        self.lblErrorNotFoundMessage.setProperty('error', True)
        self.lblErrorNotFoundMessage.setHidden(True)
        self._wdgCenter.layout().addWidget(self.lblErrorNotFoundMessage, alignment=Qt.AlignmentFlag.AlignCenter)

        self.btnCheck = QPushButton('Check for updates')
        self.btnCheck.setProperty('base', True)
        pointy(self.btnCheck)
        self.btnCheck.setIcon(IconRegistry.refresh_icon('black'))
        self.btnCheck.installEventFilter(ButtonPressResizeEventFilter(self.btnCheck))

        self.btnSync = QPushButton('Synchronize')
        pointy(self.btnSync)
        self.btnSync.setProperty('base', True)
        self.btnSync.setProperty('positive', True)
        self.btnSync.setIcon(IconRegistry.refresh_icon('white'))
        self.btnSync.installEventFilter(ButtonPressResizeEventFilter(self.btnSync))

        self._wdgBottom.layout().addWidget(self.btnCheck, alignment=Qt.AlignmentFlag.AlignCenter)
        self._wdgBottom.layout().addWidget(self.btnSync, alignment=Qt.AlignmentFlag.AlignCenter)

        self.installEventFilter(VisibilityToggleEventFilter(self.btnChangeLocation, self))

        vbox(self)
        self.layout().addWidget(self._wdgTop)
        self.layout().addWidget(self._wdgCenter)
        self.layout().addWidget(self._wdgBottom)


class NovelSyncButton(QPushButton):
    UP_TO_DATE_MSG: str = 'Up-to-date'
    UPDATES_AVAILABLE_MSG: str = 'New updates are available'

    def __init__(self, parent=None):
        super(NovelSyncButton, self).__init__(parent)
        self.setProperty('importer-sync', True)
        self.installEventFilter(ButtonPressResizeEventFilter(self))
        self.installEventFilter(OpacityEventFilter(self, leaveOpacity=0.7))
        pointy(self)

        self._icon = QIcon()
        self._importer: Optional[SyncImporter] = None
        self._novel: Optional[Novel] = None

        self._menu = MenuWidget(self)
        self._wdgSync = _NovelSyncWidget()
        self._menu.addWidget(self._wdgSync)

        self._wdgSync.btnCheck.clicked.connect(self._checkForUpdates)
        self._wdgSync.btnSync.clicked.connect(self._sync)

    def setImporter(self, importer: SyncImporter, novel: Novel):
        self._importer = importer
        self._novel = novel
        self._icon = self._importer.icon()
        self.setIcon(self._icon)
        self.setText(self._importer.name())

        location = self._importer.location(self._novel)
        self._wdgSync.lblTitle.setText(location)
        self._wdgSync.lblTitle.setToolTip(self._novel.import_origin.source)

        self._toggleUpToDate(True)

    def clear(self):
        self._novel = None
        self._importer = None

    def _checkForUpdates(self):
        prev_icon = self._wdgSync.btnCheck.icon()
        spin(self._wdgSync.btnCheck)
        if self._importer.location_exists(self._novel):
            self._wdgSync.lblErrorNotFoundMessage.setHidden(True)
            self.setIcon(self._icon)

            if self._importer.is_updated(self._novel):
                fade_in(self._wdgSync.lblUpdateMessage)
            else:
                self._toggleUpToDate(False)
                fade_in(self._wdgSync.lblUpdateMessage)
                fade_in(self._wdgSync.btnSync)
        else:
            self.setIcon(IconRegistry.from_name('ri.error-warning-fill', '#e76f51'))
            self._wdgSync.lblUpdateMessage.setHidden(True)
            self._wdgSync.lblErrorNotFoundMessage.setVisible(True)

        QTimer.singleShot(100, lambda: self._wdgSync.btnCheck.setIcon(prev_icon))

    def _sync(self):
        self._importer.sync(self._novel)

        self._toggleUpToDate(True)
        self.menu().close()

    def _toggleUpToDate(self, updated: bool):
        # hide all first to avoid layout problems
        self._wdgSync.btnCheck.setHidden(True)
        self._wdgSync.btnSync.setHidden(True)

        self._wdgSync.btnCheck.setVisible(updated)
        self._wdgSync.btnSync.setHidden(updated)

        self._wdgSync.lblUpdateMessage.setText(self.UP_TO_DATE_MSG if updated else self.UPDATES_AVAILABLE_MSG)
