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

from PyQt5.QtCore import Qt, QPoint, QEvent, pyqtSignal, QSize
from PyQt5.QtGui import QPaintEvent, QPainter, QPen, QPainterPath, QPixmap, QMouseEvent, QColor
from PyQt5.QtWidgets import QWidget, QMenu, QAction, QApplication
from overrides import overrides

from src.main.python.plotlyst.core.domain import Scene, Novel


class StoryLinesMapWidget(QWidget):
    scene_selected = pyqtSignal(Scene)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setMouseTracking(True)
        self.novel: Optional[Novel] = None
        self._scene_coord_y: Dict[int, int] = {}
        self._clicked_scene: Optional[Scene] = None

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu_requested)

    def setNovel(self, novel: Novel):
        self.novel = novel

    @overrides
    def minimumSizeHint(self) -> QSize:
        if self.novel:
            x = self._scene_x(len(self.novel.scenes) - 1) + 50
            y = self._story_line_y(len(self.novel.story_lines)) * 2
            return QSize(x, y)
        return super().minimumSizeHint()

    @overrides
    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.ToolTip:
            index = self._index_from_pos(event.pos())
            if index < len(self.novel.scenes):
                self.setToolTip(self.novel.scenes[index].title)

            return super().event(event)
        return super().event(event)

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        index = self._index_from_pos(event.pos())
        if index < len(self.novel.scenes):
            self._clicked_scene = self.novel.scenes[index]
            self.update()
            self.scene_selected.emit(self._clicked_scene)

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.white)
        self._scene_coord_y.clear()
        y = 0
        for sl_i, story in enumerate(self.novel.story_lines):
            y = self._story_line_y(sl_i)
            path = QPainterPath()
            painter.setPen(QPen(QColor(story.color_hexa), 4, Qt.SolidLine))
            path.moveTo(0, y)
            path.lineTo(5, y)

            for sc_i, scene in enumerate(self.novel.scenes):
                x = self._scene_x(sc_i)
                if story in scene.story_lines:
                    if sc_i not in self._scene_coord_y.keys():
                        self._scene_coord_y[sc_i] = y
                    path.lineTo(x, self._scene_coord_y[sc_i])
                    painter.drawPath(path)

        for sc_i, scene in enumerate(self.novel.scenes):
            if sc_i not in self._scene_coord_y.keys():
                continue
            self._draw_scene_ellipse(painter, scene, self._scene_x(sc_i), self._scene_coord_y[sc_i])

        base_y = y
        for sl_i, story in enumerate(self.novel.story_lines):
            y = 50 * (sl_i + 1) + 25 + base_y
            painter.setPen(QPen(QColor(story.color_hexa), 4, Qt.SolidLine))
            painter.drawLine(0, y, self.rect().width(), y)
            painter.setPen(QPen(Qt.black, 5, Qt.SolidLine))
            painter.drawText(5, y - 15, story.text)

            for sc_i, scene in enumerate(self.novel.scenes):
                if story in scene.story_lines:
                    self._draw_scene_ellipse(painter, scene, self._scene_x(sc_i), y)

        for sc_i, scene in enumerate(self.novel.scenes):
            if not scene.story_lines:
                self._draw_scene_ellipse(painter, scene, self._scene_x(sc_i), 3)

    def _draw_scene_ellipse(self, painter: QPainter, scene: Scene, x: int, y: int):
        if scene.story_lines:
            pen = Qt.red if scene is self._clicked_scene else Qt.black
            if len(scene.story_lines) == 1:
                painter.setPen(QPen(pen, 3, Qt.SolidLine))
                painter.setBrush(Qt.black)
                painter.drawEllipse(x, y - 7, 14, 14)
            else:
                painter.setPen(QPen(pen, 3, Qt.SolidLine))
                painter.setBrush(Qt.white)
                painter.drawEllipse(x, y - 10, 20, 20)
        else:
            pen = Qt.red if scene is self._clicked_scene else Qt.gray
            painter.setPen(QPen(pen, 3, Qt.SolidLine))
            painter.setBrush(Qt.gray)
            painter.drawEllipse(x, y, 14, 14)

    @staticmethod
    def _story_line_y(index: int) -> int:
        return 50 * (index + 1)

    @staticmethod
    def _scene_x(index: int) -> int:
        return 25 * (index + 1)

    @staticmethod
    def _index_from_pos(pos: QPoint) -> int:
        return int((pos.x() / 25) - 1)

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
