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
import math
from functools import partial
from typing import Optional, Tuple, List

import qtawesome
from PyQt6.QtCore import Qt, QRectF, QModelIndex, QRect, QPoint, QBuffer, QIODevice, QSize, QObject, QEvent
from PyQt6.QtGui import QPixmap, QPainterPath, QPainter, QFont, QColor, QIcon, QAction
from PyQt6.QtWidgets import QWidget, QSizePolicy, QColorDialog, QAbstractItemView, \
    QMenu, QAbstractButton, \
    QStackedWidget, QAbstractScrollArea, QLineEdit, QHeaderView, QScrollArea, QFrame, QTabWidget, \
    QGraphicsDropShadowEffect, QTableView, QPushButton, QToolButton
from fbs_runtime import platform
from overrides import overrides
from qtanim import fade_out
from qthandy import hbox, vbox, margins, gc

from src.main.python.plotlyst.env import app_env


def rounded_pixmap(original: QPixmap) -> QPixmap:
    size = min(original.width(), original.height())

    rounded = QPixmap(size, size)
    rounded.fill(Qt.GlobalColor.transparent)

    path = QPainterPath()
    path.addEllipse(QRectF(rounded.rect()))
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setClipPath(path)
    painter.fillRect(rounded.rect(), Qt.GlobalColor.black)

    painter.drawPixmap(0, 0, original.width(), original.height(), original)
    painter.end()

    return rounded


def emoji_font() -> QFont:
    if platform.is_mac():
        return QFont('Apple Color Emoji', 20)
    if platform.is_windows():
        return QFont('Segoe UI Emoji', 14)
    return QFont('Noto Emoji', 18)


def show_color_picker(default_color: QColor = QColor('white')) -> QColor:
    if platform.is_linux():
        color: QColor = QColorDialog.getColor(QColor(default_color),
                                              options=QColorDialog.ColorDialogOption.DontUseNativeDialog)
    else:
        color = QColorDialog.getColor(QColor(default_color))

    return color


def text_color_with_bg_color(bg_color: str) -> str:
    rgb = QColor(bg_color).getRgb()
    r = rgb[0]
    g = rgb[1]
    b = rgb[2]
    hsp = math.sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b))
    return 'black' if hsp > 127.5 else 'white'


def action(text: str, icon: Optional[QIcon] = None, slot=None, parent=None, checkable: bool = False) -> QAction:
    _action = QAction(text)
    if icon:
        _action.setIcon(icon)
    if slot:
        _action.triggered.connect(slot)
    if parent:
        _action.setParent(parent)
    _action.setCheckable(checkable)

    return _action


class PopupMenuBuilder:
    def __init__(self, parent: QWidget, viewport: QWidget, pos: QPoint):
        self._parent = parent
        self._viewport = viewport
        self.menu = QMenu(parent)
        self.pos = pos

    @staticmethod
    def from_index(view: QAbstractItemView, index: QModelIndex) -> 'PopupMenuBuilder':
        rect: QRect = view.visualRect(index)
        return PopupMenuBuilder(view, view.viewport(), QPoint(rect.x(), rect.y()))

    @staticmethod
    def from_widget_position(widget: QWidget, pos: QPoint) -> 'PopupMenuBuilder':
        return PopupMenuBuilder(widget, widget, pos)

    def add_action(self, text: str, icon: Optional[QIcon] = None, slot=None) -> QAction:
        _action = action(text, icon, slot)
        _action.setParent(self.menu)
        self.menu.addAction(_action)
        return _action

    def add_separator(self):
        self.menu.addSeparator()

    def add_section(self, text: str, icon: Optional[QIcon] = None):
        action = self.menu.addSection(text)
        if icon:
            action.setIcon(icon)

    def add_submenu(self, text: str, icon: Optional[QIcon] = None) -> QMenu:
        submenu = QMenu(text, self.menu)
        if icon:
            submenu.setIcon(icon)
        self.menu.addMenu(submenu)

        return submenu

    def popup(self):
        self.menu.popup(self._viewport.mapToGlobal(self.pos))


