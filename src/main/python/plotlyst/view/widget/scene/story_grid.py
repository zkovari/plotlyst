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
from functools import partial

import qtanim
from PyQt6.QtCore import QTimer
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPaintEvent, QPainter
from PyQt6.QtWidgets import QWidget, QTextEdit, QLabel, QPushButton
from overrides import overrides
from qthandy import margins, vspacer, line, incr_font, sp
from qthandy import transparent, hbox, spacer, vbox
from qthandy.filter import OpacityEventFilter, VisibilityToggleEventFilter

from plotlyst.common import WHITE_COLOR
from plotlyst.core.domain import Scene, Novel, Plot, \
    ScenePlotReference
from plotlyst.service.persistence import RepositoryPersistenceManager
from plotlyst.view.common import hmax, tool_btn, ButtonPressResizeEventFilter, fade_out_and_gc
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.display import Icon
from plotlyst.view.widget.input import RotatedButton, RotatedButtonOrientation, RemovalButton
from plotlyst.view.widget.timeline import TimelineGridWidget

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
            vbox(self, margin=0, spacing=5)
        else:
            hbox(self, margin=0, spacing=12)

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

        sp(self).v_max()


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
                wdg = self.__initPlusWidget(scene)
            self.wdgReferences.layout().addWidget(wdg)

        if vertical:
            self.wdgReferences.layout().addWidget(vspacer())
        else:
            self.wdgReferences.layout().addWidget(spacer())

        self.repo = RepositoryPersistenceManager.instance()
        sp(self).v_max()

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(self.plot.icon_color))
        painter.setBrush(QColor(self.plot.icon_color))
        painter.setOpacity(0.7)

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
        self.wdgReferences.layout().replaceWidget(placeholder, wdg)
        qtanim.fade_in(wdg)
        wdg.setFocus()

        self.repo.update_scene(scene)

    def _removePlotLink(self, editor: QTextEdit, scene: Scene, ref: ScenePlotReference):
        i = self.wdgReferences.layout().indexOf(editor)
        fade_out_and_gc(self.wdgReferences, editor)
        wdg = self.__initPlusWidget(scene)
        QTimer.singleShot(200, lambda: self.wdgReferences.layout().insertWidget(i, wdg))

        scene.plot_values.remove(ref)
        self.repo.update_scene(scene)

    def __initCommentWidget(self, scene: Scene, ref: ScenePlotReference) -> QWidget:
        wdg = QTextEdit()
        wdg.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        wdg.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        wdg.setPlaceholderText('How is the scene related to this storyline?')
        wdg.setTabChangesFocus(True)
        wdg.setStyleSheet(f'''
                            border:1px solid {self.plot.icon_color};
                            background: {WHITE_COLOR};
                            padding: 4px;
                            border-radius: 6px;
                        ''')
        wdg.setText(ref.data.comment)
        wdg.textChanged.connect(partial(self._commentChanged, wdg, scene, ref))

        btn = RemovalButton(wdg, ref.plot.icon_color, ref.plot.icon_color, colorHover='lightgrey')
        btn.installEventFilter(ButtonPressResizeEventFilter(btn))
        btn.setGeometry(GRID_ITEM_WIDTH - 20, 1, 20, 20)
        btn.setVisible(True)
        btn.clicked.connect(lambda: self._removePlotLink(wdg, scene, ref))

        wdg.installEventFilter(VisibilityToggleEventFilter(btn, wdg))
        wdg.setFixedSize(GRID_ITEM_WIDTH, GRID_ITEM_HEIGHT)

        return wdg

    def __initPlusWidget(self, scene: Scene) -> QWidget:
        wdg = QWidget()
        transparent(wdg)
        wdg.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        btnPlus = tool_btn(IconRegistry.plus_circle_icon('grey'), 'Associate to storyline', transparent_=True)
        btnPlus.setIconSize(QSize(32, 32))
        btnPlus.installEventFilter(OpacityEventFilter(btnPlus, enterOpacity=0.7, leaveOpacity=0.1))
        btnPlus.clicked.connect(partial(self._linkToPlot, wdg, scene))
        vbox(wdg).addWidget(btnPlus, alignment=Qt.AlignmentFlag.AlignCenter)
        wdg.setFixedSize(GRID_ITEM_WIDTH, GRID_ITEM_HEIGHT)
        wdg.installEventFilter(VisibilityToggleEventFilter(btnPlus, wdg))

        return wdg


# wdgScenePlotParent = QWidget(self)
# if self._orientation == Qt.Orientation.Horizontal:
#     vbox(wdgScenePlotParent, spacing=0)
# else:
#     hbox(wdgScenePlotParent, spacing=0)
#
# wdgScenes = _ScenesLineWidget(self.novel, vertical=self._orientation == Qt.Orientation.Vertical)
# wdgScenePlotParent.layout().addWidget(wdgScenes)
#
# for plot in self.novel.plots:
#     wdg = _ScenePlotAssociationsWidget(self.novel, plot, parent=self,
#                                        vertical=self._orientation == Qt.Orientation.Vertical)
#     wdgScenePlotParent.layout().addWidget(wdg)
#
# if self._orientation == Qt.Orientation.Horizontal:
#     wdgScenePlotParent.layout().addWidget(vspacer())
# else:
#     wdgScenePlotParent.layout().addWidget(spacer())
# self.layout().addWidget(wdgScenePlotParent)


class ScenesGridWidget(TimelineGridWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel

        self.setColumnWidth(200)
        self.setRowHeight(80)

        for plot in self._novel.plots:
            self.addColumn(plot, plot.text, IconRegistry.from_name(plot.icon, plot.icon_color))

        for i, scene in enumerate(self._novel.scenes):
            self.addRow(scene, scene.title_or_index(self._novel))
            for plot_ref in scene.plot_values:
                self.addItem(plot_ref.plot, i, plot_ref, plot_ref.data.comment)
