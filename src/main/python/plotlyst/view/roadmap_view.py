"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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
import datetime
from typing import Optional, Dict

from PyQt6.QtCore import QEvent, QThreadPool, QSize, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QSizePolicy, QFrame, QLineEdit
from overrides import overrides
from qthandy import clear_layout, hbox, spacer, margins, vbox, incr_font, retain_when_hidden

from plotlyst.common import PLOTLYST_SECONDARY_COLOR
from plotlyst.core.domain import Board, Task
from plotlyst.env import app_env
from plotlyst.service.resource import JsonDownloadWorker, JsonDownloadResult
from plotlyst.view.common import push_btn, spin, shadow
from plotlyst.view.generated.roadmap_view_ui import Ui_RoadmapView
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.task import BaseStatusColumnWidget


class RoadmapTaskWidget(QFrame):

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self._task: Task = task

        vbox(self, margin=5)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.setMinimumHeight(75)
        shadow(self, 3)

        self._lineTitle = QLineEdit(self)
        self._lineTitle.setPlaceholderText('New task')
        self._lineTitle.setText(task.title)
        self._lineTitle.setFrame(False)
        self._lineTitle.setReadOnly(True)
        font = QFont(app_env.sans_serif_font())
        font.setWeight(QFont.Weight.Medium)
        self._lineTitle.setFont(font)
        incr_font(self._lineTitle)

        # top_wdg = group(self._lineTitle, spacer(), self._charSelector, margin=0, spacing=1)
        self.layout().addWidget(self._lineTitle, alignment=Qt.AlignmentFlag.AlignTop)

        self._wdgBottom = QWidget()
        retain_when_hidden(self._wdgBottom)
        hbox(self._wdgBottom)

        # self._btnTags = TaskTagSelector(self._wdgBottom)
        # self._btnTags.tagSelected.connect(self._tagChanged)

        self._wdgBottom.layout().addWidget(spacer())
        self.layout().addWidget(self._wdgBottom, alignment=Qt.AlignmentFlag.AlignBottom)

        # if self._task.tags:
        #     tag = task_tags.get(self._task.tags[0], None)
        #     if tag:
        #         self._btnTags.select(tag)
        # else:
        #     self._btnTags.setHidden(True)

        # self.installEventFilter(self)

    # @overrides
    # def eventFilter(self, watched: QObject, event: QEvent) -> bool:
    #     if event.type() == QEvent.Type.Enter:
    #         if not self._task.character_id:
    #             self._charSelector.setVisible(True)
    #         self._btnMenu.setVisible(True)
    #         self._btnResolve.setVisible(True)
    #         self._btnTags.setVisible(True)
    #     elif event.type() == QEvent.Type.Leave:
    #         if any_menu_visible(self._charSelector, self._btnMenu, self._btnTags):
    #             return True
    #         self._onLeave()
    #     return super(TaskWidget, self).eventFilter(watched, event)

    def task(self) -> Task:
        return self._task


class RoadmapStatusColumn(BaseStatusColumnWidget):

    def addTask(self, task: Task):
        wdg = RoadmapTaskWidget(task, self)
        self._container.layout().insertWidget(self._container.layout().count() - 1, wdg,
                                              alignment=Qt.AlignmentFlag.AlignTop)


class RoadmapBoardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        hbox(self, spacing=20)
        self._statusColumns: Dict[str, RoadmapStatusColumn] = {}

    def setBoard(self, board: Board):
        clear_layout(self)
        self._statusColumns.clear()

        for status in board.statuses:
            column = RoadmapStatusColumn(status)
            self.layout().addWidget(column)
            self._statusColumns[str(status.id)] = column

        for task in board.tasks:
            column = self._statusColumns.get(str(task.status_ref))
            column.addTask(task)

        _spacer = spacer()
        _spacer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.layout().addWidget(_spacer)
        margins(self, left=20)


class RoadmapView(QWidget, Ui_RoadmapView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.btnRoadmapIcon.setIcon(IconRegistry.from_name('fa5s.road'))
        self.btnPlus.setIcon(IconRegistry.from_name('mdi.certificate', color_on=PLOTLYST_SECONDARY_COLOR))

        self._last_fetched = None
        self._downloading = False
        self._board: Optional[Board] = None
        self._thread_pool = QThreadPool()

        self._roadmapWidget = RoadmapBoardWidget()
        self.scrollAreaWidgetContents.layout().addWidget(self._roadmapWidget)

        self.wdgLoading.setHidden(True)

    @overrides
    def showEvent(self, event: QEvent):
        super().showEvent(event)

        if self._downloading:
            return

        if self._last_fetched is None or (datetime.datetime.now() - self._last_fetched).total_seconds() > 86400:
            self._handle_downloading_status(True)
            self._download_data()

    def _download_data(self):
        result = JsonDownloadResult()
        runnable = JsonDownloadWorker("https://raw.githubusercontent.com/plotlyst/feed/refs/heads/main/posts.json",
                                      result)
        result.finished.connect(self._handle_downloaded_data)
        result.failed.connect(self._handle_download_failure)
        self._thread_pool.start(runnable)

    def _handle_downloaded_data(self, data):
        self._board = Board.from_dict(data)
        self._roadmapWidget.setBoard(self._board)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.lblLastUpdated.setText(f"Last updated: {now}")
        self._last_fetched = datetime.datetime.now()
        self._handle_downloading_status(False)

    def _handle_download_failure(self, status_code: int, message: str):
        if self._board is None:
            self.lblLastUpdated.setText("Failed to update data.")
        self._handle_downloading_status(False)

    def _handle_downloading_status(self, loading: bool):
        self._downloading = loading
        self.scrollAreaWidgetContents.setDisabled(loading)
        self.splitter.setHidden(loading)
        self.wdgTopSelectors.setHidden(loading)
        self.wdgLoading.setVisible(loading)
        if loading:
            btn = push_btn(transparent_=True)
            btn.setIconSize(QSize(128, 128))
            self.wdgLoading.layout().addWidget(btn,
                                               alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            spin(btn, PLOTLYST_SECONDARY_COLOR)
        else:
            clear_layout(self.wdgLoading)
