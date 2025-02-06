"""
Plotlyst
Copyright (C) 2021-2025  Zsolt Kovari

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

import qtanim
from PyQt6.QtCore import QPoint, QSize, Qt
from PyQt6.QtGui import QMouseEvent, QColor
from PyQt6.QtWidgets import QWidget, QButtonGroup, QToolButton
from overrides import overrides
from qthandy import vbox, hbox, pointy, line, incr_font
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget

from plotlyst.common import PLOTLYST_SECONDARY_COLOR, RELAXED_WHITE_COLOR
from plotlyst.core.domain import Novel, DailyProductivity, ProductivityType
from plotlyst.env import app_env
from plotlyst.view.common import label, frame, ButtonPressResizeEventFilter, to_rgba_str
from plotlyst.view.icons import IconRegistry
from plotlyst.view.style.base import apply_white_menu
from plotlyst.view.style.button import apply_button_palette_color
from plotlyst.view.widget.display import IconText


class ProductivityTypeButton(QToolButton):
    def __init__(self, category: ProductivityType, parent=None):
        super().__init__(parent)
        self.category = category
        self.setIcon(IconRegistry.from_name(category.icon, 'grey', RELAXED_WHITE_COLOR))
        self.setCheckable(True)
        self.setText(category.text)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(24, 24))
        self.setMinimumWidth(80)
        self.installEventFilter(ButtonPressResizeEventFilter(self))
        pointy(self)
        # self.installEventFilter(OpacityEventFilter(self, ignoreCheckedButton=True))
        if app_env.is_mac():
            incr_font(self)

        hover_bg = to_rgba_str(QColor(self.category.icon_color), 45)
        checked_bg = to_rgba_str(QColor(self.category.icon_color), 150)
        self.setStyleSheet(f'''
                            QToolButton {{
                                border: 1px hidden lightgrey;
                                border-radius: 10px;
                                padding: 2px;
                            }}
                            QToolButton:hover:!checked {{
                                background: {hover_bg};
                            }}
                            QToolButton:checked {{
                                background: {checked_bg};
                                color: {RELAXED_WHITE_COLOR};
                            }}
                            ''')

        self.toggled.connect(self._toggled)

    def _toggled(self, toggled: bool):
        # bold(self, toggled)
        if toggled:
            color = QColor(self.category.icon_color)
            color.setAlpha(175)
            qtanim.glow(self, radius=8, color=color, reverseAnimation=False,
                        teardown=lambda: self.setGraphicsEffect(None))


class ProductivityTrackingWidget(QWidget):
    def __init__(self, productivity: DailyProductivity, parent=None):
        super().__init__(parent)
        vbox(self)
        self.setProperty('relaxed-white-bg', True)

        self.wdgTypes = frame()
        self.wdgTypes.setProperty('relaxed-white-bg', True)
        self.wdgTypes.setProperty('rounded', True)
        hbox(self.wdgTypes, 5, 8)
        self.btnGroup = QButtonGroup()
        for category in productivity.categories:
            btn = ProductivityTypeButton(category)
            # btn.setText(type_.text)
            # btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            # btn.setIconSize(QSize(28, 28))
            # btn.installEventFilter(OpacityEventFilter(btn, ignoreCheckedButton=True))
            self.btnGroup.addButton(btn)
            self.wdgTypes.layout().addWidget(btn)

        self.layout().addWidget(label('Daily productivity tracker', h5=True), alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(label('In which category did you make the most progress today?', description=True))
        self.layout().addWidget(line())
        self.layout().addWidget(self.wdgTypes)

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        pass


class ProductivityButton(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        hbox(self, spacing=0)
        self._novel: Optional[Novel] = None
        self._trackerWdg: Optional[ProductivityTrackingWidget] = None
        self._menu: Optional[MenuWidget] = None

        self.icon = IconText()
        self.icon.setIcon(IconRegistry.from_name('mdi6.progress-star-four-points', color=PLOTLYST_SECONDARY_COLOR))
        self.icon.setText('Days:')
        apply_button_palette_color(self.icon, PLOTLYST_SECONDARY_COLOR)
        self.icon.clicked.connect(self._popup)

        self.streak = label('0', incr_font_diff=4, color=PLOTLYST_SECONDARY_COLOR)
        self.streak.setStyleSheet(f'''
            color: {PLOTLYST_SECONDARY_COLOR};
            font-family: {app_env.serif_font()};
            ''')

        self.layout().addWidget(self.icon)
        self.layout().addWidget(self.streak)

        pointy(self)
        self.installEventFilter(OpacityEventFilter(self, leaveOpacity=0.7))

    def setNovel(self, novel: Novel):
        self._novel = novel
        self.streak.setText(str(self._novel.productivity.overall_days))

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._popup()

    def _popup(self):
        self._trackerWdg = ProductivityTrackingWidget(self._novel.productivity)
        self._menu = MenuWidget()
        apply_white_menu(self._menu)
        self._menu.addWidget(self._trackerWdg)
        self._menu.exec(self.mapToGlobal(QPoint(0, self.sizeHint().height() + 10)))
