"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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
from typing import List, Any

import qtawesome
from PyQt5.QtCore import QModelIndex, Qt, QAbstractListModel, pyqtSignal
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QWidget, QListView, QColorDialog
from overrides import overrides

from src.main.python.plotlyst.view.generated.icon_selector_widget_ui import Ui_IconsSelectorWidget
from src.main.python.plotlyst.view.icons import IconRegistry


class IconSelectorWidget(QWidget, Ui_IconsSelectorWidget):
    iconSelected = pyqtSignal(QIcon, QColor)

    def __init__(self, parent=None):
        super(IconSelectorWidget, self).__init__(parent)
        self.setupUi(self)

        qtawesome._instance()
        fonts_maps = qtawesome._resource['iconic'].charmap

        icons: List[str] = []
        for font, font_data in fonts_maps.items():
            if font == 'fa5b':
                continue
            for icon in font_data:
                icons.append(f'{font}.{icon}')
        self.model = self._Model(icons)
        self.lstIcons.setModel(self.model)
        self.lstIcons.setViewMode(QListView.IconMode)
        self.lstIcons.clicked.connect(self._icon_clicked)

        self._color: QColor = QColor('black')
        self._update_button_color()

        self.btnColor.clicked.connect(self._change_color)

    def _update_button_color(self):
        self.btnColor.setStyleSheet(f'''
        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {self._color.name()}, stop: 1 {self._color.name()}) ;''')

    def _change_color(self):
        color: QColor = QColorDialog.getColor(QColor(self._color),
                                              options=QColorDialog.DontUseNativeDialog)
        if color.isValid():
            self._color = color
            self._update_button_color()

    def _icon_clicked(self, index: QModelIndex):
        icon: QIcon = index.data(role=Qt.DecorationRole)
        self.iconSelected.emit(icon, self._color)

    class _Model(QAbstractListModel):

        def __init__(self, icons: List[str]):
            super().__init__()
            self.icons = icons

        @overrides
        def rowCount(self, parent: QModelIndex = ...) -> int:
            return len(self.icons)

        @overrides
        def data(self, index: QModelIndex, role: int) -> Any:
            if role == Qt.DecorationRole:
                return IconRegistry.from_name(self.icons[index.row()])
