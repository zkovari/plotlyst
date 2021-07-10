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
from typing import Dict, Optional

from PyQt5.QtCore import Qt, QPoint, QEvent, pyqtSignal
from PyQt5.QtGui import QPaintEvent, QPainter, QPen, QPainterPath, QPixmap, QMouseEvent
from PyQt5.QtWidgets import QWidget, QMenu, QAction, QApplication
from overrides import overrides

from plotlyst.core.domain import Scene


class StoryLinesMapWidget(QWidget):
    colors = [Qt.red, Qt.blue, Qt.green, Qt.magenta, Qt.darkBlue, Qt.darkGreen]

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setMouseTracking(True)
        self.novel = None
        self._scene_coord_y: Dict[int, int] = {}

    @overrides
    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.ToolTip:
            pos: QPoint = event.pos()
            index = int((pos.x() / 25) - 1)
            self.setToolTip(self.novel.scenes[index].title)

            return super().event(event)
        return super().event(event)

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        rect = self.rect()
        h = rect.height()
        w = rect.width()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for i, story in enumerate(self.novel.story_lines):
            y = 50 * (i + 1)
            path = QPainterPath()
            painter.setPen(QPen(self.colors[i], 4, Qt.SolidLine))
            path.moveTo(0, y)
            path.lineTo(5, y)

            for j, scene in enumerate(self.novel.scenes):
                x = 25 * (j + 1)
                if story in scene.story_lines:
                    if j not in self._scene_coord_y.keys():
                        self._scene_coord_y[j] = y
                    if i == 1 and j == 2:
                        path.arcTo(x, self._scene_coord_y[j], 20, 20, 25, 25)
                    else:
                        path.lineTo(x, self._scene_coord_y[j])
                    painter.drawPath(path)

        for j, scene in enumerate(self.novel.scenes):
            x = 25 * (j + 1)
            if not j in self._scene_coord_y.keys():
                continue
            if len(scene.story_lines) == 1:
                painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
                painter.setBrush(Qt.black)
                painter.drawEllipse(x, self._scene_coord_y[j] - 7, 14, 14)
            else:
                painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
                painter.setBrush(Qt.white)
                painter.drawEllipse(x, self._scene_coord_y[j] - 10, 20, 20)


class StoryLinesLinearMapWidget(QWidget):
    colors = [Qt.red, Qt.blue, Qt.green, Qt.magenta, Qt.darkBlue, Qt.darkGreen]

    scene_selected = pyqtSignal(Scene)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setMouseTracking(True)
        self.novel = None
        self._clicked_scene: Optional[Scene] = None

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu_requested)

    @overrides
    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.ToolTip:
            pos: QPoint = event.pos()
            index = int((pos.x() / 25) - 1)
            self.setToolTip(self.novel.scenes[index].title)

            return super().event(event)
        return super().event(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos: QPoint = event.pos()
        index = int((pos.x() / 25) - 1)
        if index < len(self.novel.scenes):
            self._clicked_scene = self.novel.scenes[index]
            self.repaint()
            self.scene_selected.emit(self._clicked_scene)

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        rect = self.rect()
        h = rect.height()
        w = rect.width()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for i, story in enumerate(self.novel.story_lines):
            y = 50 * (i + 1) + 25
            painter.setPen(QPen(self.colors[i], 4, Qt.SolidLine))
            painter.drawLine(0, y, w, y)
            painter.setPen(QPen(Qt.black, 5, Qt.SolidLine))
            painter.drawText(5, y - 15, story.text)

            for j, scene in enumerate(self.novel.scenes):
                x = 25 * (j + 1)
                if story in scene.story_lines:
                    if scene == self._clicked_scene:
                        pen = Qt.red
                    else:
                        pen = Qt.black
                    if len(scene.story_lines) == 1:
                        painter.setPen(QPen(pen, 3, Qt.SolidLine))
                        painter.setBrush(Qt.black)
                        painter.drawEllipse(x, y - 7, 14, 14)
                    else:
                        painter.setPen(QPen(pen, 3, Qt.SolidLine))
                        painter.setBrush(Qt.white)
                        painter.drawEllipse(x, y - 10, 20, 20)

        for j, scene in enumerate(self.novel.scenes):
            x = 25 * (j + 1)
            if not scene.story_lines:
                if scene == self._clicked_scene:
                    pen = Qt.red
                else:
                    pen = Qt.gray
                painter.setPen(QPen(pen, 3, Qt.SolidLine))
                painter.setBrush(Qt.gray)
                painter.drawEllipse(x, 3, 14, 14)

    def _context_menu_requested(self, pos: QPoint):
        menu = QMenu(self)

        wip_action = QAction('Copy image', menu)
        wip_action.triggered.connect(self._copy_image)
        menu.addAction(wip_action)

        menu.popup(self.mapToGlobal(pos))

    def _copy_image(self):
        clipboard = QApplication.clipboard()
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        clipboard.setPixmap(pixmap)
