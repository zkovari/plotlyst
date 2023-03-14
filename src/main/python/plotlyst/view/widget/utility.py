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
from typing import Any

from PyQt6.QtCore import QModelIndex, Qt, QAbstractListModel, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtWidgets import QWidget, QListView, QSizePolicy, QToolButton, QButtonGroup
from overrides import overrides
from qthandy import flow, btn_popup, transparent

from src.main.python.plotlyst.model.common import proxy
from src.main.python.plotlyst.view.generated.icon_selector_widget_ui import Ui_IconsSelectorWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget._icons import icons_registry
from src.main.python.plotlyst.view.widget.button import SecondaryActionToolButton


class ColorButton(QToolButton):
    def __init__(self, color: str, parent=None):
        super(ColorButton, self).__init__(parent)
        self.color = color


class ColorPicker(QWidget):
    colorPicked = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super(ColorPicker, self).__init__(parent)
        flow(self)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self.btnGroup = QButtonGroup(self)
        self.btnGroup.setExclusive(True)

        for color in ['#0077b6', '#00b4d8', '#007200', '#2a9d8f', '#94d2bd', '#ffe66d', '#ffd000', '#f48c06', '#e85d04',
                      '#dc2f02',
                      '#ffc6ff', '#b5179e', '#7209b7', '#d6ccc2', '#6c757d', '#dda15e', '#bc6c25', 'black', 'white']:
            btn = ColorButton(color, self)
            btn.setIconSize(QSize(22, 22))
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f'''
            QToolButton {{
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                      stop: 0 {color});
                border: 1px solid darkGrey;
                border-radius: 12px;
            }}
            QToolButton:pressed {{
                border: 1px solid white;
            }}
            ''')
            self.btnGroup.addButton(btn)
            self.layout().addWidget(btn)
        self.btnGroup.buttonClicked.connect(self._clicked)

    def color(self) -> QColor:
        btn = self.btnGroup.checkedButton()
        if btn:
            return QColor(btn.color)
        else:
            return QColor(Qt.GlobalColor.black)

    def _clicked(self, btn: ColorButton):
        self.colorPicked.emit(QColor(btn.color))


