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
import functools
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QPainterPath, QPainter, QCursor, QFont
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QSizePolicy, QFrame
from fbs_runtime import platform


class EditorCommandType(Enum):
    UPDATE_SCENE_SEQUENCES = 5


@dataclass
class EditorCommand:
    type: EditorCommandType
    value: Optional[Any] = None

    @staticmethod
    def close_editor():
        return EditorCommand(EditorCommandType.CLOSE_CURRENT_EDITOR)

    @staticmethod
    def display_scenes():
        return EditorCommand(EditorCommandType.DISPLAY_SCENES)

    @staticmethod
    def display_characters():
        return EditorCommand(EditorCommandType.DISPLAY_CHARACTERS)


def rounded_pixmap(original: QPixmap) -> QPixmap:
    size = max(original.width(), original.height())

    rounded = QPixmap(size, size)
    rounded.fill(Qt.transparent)
    path = QPainterPath()
    path.addEllipse(QRectF(rounded.rect()))
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setClipPath(path)
    painter.fillRect(rounded.rect(), Qt.black)
    x = int((original.width() - size) / 2)
    y = int((original.height() - size) / 2)

    painter.drawPixmap(x, y, original.width(), original.height(), original)
    painter.end()
    # pr = QWindow().devicePixelRatio()
    # print(pr)
    # rounded.setDevicePixelRatio(pr)

    return rounded


def ask_confirmation(message: str, parent: Optional[QWidget] = None) -> bool:
    """Raise a confirmation dialog. Return True if the user clicked Yes, False otherwise."""
    QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
    status: int = QMessageBox.question(parent, 'Confirmation', message)
    QApplication.restoreOverrideCursor()
    if status & QMessageBox.Yes:
        return True
    return False


def spacer_widget(max_width: Optional[int] = None, vertical: bool = False) -> QWidget:
    spacer = QWidget()
    if vertical:
        spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    else:
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    if max_width:
        spacer.setMaximumWidth(max_width)
    return spacer


def line(vertical: bool = False) -> QFrame:
    line = QFrame()
    if vertical:
        line.setFrameShape(QFrame.VLine)
    else:
        line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)

    return line


def busy(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))
        try:
            return func(*args, **kwargs)
        finally:
            QApplication.restoreOverrideCursor()

    return wrapper_timer


def emoji_font(size: int = 13) -> QFont:
    if platform.is_mac():
        return QFont('Apple Color Emoji', size)
    if platform.is_windows():
        return QFont('Segoe UI Emoji', size)
    return QFont('Noto Emoji', size)
