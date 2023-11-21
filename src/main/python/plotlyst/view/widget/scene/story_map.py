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

from enum import Enum
from functools import partial
from typing import Dict, Optional
from typing import List

import qtanim
from PyQt6.QtCore import QPoint, QTimeLine
from PyQt6.QtCore import Qt, QEvent, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QPaintEvent, QPainter, \
    QPen, QPainterPath, QShowEvent
from PyQt6.QtWidgets import QSizePolicy, QWidget, QTextEdit, QLabel, QPushButton
from overrides import overrides
from qthandy import busy, margins, vspacer, line, incr_font
from qthandy import decr_font, transparent, clear_layout, hbox, spacer, vbox
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.common import truncate_string
from src.main.python.plotlyst.core.domain import Scene, Novel, Plot, \
    ScenePlotReference
from src.main.python.plotlyst.event.core import Event, EventListener
from src.main.python.plotlyst.event.handler import event_dispatchers
from src.main.python.plotlyst.events import SceneOrderChangedEvent
from src.main.python.plotlyst.service.cache import acts_registry
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import hmax, action, tool_btn
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import WordWrappedPushButton
from src.main.python.plotlyst.view.widget.display import Icon
from src.main.python.plotlyst.view.widget.input import RotatedButton, RotatedButtonOrientation


class StoryMapDisplayMode(Enum):
    DOTS = 0
    TITLE = 1
    DETAILED = 2


