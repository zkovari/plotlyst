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
import datetime

from PyQt6.QtCore import QThreadPool
from PyQt6.QtGui import QShowEvent
from PyQt6.QtWidgets import QWidget, QTabWidget
from overrides import overrides
from qthandy import vbox, hbox

from plotlyst.common import PLOTLYST_MAIN_COLOR
from plotlyst.service.resource import JsonDownloadResult, JsonDownloadWorker
from plotlyst.view.common import label
from plotlyst.view.icons import IconRegistry


class SurveyResultsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        vbox(self).addWidget(label('Survey'))


class PatronsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        vbox(self).addWidget(label('Patrons'))


class PlotlystPlusWidget(QWidget):
    DOWNLOAD_THRESHOLD_SECONDS = 60 * 60 * 8  # 8 hours in seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        hbox(self)

        self.tabWidget = QTabWidget()
        self.tabWidget.setProperty('centered', True)
        self.tabWidget.setProperty('large-rounded', True)
        self.tabWidget.setProperty('relaxed-white-bg', True)
        self.tabWidget.setMaximumWidth(1000)
        self.tabReport = QWidget()
        self.tabPatreon = QWidget()
        self.tabPlus = QWidget()
        self.tabPatrons = QWidget()

        self.tabWidget.addTab(self.tabReport, IconRegistry.from_name('mdi.crystal-ball', color_on=PLOTLYST_MAIN_COLOR),
                              'Vision')
        self.tabWidget.addTab(self.tabPatreon, IconRegistry.from_name('fa5b.patreon', color_on=PLOTLYST_MAIN_COLOR),
                              'Patreon')
        self.tabWidget.addTab(self.tabPlus, IconRegistry.from_name('mdi.certificate', color_on=PLOTLYST_MAIN_COLOR),
                              'Plotlyst Plus')
        self.tabWidget.addTab(self.tabPatrons, IconRegistry.from_name('msc.organization', color_on=PLOTLYST_MAIN_COLOR),
                              'Community')

        self.layout().addWidget(self.tabWidget)

        self._last_fetched = None
        self._downloading = False

        self._thread_pool = QThreadPool()

    @overrides
    def showEvent(self, event: QShowEvent):
        super().showEvent(event)

        if self._downloading:
            return

        if self._last_fetched is None or (
                datetime.datetime.now() - self._last_fetched).total_seconds() > self.DOWNLOAD_THRESHOLD_SECONDS:
            self._handle_downloading_status(True)
            self._download_data()

    def _download_data(self):
        result = JsonDownloadResult()
        runnable = JsonDownloadWorker("https://raw.githubusercontent.com/plotlyst/feed/refs/heads/main/posts.json",
                                      result)
        result.finished.connect(self._handle_downloaded_patreon_data)
        result.failed.connect(self._handle_download_failure)
        self._thread_pool.start(runnable)

    def _handle_downloaded_patreon_data(self, data):
        print(data)

    def _handle_downloading_status(self, loading: bool):
        pass