class ButtonPressResizeEventFilter(QObject):
    def __init__(self, parent):
        super(ButtonPressResizeEventFilter, self).__init__(parent)
        self._originalSize: Optional[QSize] = None
        self._reducedSize: Optional[QSize] = None
        if isinstance(parent, (QPushButton, QToolButton)):
            if parent.menu():
                parent.menu().aboutToHide.connect(lambda: self._resetSize(parent))

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QAbstractButton):
            if event.type() == QEvent.Type.MouseButtonPress and watched.isEnabled():
                if self._originalSize is None:
                    self._calculateSize(watched)
                watched.setIconSize(self._reducedSize)
            elif event.type() == QEvent.Type.MouseButtonRelease and watched.isEnabled():
                self._resetSize(watched)

        return super(ButtonPressResizeEventFilter, self).eventFilter(watched, event)

    def _calculateSize(self, watched):
        self._originalSize = watched.iconSize()
        self._reducedSize = watched.iconSize()
        self._reducedSize.setWidth(self._originalSize.width() - 1)
        self._reducedSize.setHeight(self._originalSize.height() - 1)

    def _resetSize(self, watched):
        if self._originalSize is None:
            self._calculateSize(watched)
        watched.setIconSize(self._originalSize)


def link_buttons_to_pages(stack: QStackedWidget, buttons: List[Tuple[QAbstractButton, QWidget]]):
    def _open(widget: QWidget, toggled: bool):
        if toggled:
            stack.setCurrentWidget(widget)

    for btn, wdg in buttons:
        btn.toggled.connect(partial(_open, wdg))


def link_editor_to_btn(editor: QWidget, btn: QAbstractButton):
    if isinstance(editor, QLineEdit):
        editor.textChanged.connect(lambda: btn.setEnabled((len(editor.text()) > 0)))


def scroll_to_top(scroll_area: QAbstractScrollArea):
    scroll_area.verticalScrollBar().setValue(0)


def scroll_to_bottom(scroll_area: QAbstractScrollArea):
    scroll_area.verticalScrollBar().setValue(scroll_area.verticalScrollBar().maximum())


def hmax(widget: QWidget):
    vpol = widget.sizePolicy().verticalPolicy()
    widget.setSizePolicy(QSizePolicy.Policy.Maximum, vpol)


def wrap(widget: QWidget, margin_left: int = 0, margin_top: int = 0, margin_right: int = 0,
         margin_bottom: int = 0) -> QWidget:
    parent = QWidget()
    vbox(parent, 0, 0).addWidget(widget)
    margins(parent, margin_left, margin_top, margin_right, margin_bottom)

    return parent


def spin(btn: QAbstractButton, color: str = 'black'):
    spin_icon = qtawesome.icon('fa5s.spinner', color=color,
                               animation=qtawesome.Spin(btn))
    btn.setIcon(spin_icon)


def icon_to_html_img(icon: QIcon, size: int = 20) -> str:
    if app_env.is_mac() and size > 15:
        size = size - 10
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    pixmap = icon.pixmap(QSize(size, size))
    pixmap.save(buffer, "PNG", quality=100)
    return f"<img src='data:image/png;base64, {bytes(buffer.data().toBase64()).decode()}'>"


def pointy(widget):
    widget.setCursor(Qt.CursorShape.PointingHandCursor)


def restyle(widget: QWidget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def shadow(wdg: QWidget, offset: int = 2):
    effect = QGraphicsDropShadowEffect(wdg)
    effect.setBlurRadius(0)
    effect.setOffset(offset, offset)
    effect.setColor(Qt.GlobalColor.lightGray)
    wdg.setGraphicsEffect(effect)


def autoresize_col(view: QTableView, col: int):
    view.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)


def stretch_col(view: QTableView, col: int):
    view.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)


def scrolled(parent: QWidget, frameless: bool = False) -> Tuple[QScrollArea, QWidget]:
    scrollArea = QScrollArea(parent)
    scrollArea.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    scrollArea.setWidgetResizable(True)

    widget = QWidget(scrollArea)
    scrollArea.setWidget(widget)
    if not parent.layout():
        hbox(parent, 0, 0)
    parent.layout().addWidget(scrollArea)

    if frameless:
        scrollArea.setFrameStyle(QFrame.Shape.NoFrame)

    return scrollArea, widget


def set_tab_icon(tabs: QTabWidget, widget: QWidget, icon: QIcon):
    i = tabs.indexOf(widget)
    tabs.setTabIcon(i, icon)


def fade_out_and_gc(parent: QWidget, widget: QWidget, duration: int = 200):
    def destroy():
        widget.setHidden(True)
        parent.layout().removeWidget(widget)
        gc(widget)

    anim = fade_out(widget, duration)
    anim.finished.connect(destroy)
