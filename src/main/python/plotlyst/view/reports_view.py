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
from enum import Enum, auto
from typing import Optional

from PyQt6.QtGui import QShowEvent
from PyQt6.QtWidgets import QWidget
from overrides import overrides
from qthandy import bold, vbox
from qthandy.filter import OpacityEventFilter

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR
from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.events import CharacterChangedEvent, SceneChangedEvent, SceneDeletedEvent, \
    PlotCreatedEvent
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import link_buttons_to_pages, scrolled
from src.main.python.plotlyst.view.generated.reports_view_ui import Ui_ReportsView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.report import AbstractReport
from src.main.python.plotlyst.view.report.character import CharacterReport


class ReportType(Enum):
    CHARACTERS = auto()
    SCENES = auto()
    ARC = auto()
    MANUSCRIPT = auto()


report_classes = {ReportType.CHARACTERS: CharacterReport}


class ReportPage(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super(ReportPage, self).__init__(parent)
        self._novel: Novel = novel
        self._report: Optional[AbstractReport] = None

        vbox(self)

        self._scrollarea, self._wdgCenter = scrolled(self)
        vbox(self._wdgCenter)


class CharactersReportPage(ReportPage):
    def __init__(self, novel: Novel, parent=None):
        super(CharactersReportPage, self).__init__(novel, parent)

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        if self._report is None:
            self._report = CharacterReport(self._novel)
            self._wdgCenter.layout().addWidget(self._report)


class ScenesReportPage(ReportPage):
    def __init__(self, novel: Novel, parent=None):
        super(ScenesReportPage, self).__init__(novel, parent)


class ArcReportPage(ReportPage):
    def __init__(self, novel: Novel, parent=None):
        super(ArcReportPage, self).__init__(novel, parent)


class ManuscriptReportPage(ReportPage):
    def __init__(self, novel: Novel, parent=None):
        super(ManuscriptReportPage, self).__init__(novel, parent)


class ReportsView(AbstractNovelView):
    def __init__(self, novel: Novel):
        super().__init__(novel, [CharacterChangedEvent, SceneChangedEvent, SceneDeletedEvent, PlotCreatedEvent])
        self.ui = Ui_ReportsView()
        self.ui.setupUi(self.widget)

        bold(self.ui.lblTitle)

        self.ui.iconReports.setIcon(IconRegistry.reports_icon())
        self.ui.btnCharacters.setIcon(IconRegistry.character_icon())
        self.ui.btnScenes.setIcon(IconRegistry.scene_icon())
        self.ui.btnArc.setIcon(IconRegistry.rising_action_icon('black', color_on=PLOTLYST_SECONDARY_COLOR))
        self.ui.btnManuscript.setIcon(IconRegistry.manuscript_icon())

        for btn in self.ui.buttonGroup.buttons():
            btn.installEventFilter(OpacityEventFilter(btn, leaveOpacity=0.7, ignoreCheckedButton=True))

        self._page_characters = CharactersReportPage(self.novel)
        self.ui.stackedWidget.addWidget(self._page_characters)
        self._page_scenes = ScenesReportPage(self.novel)
        self.ui.stackedWidget.addWidget(self._page_scenes)
        self._page_arc = ArcReportPage(self.novel)
        self.ui.stackedWidget.addWidget(self._page_arc)
        self._page_manuscript = ManuscriptReportPage(self.novel)
        self.ui.stackedWidget.addWidget(self._page_manuscript)

        link_buttons_to_pages(self.ui.stackedWidget, [(self.ui.btnCharacters, self._page_characters),
                                                      (self.ui.btnScenes, self._page_scenes),
                                                      (self.ui.btnArc, self._page_arc),
                                                      (self.ui.btnManuscript, self._page_manuscript)])

        self.ui.btnCharacters.setChecked(True)

    @overrides
    def refresh(self):
        pass
