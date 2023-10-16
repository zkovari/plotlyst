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
from typing import Optional

import qtanim
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFileDialog
from qthandy import incr_font
from qthandy.filter import DisabledClickEventFilter, OpacityEventFilter

from src.main.python.plotlyst.common import MAXIMUM_SIZE
from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.core.scrivener import ScrivenerParser
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import EventListener, Event
from src.main.python.plotlyst.event.handler import global_event_dispatcher
from src.main.python.plotlyst.resources import resource_registry, ResourceType
from src.main.python.plotlyst.service.tour import TourService
from src.main.python.plotlyst.view.common import link_buttons_to_pages, link_editor_to_btn, ButtonPressResizeEventFilter
from src.main.python.plotlyst.view.generated.story_creation_dialog_ui import Ui_StoryCreationDialog
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.tour.core import NewStoryTitleInDialogTourEvent, \
    NewStoryTitleFillInDialogTourEvent, NewStoryDialogOkayButtonTourEvent
from src.main.python.plotlyst.view.widget.utility import ask_for_resource


class StoryCreationDialog(QDialog, Ui_StoryCreationDialog, EventListener):

    def __init__(self, parent=None):
        super(StoryCreationDialog, self).__init__(parent)
        self.setupUi(self)

        self._scrivenerNovel: Optional[Novel] = None

        link_buttons_to_pages(self.stackedWidget,
                              [(self.btnNewStory, self.pageNewStory), (self.btnScrivener, self.pageScrivener)])
        self.lineTitle.setFocus()
        self.wdgScrivenerImportDetails.setHidden(True)
        self.lblBanner.setPixmap(QPixmap(resource_registry.banner))
        self.btnNewStory.setIcon(IconRegistry.book_icon(color_on='white'))
        self.btnScrivener.setIcon(IconRegistry.from_name('mdi.alpha-s-circle-outline', color_on='white'))
        self.btnLoadScrivener.setIcon(IconRegistry.from_name('mdi6.application-import', color='white'))
        self.btnLoadScrivener.clicked.connect(self._loadFromScrivener)
        self.btnLoadScrivener.installEventFilter(ButtonPressResizeEventFilter(self.btnLoadScrivener))
        incr_font(self.btnNewStory)
        incr_font(self.btnScrivener)

        self.btnSaveNewStory = self.btnBoxStoryCreation.button(QDialogButtonBox.StandardButton.Ok)
        self.btnSaveNewStory.setDisabled(True)
        self.btnSaveNewStory.installEventFilter(
            DisabledClickEventFilter(self.btnSaveNewStory, lambda: qtanim.shake(self.lineTitle)))
        link_editor_to_btn(self.lineTitle, self.btnSaveNewStory)

        self.btnSaveScrivener = self.btnBoxScrivener.button(QDialogButtonBox.StandardButton.Ok)
        self.btnSaveScrivener.setDisabled(True)
        self.btnSaveScrivener.installEventFilter(
            DisabledClickEventFilter(self.btnSaveScrivener, lambda: qtanim.shake(self.btnLoadScrivener)))
        for btn in [self.btnNewStory, self.btnScrivener]:
            btn.installEventFilter(OpacityEventFilter(parent=btn, ignoreCheckedButton=True))
        self.stackedWidget.currentChanged.connect(self._pageChanged)
        self.stackedWidget.setCurrentWidget(self.pageNewStory)

        self._tour_service: TourService = TourService.instance()
        self._eventTypes = [NewStoryTitleInDialogTourEvent, NewStoryTitleFillInDialogTourEvent,
                            NewStoryDialogOkayButtonTourEvent]
        global_event_dispatcher.register(self, *self._eventTypes)

    def display(self) -> Optional[Novel]:
        self._scrivenerNovel = None
        result = self.exec()
        if result == QDialog.DialogCode.Rejected:
            return None

        if self.stackedWidget.currentWidget() == self.pageNewStory:
            return Novel.new_novel(self.lineTitle.text())
        elif self._scrivenerNovel is not None:
            return self._scrivenerNovel

        return None

    def hideEvent(self, event):
        global_event_dispatcher.deregister(self, *self._eventTypes)
        super(StoryCreationDialog, self).hideEvent(event)

    def event_received(self, event: Event):
        if isinstance(event, NewStoryTitleInDialogTourEvent):
            self._tour_service.addDialogWidget(self, self.lineTitle, event)
        elif isinstance(event, NewStoryTitleFillInDialogTourEvent):
            self.lineTitle.setText(event.title)
            self._tour_service.next()
        elif isinstance(event, NewStoryDialogOkayButtonTourEvent):
            self._tour_service.addDialogWidget(self, self.btnSaveNewStory, event)

    def _pageChanged(self):
        if self.stackedWidget.currentWidget() == self.pageNewStory:
            self.lineTitle.setFocus()

    def _loadFromScrivener(self):
        if not ask_for_resource(ResourceType.PANDOC):
            return
        if app_env.is_dev():
            default_path = 'resources/scrivener/v3/'
        else:
            default_path = None
        if app_env.is_mac():
            project = QFileDialog.getOpenFileName(self, 'Choose a Scrivener project directory', default_path)
            if project:
                project = project[0]
        else:
            project = QFileDialog.getExistingDirectory(self, 'Choose a Scrivener project directory', default_path)
        if not project:
            return

        parser = ScrivenerParser()
        self._scrivenerNovel = parser.parse_project(project)

        self.stackedWidget.setCurrentWidget(self.pageScrivenerPreview)
        self.setMaximumWidth(MAXIMUM_SIZE)
        self.wdgScrivenerImportDetails.setVisible(True)
        self.wdgScrivenerImportDetails.setNovel(self._scrivenerNovel)
        self.btnSaveScrivener.setEnabled(True)
        self.wdgTypesContainer.setHidden(True)