class StoryLinesMapWidget(QWidget):
    sceneSelected = pyqtSignal(Scene)

    def __init__(self, mode: StoryMapDisplayMode, acts_filter: Dict[int, bool], parent=None):
        super().__init__(parent=parent)
        hbox(self)
        self.setMouseTracking(True)
        self.novel: Optional[Novel] = None
        self._scene_coord_y: Dict[int, int] = {}
        self._clicked_scene: Optional[Scene] = None
        self._display_mode: StoryMapDisplayMode = mode
        self._acts_filter = acts_filter

        if mode == StoryMapDisplayMode.DOTS:
            self._scene_width = 25
            self._top_height = 50
        else:
            self._scene_width = 120
            self._top_height = 50
        self._line_height = 50
        self._first_paint_triggered: bool = False

        self._menuPlots = MenuWidget()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu_requested)

    def setNovel(self, novel: Novel, animated: bool = True):
        def changed(x: int):
            self._first_paint_triggered = True
            self.update(0, 0, x, self.minimumSizeHint().height())

        self.novel = novel
        if animated:
            timeline = QTimeLine(700, parent=self)
            timeline.setFrameRange(0, self.minimumSizeHint().width())
            timeline.frameChanged.connect(changed)

            timeline.start()
        else:
            self._first_paint_triggered = True

    def scenes(self) -> List[Scene]:
        return [x for x in self.novel.scenes if self._acts_filter.get(acts_registry.act(x), True)]

    @overrides
    def minimumSizeHint(self) -> QSize:
        if self.novel:
            x = self._scene_x(len(self.scenes()) - 1) + 50
            y = self._story_line_y(len(self.novel.plots)) * 2
            return QSize(x, y)
        return super().minimumSizeHint()

    @overrides
    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.ToolTip:
            index = self._index_from_pos(event.pos())
            scenes = self.scenes()
            if index < len(scenes):
                self.setToolTip(scenes[index].title_or_index(self.novel))

            return super().event(event)
        return super().event(event)

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        index = self._index_from_pos(event.pos())
        scenes = self.scenes()
        if index < len(scenes):
            self._clicked_scene: Scene = scenes[index]
            self.sceneSelected.emit(self._clicked_scene)
            self.update()

    @overrides
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self._context_menu_requested(event.pos())

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(RELAXED_WHITE_COLOR))

        if not self._first_paint_triggered:
            painter.end()
            return

        scenes = self.scenes()

        self._scene_coord_y.clear()
        y = 0
        last_sc_x: Dict[int, int] = {}
        for sl_i, plot in enumerate(self.novel.plots):
            previous_y = 0
            previous_x = 0
            y = self._story_line_y(sl_i)
            path = QPainterPath()
            painter.setPen(QPen(QColor(plot.icon_color), 4, Qt.PenStyle.SolidLine))
            path.moveTo(0, y)
            IconRegistry.from_name(plot.icon, plot.icon_color).paint(painter, 0, y - 35, 24, 24)
            path.lineTo(5, y)
            painter.drawPath(path)

            for sc_i, scene in enumerate(scenes):
                x = self._scene_x(sc_i)
                if plot in scene.plots():
                    if sc_i not in self._scene_coord_y.keys():
                        self._scene_coord_y[sc_i] = y
                    if previous_y > self._scene_coord_y[sc_i] or (previous_y == 0 and y > self._scene_coord_y[sc_i]):
                        path.lineTo(x - self._scene_width // 2, y)
                    elif 0 < previous_y < self._scene_coord_y[sc_i]:
                        path.lineTo(previous_x + self._scene_width // 2, y)

                    if previous_y == self._scene_coord_y[sc_i] and previous_y != y:
                        path.arcTo(previous_x + 4, self._scene_coord_y[sc_i] - 3, x - previous_x,
                                   self._scene_coord_y[sc_i] - 25,
                                   -180, 180)
                    else:
                        path.lineTo(x, self._scene_coord_y[sc_i])

                    painter.drawPath(path)
                    previous_y = self._scene_coord_y[sc_i]
                    previous_x = x
                    last_sc_x[sl_i] = x

        for sc_i, scene in enumerate(scenes):
            if sc_i not in self._scene_coord_y.keys():
                continue
            self._draw_scene_ellipse(painter, scene, self._scene_x(sc_i), self._scene_coord_y[sc_i])

        for sc_i, scene in enumerate(scenes):
            if not scene.plots():
                self._draw_scene_ellipse(painter, scene, self._scene_x(sc_i), 3)

        if len(self.novel.plots) <= 1:
            return

        base_y = y
        for sl_i, plot in enumerate(self.novel.plots):
            y = 50 * (sl_i + 1) + 25 + base_y
            painter.setPen(QPen(QColor(plot.icon_color), 4, Qt.PenStyle.SolidLine))
            painter.drawLine(0, y, last_sc_x.get(sl_i, 15), y)
            painter.setPen(QPen(Qt.GlobalColor.black, 5, Qt.PenStyle.SolidLine))
            painter.drawPixmap(0, y - 35, IconRegistry.from_name(plot.icon, plot.icon_color).pixmap(24, 24))
            painter.drawText(26, y - 15, plot.text)

            for sc_i, scene in enumerate(scenes):
                if plot in scene.plots():
                    self._draw_scene_ellipse(painter, scene, self._scene_x(sc_i), y)

        painter.end()

    def _draw_scene_ellipse(self, painter: QPainter, scene: Scene, x: int, y: int):
        selected = scene is self._clicked_scene
        if scene.plot_values:
            pen_color = '#CB4D4D' if selected else Qt.GlobalColor.black
            if len(scene.plot_values) == 1:
                painter.setPen(QPen(QColor(pen_color), 3, Qt.PenStyle.SolidLine))
                painter.setBrush(Qt.GlobalColor.black)
                size = 22 if selected else 14
                x_diff = 4 if selected else 0
                painter.drawEllipse(x - x_diff, y - size // 2, size, size)
            else:
                painter.setPen(QPen(QColor(pen_color), 3, Qt.PenStyle.SolidLine))
                painter.setBrush(Qt.GlobalColor.white)
                painter.drawEllipse(x, y - 10, 20, 20)
        else:
            pen_color = '#CB4D4D' if scene is self._clicked_scene else Qt.GlobalColor.gray
            painter.setPen(QPen(QColor(pen_color), 3, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.GlobalColor.gray)
            size = 18 if selected else 14
            x_diff = 2 if selected else 0
            painter.drawEllipse(x - x_diff, y, size, size)

    def _story_line_y(self, index: int) -> int:
        return self._top_height + self._line_height * (index)

    def _scene_x(self, index: int) -> int:
        return self._scene_width * (index + 1)

    def _index_from_pos(self, pos: QPoint) -> int:
        return int((pos.x() / self._scene_width) - 1)

    def _context_menu_requested(self, pos: QPoint) -> None:
        index = self._index_from_pos(pos)
        scenes = self.scenes()
        if index < len(scenes):
            self._clicked_scene: Scene = scenes[index]
            self.update()

            self._menuPlots.clear()
            if self.novel.plots:
                for plot in self.novel.plots:
                    plot_action = action(truncate_string(plot.text, 70),
                                         IconRegistry.from_name(plot.icon, plot.icon_color),
                                         slot=partial(self._plot_changed, plot))
                    self._menuPlots.addAction(plot_action)
                    plot_action.setCheckable(True)
                    if plot in self._clicked_scene.plots():
                        plot_action.setChecked(True)
            else:
                self._menuPlots.addSection('No storylines were found')
            self._menuPlots.exec(self.mapToGlobal(pos))

    @busy
    def _plot_changed(self, plot: Plot, checked: bool):
        if checked:
            self._clicked_scene.plot_values.append(ScenePlotReference(plot))
        else:
            to_be_removed = None
            for plot_v in self._clicked_scene.plot_values:
                if plot_v.plot is plot:
                    to_be_removed = plot_v
                    break
            if to_be_removed:
                self._clicked_scene.plot_values.remove(to_be_removed)
        RepositoryPersistenceManager.instance().update_scene(self._clicked_scene)

        self.update()


GRID_ITEM_WIDTH: int = 190
GRID_ITEM_HEIGHT: int = 120


class _SceneGridItem(QWidget):
    def __init__(self, novel: Novel, scene: Scene, parent=None):
        super(_SceneGridItem, self).__init__(parent)
        self.novel = novel
        self.scene = scene

        vbox(self, spacing=1)

        icon = Icon()
        beat = self.scene.beat(self.novel)
        if beat and beat.icon:
            icon.setIcon(IconRegistry.from_name(beat.icon, beat.icon_color))

        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setText(scene.title_or_index(self.novel))

        self.wdgTop = QWidget()
        hbox(self.wdgTop, 0, 1)
        self.wdgTop.layout().addWidget(spacer())
        self.wdgTop.layout().addWidget(icon)
        self.wdgTop.layout().addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.wdgTop.layout().addWidget(spacer())

        self.textSynopsis = QTextEdit()
        self.textSynopsis.setFontPointSize(self.label.font().pointSize())
        self.textSynopsis.setPlaceholderText('Scene synopsis...')
        self.textSynopsis.setTabChangesFocus(True)
        self.textSynopsis.verticalScrollBar().setVisible(False)
        transparent(self.textSynopsis)
        self.textSynopsis.setAcceptRichText(False)
        self.textSynopsis.setText(self.scene.synopsis)
        self.textSynopsis.textChanged.connect(self._synopsisChanged)

        self.layout().addWidget(self.wdgTop)
        self.layout().addWidget(line())
        self.layout().addWidget(self.textSynopsis)

        self.repo = RepositoryPersistenceManager.instance()

    def _synopsisChanged(self):
        self.scene.synopsis = self.textSynopsis.toPlainText()
        self.repo.update_scene(self.scene)


class _ScenesLineWidget(QWidget):
    def __init__(self, novel: Novel, parent=None, vertical: bool = False):
        super(_ScenesLineWidget, self).__init__(parent)
        self.novel = novel

        if vertical:
            vbox(self, margin=0)
        else:
            hbox(self, margin=0)

        wdgEmpty = QWidget()
        wdgEmpty.setFixedSize(GRID_ITEM_WIDTH, GRID_ITEM_HEIGHT)
        self.layout().addWidget(wdgEmpty)

        if vertical:
            hmax(self)

        for scene in self.novel.scenes:
            wdg = _SceneGridItem(self.novel, scene)
            wdg.setFixedSize(GRID_ITEM_WIDTH, GRID_ITEM_HEIGHT)
            self.layout().addWidget(wdg)

        if vertical:
            self.layout().addWidget(vspacer())
        else:
            self.layout().addWidget(spacer())


class _ScenePlotAssociationsWidget(QWidget):
    LineSize: int = 15

    def __init__(self, novel: Novel, plot: Plot, parent=None, vertical: bool = False):
        super(_ScenePlotAssociationsWidget, self).__init__(parent)
        self.novel = novel
        self.plot = plot
        self._vertical = vertical

        self.setProperty('relaxed-white-bg', True)

        self.wdgReferences = QWidget()
        self.wdgReferences.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        if vertical:
            hbox(self, 0, 0)
            vbox(self.wdgReferences, margin=0, spacing=5)
            margins(self.wdgReferences, top=GRID_ITEM_HEIGHT)
            btnPlot = RotatedButton()
            btnPlot.setOrientation(RotatedButtonOrientation.VerticalBottomToTop)
            hmax(btnPlot)
            self.layout().addWidget(btnPlot, alignment=Qt.AlignmentFlag.AlignTop)

            hmax(self)
        else:
            vbox(self, 0, 0)
            hbox(self.wdgReferences, margin=0, spacing=12)
            margins(self.wdgReferences, left=GRID_ITEM_WIDTH)
            btnPlot = QPushButton()
            self.layout().addWidget(btnPlot, alignment=Qt.AlignmentFlag.AlignLeft)

        btnPlot.setText(self.plot.text)
        incr_font(btnPlot)
        if self.plot.icon:
            btnPlot.setIcon(IconRegistry.from_name(self.plot.icon, self.plot.icon_color))
        transparent(btnPlot)

        self.layout().addWidget(self.wdgReferences)

        for scene in self.novel.scenes:
            pv = next((x for x in scene.plot_values if x.plot.id == self.plot.id), None)
            if pv:
                wdg = self.__initCommentWidget(scene, pv)
            else:
                wdg = QWidget()
                transparent(wdg)
                wdg.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
                btnPlus = tool_btn(IconRegistry.plus_circle_icon('grey'), 'Associate to storyline', transparent_=True)
                btnPlus.setIconSize(QSize(32, 32))
                btnPlus.installEventFilter(OpacityEventFilter(btnPlus, enterOpacity=0.7, leaveOpacity=0.2))
                btnPlus.clicked.connect(partial(self._linkToPlot, wdg, scene))
                vbox(wdg).addWidget(btnPlus, alignment=Qt.AlignmentFlag.AlignCenter)

            wdg.setFixedSize(GRID_ITEM_WIDTH, GRID_ITEM_HEIGHT)
            self.wdgReferences.layout().addWidget(wdg)

        if vertical:
            self.wdgReferences.layout().addWidget(vspacer())
        else:
            self.wdgReferences.layout().addWidget(spacer())

        self.repo = RepositoryPersistenceManager.instance()

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(self.plot.icon_color))
        painter.setBrush(QColor(self.plot.icon_color))

        if self._vertical:
            painter.drawRect(self.rect().width() // 2 - 4, 5, 8, self.rect().height())
        else:
            painter.drawRect(5, 50, self.rect().width(), 8)

    def _commentChanged(self, editor: QTextEdit, scene: Scene, scenePlotRef: ScenePlotReference):
        scenePlotRef.data.comment = editor.toPlainText()
        self.repo.update_scene(scene)

    def _linkToPlot(self, placeholder: QWidget, scene: Scene):
        ref = ScenePlotReference(self.plot)
        scene.plot_values.append(ref)

        wdg = self.__initCommentWidget(scene, ref)
        wdg.setFixedSize(GRID_ITEM_WIDTH, GRID_ITEM_HEIGHT)
        self.wdgReferences.layout().replaceWidget(placeholder, wdg)
        qtanim.fade_in(wdg)
        wdg.setFocus()

        self.repo.update_scene(scene)

    def __initCommentWidget(self, scene: Scene, ref: ScenePlotReference) -> QWidget:
        wdg = QTextEdit()
        wdg.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        wdg.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        wdg.setPlaceholderText('How is the scene related to this storyline?')
        wdg.setTabChangesFocus(True)
        wdg.setStyleSheet(f'''
                            border:2px solid {self.plot.icon_color};
                            padding: 4px;
                            border-radius: 6px;
                        ''')
        wdg.setText(ref.data.comment)
        wdg.textChanged.connect(partial(self._commentChanged, wdg, scene, ref))

        return wdg


class StoryMap(QWidget, EventListener):
    sceneSelected = pyqtSignal(Scene)

    def __init__(self, parent=None):
        super(StoryMap, self).__init__(parent)
        self.novel: Optional[Novel] = None
        self._display_mode: StoryMapDisplayMode = StoryMapDisplayMode.DOTS
        self._orientation: int = Qt.Orientation.Horizontal
        self._acts_filter: Dict[int, bool] = {}
        vbox(self, spacing=0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # apply to every QWidget inside
        self.setStyleSheet(f'QWidget {{background-color: {RELAXED_WHITE_COLOR};}}')

        self._refreshOnShow = False

    def setNovel(self, novel: Novel):
        self.novel = novel
        dispatcher = event_dispatchers.instance(self.novel)
        dispatcher.register(self, SceneOrderChangedEvent)
        self.refresh()

    @overrides
    def event_received(self, event: Event):
        if self.isVisible():
            self.refresh()
        else:
            self._refreshOnShow = True

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        if self._refreshOnShow:
            self._refreshOnShow = False
            self.refresh()

    def refresh(self, animated: bool = True):
        if not self.novel:
            return
        clear_layout(self)

        if self._display_mode == StoryMapDisplayMode.DETAILED:
            wdgScenePlotParent = QWidget(self)
            if self._orientation == Qt.Orientation.Horizontal:
                vbox(wdgScenePlotParent, spacing=0)
            else:
                hbox(wdgScenePlotParent, spacing=0)

            wdgScenes = _ScenesLineWidget(self.novel, vertical=self._orientation == Qt.Orientation.Vertical)
            wdgScenePlotParent.layout().addWidget(wdgScenes)

            for plot in self.novel.plots:
                wdg = _ScenePlotAssociationsWidget(self.novel, plot, parent=self,
                                                   vertical=self._orientation == Qt.Orientation.Vertical)
                wdgScenePlotParent.layout().addWidget(wdg)

            if self._orientation == Qt.Orientation.Horizontal:
                wdgScenePlotParent.layout().addWidget(vspacer())
            else:
                wdgScenePlotParent.layout().addWidget(spacer())
            self.layout().addWidget(wdgScenePlotParent)

        else:
            wdg = StoryLinesMapWidget(self._display_mode, self._acts_filter, parent=self)
            self.layout().addWidget(wdg)
            wdg.setNovel(self.novel, animated=animated)
            if self._display_mode == StoryMapDisplayMode.TITLE:
                titles = QWidget(self)
                titles.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
                titles.setProperty('relaxed-white-bg', True)
                hbox(titles, 0, 0)
                margins(titles, left=70)
                self.layout().insertWidget(0, titles)
                for scene in wdg.scenes():
                    btn = WordWrappedPushButton(parent=self)
                    btn.setFixedWidth(120)
                    btn.setText(scene.title_or_index(self.novel))
                    decr_font(btn.label, step=2)
                    transparent(btn)
                    titles.layout().addWidget(btn)
                titles.layout().addWidget(spacer())
            wdg.sceneSelected.connect(self.sceneSelected.emit)

    @busy
    def setMode(self, mode: StoryMapDisplayMode):
        if self._display_mode == mode:
            return
        self._display_mode = mode
        if self.novel:
            self.refresh()

    @busy
    def setOrientation(self, orientation: int):
        self._orientation = orientation
        if self._display_mode != StoryMapDisplayMode.DETAILED:
            return
        if self.novel:
            self.refresh()

    def setActsFilter(self, act: int, filtered: bool):
        self._acts_filter[act] = filtered
        if self.novel:
            self.refresh(animated=False)
