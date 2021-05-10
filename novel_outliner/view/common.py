from enum import Enum
from typing import Optional

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QPainterPath, QPainter, QCursor
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QSizePolicy


class EditorCommand(Enum):
    SAVE = 0
    CLOSE_CURRENT_EDITOR = 1
    DISPLAY_CHARACTERS = 2
    DISPLAY_SCENES = 3


def rounded_pixmap(original: QPixmap) -> QPixmap:
    size = max(original.width(), original.height())

    rounded = QPixmap(size, size)
    rounded.fill(Qt.transparent)
    path = QPainterPath()
    path.addEllipse(QRectF(rounded.rect()))
    painter = QPainter(rounded)
    painter.setClipPath(path)
    painter.fillRect(rounded.rect(), Qt.black)
    x = int((original.width() - size) / 2)
    y = int((original.height() - size) / 2)

    painter.drawPixmap(x, y, original.width(), original.height(), original)

    return rounded


def ask_confirmation(message: str, parent: Optional[QWidget] = None) -> bool:
    """Raise a confirmation dialog. Return True if the user clicked Yes, False otherwise."""
    QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
    status: int = QMessageBox.question(parent, 'Confirmation', message)
    QApplication.restoreOverrideCursor()
    if status & QMessageBox.Yes:
        return True
    return False


def spacer_widget(max_width: Optional[int] = None) -> QWidget:
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    if max_width:
        spacer.setMaximumWidth(max_width)
    return spacer