class IconSelectorWidget(QWidget, Ui_IconsSelectorWidget):
    iconSelected = pyqtSignal(str, QColor)

    def __init__(self, parent=None):
        super(IconSelectorWidget, self).__init__(parent)
        self.setupUi(self)

        self.btnFilterIcon.setIcon(IconRegistry.from_name('mdi.magnify'))

        self.btnPeople.setIcon(IconRegistry.from_name('mdi.account', color_on='darkGreen'))
        self.btnPeople.setToolTip('People and emotions')
        self.btnFood.setIcon(IconRegistry.from_name('fa5s.ice-cream', color_on='darkGreen'))
        self.btnFood.setToolTip('Food and beverage')
        self.btnNature.setIcon(IconRegistry.from_name('mdi.nature', color_on='darkGreen'))
        self.btnNature.setToolTip('Nature')
        self.btnSports.setIcon(IconRegistry.from_name('fa5s.football-ball', color_on='darkGreen'))
        self.btnSports.setToolTip('Sports')
        self.btnObjects.setIcon(IconRegistry.from_name('fa5.lightbulb', color_on='darkGreen'))
        self.btnObjects.setToolTip('Objects')
        self.btnPlaces.setIcon(IconRegistry.from_name('ei.globe', color_on='darkGreen'))
        self.btnPlaces.setToolTip('Places and travel')
        self.btnCharacters.setIcon(IconRegistry.from_name('mdi6.alphabetical-variant', color_on='darkGreen'))
        self.btnCharacters.setToolTip('Numbers and characters')
        self.btnSymbols.setIcon(IconRegistry.from_name('mdi.symbol', color_on='darkGreen'))
        self.btnSymbols.setToolTip('Symbols')
        self.btnAll.setChecked(True)

        self.colorPicker = ColorPicker(self)
        self.colorPicker.colorPicked.connect(self._colorPicked)
        self.hLayoutTop.insertWidget(0, self.colorPicker)

        filtered_icons = []
        for type, icons_list in icons_registry.items():
            for icon in icons_list:
                if icon and icon != 'fa5s.' and icon != 'mdi.':
                    filtered_icons.append(self._IconItem(type, icon))
        self.model = self._Model(filtered_icons)
        self._proxy = proxy(self.model)
        self._proxy.setFilterRole(self._Model.IconTypeRole)
        self.lstIcons.setModel(self._proxy)
        self.lstIcons.setViewMode(QListView.ViewMode.IconMode)
        self.lstIcons.clicked.connect(self._iconClicked)

        self.lineFilter.textChanged.connect(self._textChanged)

        self.buttonGroup.buttonToggled.connect(self._filterToggled)

    def setColor(self, color: QColor):
        self.model.setColor(color)

    def _colorPicked(self, color: QColor):
        self.model.setColor(color)

    def _textChanged(self, text: str):
        self.btnAll.setChecked(True)
        self._proxy.setFilterRole(self._Model.IconAliasRole)
        self._proxy.setFilterRegularExpression(text)

    def _filterToggled(self):
        self.lineFilter.clear()
        self._proxy.setFilterRole(self._Model.IconTypeRole)
        if self.btnPeople.isChecked():
            self._proxy.setFilterFixedString('People')
        elif self.btnFood.isChecked():
            self._proxy.setFilterFixedString('Food')
        elif self.btnNature.isChecked():
            self._proxy.setFilterFixedString('Animals & Nature')
        elif self.btnSports.isChecked():
            self._proxy.setFilterFixedString('Sports & Activities')
        elif self.btnPlaces.isChecked():
            self._proxy.setFilterFixedString('Travel & Places')
        elif self.btnObjects.isChecked():
            self._proxy.setFilterFixedString('Objects')
        elif self.btnCharacters.isChecked():
            self._proxy.setFilterFixedString('Numbers and Characters')
        elif self.btnSymbols.isChecked():
            self._proxy.setFilterFixedString('Symbols')
        elif self.btnAll.isChecked():
            self._proxy.setFilterFixedString('')

    def _iconClicked(self, index: QModelIndex):
        icon_alias: str = index.data(role=self._Model.IconAliasRole)
        self.iconSelected.emit(icon_alias, QColor(self.model.color))

    class _IconItem:
        def __init__(self, type: str, name: str):
            self.type = type
            self.name = name

    class _Model(QAbstractListModel):

        IconAliasRole = Qt.ItemDataRole.UserRole + 1
        IconTypeRole = Qt.ItemDataRole.UserRole + 2

        def __init__(self, icons):
            super().__init__()
            self.icons = icons
            self.color: str = 'black'

        @overrides
        def rowCount(self, parent: QModelIndex = ...) -> int:
            return len(self.icons)

        @overrides
        def data(self, index: QModelIndex, role: int) -> Any:
            if role == self.IconAliasRole:
                return self.icons[index.row()].name
            if role == self.IconTypeRole:
                return self.icons[index.row()].type
            if role == Qt.ItemDataRole.DecorationRole:
                return IconRegistry.from_name(self.icons[index.row()].name, self.color)
            if role == Qt.ItemDataRole.BackgroundRole:
                if self.color == '#ffffff':
                    return QBrush(Qt.GlobalColor.lightGray)
                else:
                    return QBrush(Qt.GlobalColor.white)

            if role == Qt.ItemDataRole.ToolTipRole:
                return self.icons[index.row()].name.split('.')[1].replace('-', ' ').capitalize()

        def setColor(self, color: QColor):
            self.color = color.name()
            self.modelReset.emit()


class IconSelectorButton(SecondaryActionToolButton):
    iconSelected = pyqtSignal(str, QColor)

    def __init__(self, parent=None):
        super(IconSelectorButton, self).__init__(parent)
        self._selectedIconSize = QSize(32, 32)
        self._defaultIconSize = QSize(24, 24)

        self._selector = IconSelectorWidget()
        btn_popup(self, self._selector)
        self.reset()
        self._selector.iconSelected.connect(self._iconSelected)

    def setSelectedIconSize(self, size: QSize):
        self._selectedIconSize = size

    def setDefaultIconSize(self, size: QSize):
        self._defaultIconSize = size

    def selectIcon(self, icon: str, icon_color: str):
        self.setIcon(IconRegistry.from_name(icon, icon_color))
        transparent(self)
        self.setIconSize(self._selectedIconSize)

    def reset(self):
        self.setIconSize(self._defaultIconSize)
        self.setIcon(IconRegistry.icons_icon())
        self.initStyleSheet()

    def _iconSelected(self, icon: str, color: QColor):
        self.selectIcon(icon, color.name())
        self.iconSelected.emit(icon, color)
        self.menu().hide()
