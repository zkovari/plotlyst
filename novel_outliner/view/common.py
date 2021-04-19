from enum import Enum

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QPainterPath, QPainter


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
