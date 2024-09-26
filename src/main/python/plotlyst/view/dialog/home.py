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
from typing import Optional

from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import QDialog, QFileDialog
from qthandy import incr_font
from qthandy.filter import OpacityEventFilter

from plotlyst.common import MAXIMUM_SIZE
from plotlyst.core.domain import Novel
from plotlyst.core.scrivener import ScrivenerParser
from plotlyst.env import app_env
from plotlyst.event.core import EventListener, Event
from plotlyst.event.handler import global_event_dispatcher
from plotlyst.resources import resource_registry, ResourceType
from plotlyst.service.tour import TourService
from plotlyst.view.common import link_buttons_to_pages, ButtonPressResizeEventFilter
from plotlyst.view.generated.story_creation_dialog_ui import Ui_StoryCreationDialog
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.display import OverlayWidget
from plotlyst.view.widget.input import Toggle
from plotlyst.view.widget.novel import NovelCustomizationWizard
from plotlyst.view.widget.tour.core import NewStoryTitleInDialogTourEvent, \
    NewStoryTitleFillInDialogTourEvent, NewStoryDialogOkayButtonTourEvent, NewStoryDialogWizardCustomizationTourEvent
from plotlyst.service.resource import ask_for_resource


class StoryCreationDialog(QDialog, Ui_StoryCreationDialog, EventListener):

    def __init__(self, parent=None):
        super(StoryCreationDialog, self).__init__(parent)
        self.setupUi(self)

        self._scrivenerNovel: Optional[Novel] = None
        self._wizardNovel: Optional[Novel] = None

        self._wizard: Optional[NovelCustomizationWizard] = None

        link_buttons_to_pages(self.stackedWidget,
                              [(self.btnNewStory, self.pageNewStory), (self.btnScrivener, self.pageScrivener)])
        self.lineTitle.setFocus()
        incr_font(self.lineTitle, 2)
        self.wdgScrivenerImportDetails.setHidden(True)
        self.lblBanner.setPixmap(QPixmap(resource_registry.banner))
        self.btnNewStory.setIcon(IconRegistry.book_icon(color_on='white'))
        self.btnScrivener.setIcon(IconRegistry.from_name('mdi.alpha-s-circle-outline', color_on='white'))
        self.btnLoadScrivener.setIcon(IconRegistry.from_name('mdi6.application-import', color='white'))
        self.btnLoadScrivener.clicked.connect(self._loadFromScrivener)
        self.btnLoadScrivener.installEventFilter(ButtonPressResizeEventFilter(self.btnLoadScrivener))
        incr_font(self.btnNewStory)
        incr_font(self.btnScrivener)

        self.btnCancel.setIcon(IconRegistry.close_icon())
        self.btnCancel.installEventFilter(ButtonPressResizeEventFilter(self.btnCancel))
        self.btnCancel.clicked.connect(self.reject)
        self.btnNext.clicked.connect(self._nextClicked)
        self.btnNext.installEventFilter(ButtonPressResizeEventFilter(self.btnNext))
        self.btnFinish.clicked.connect(self.accept)
        self.btnFinish.setVisible(False)

        self.toggleWizard = Toggle()
        self.toggleWizard.toggled.connect(self._wizardToggled)
        self.toggleWizard.setChecked(True)
        self.wdgWizardSubtitle.addWidget(self.toggleWizard)

        for btn in [self.btnNewStory, self.btnScrivener]:
            btn.installEventFilter(OpacityEventFilter(parent=btn, ignoreCheckedButton=True))
        self.stackedWidget.currentChanged.connect(self._pageChanged)
        self.stackedWidget.setCurrentWidget(self.pageNewStory)

        self._tour_service: TourService = TourService.instance()
        self._eventTypes = [NewStoryTitleInDialogTourEvent, NewStoryTitleFillInDialogTourEvent,
                            NewStoryDialogWizardCustomizationTourEvent,
                            NewStoryDialogOkayButtonTourEvent]
        global_event_dispatcher.register(self, *self._eventTypes)

        self.resize(700, 550)

    def display(self) -> Optional[Novel]:
        overlay = OverlayWidget.getActiveWindowOverlay()
        overlay.show()

        self._scrivenerNovel = None

        try:
            result = self.exec()
        finally:
            overlay.setHidden(True)

        if result == QDialog.DialogCode.Rejected:
            return None

        if self.stackedWidget.currentWidget() == self.pageNewStory:
            return self.__newNovel()
        elif self.stackedWidget.currentWidget() == self.pageWizard:
            return self._wizardNovel
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
        elif isinstance(event, NewStoryDialogWizardCustomizationTourEvent):
            self._tour_service.addDialogWidget(self, self.toggleWizard, event)
        elif isinstance(event, NewStoryDialogOkayButtonTourEvent):
            self._tour_service.addDialogWidget(self, self.btnNext, event)

    def _pageChanged(self):
        if self.stackedWidget.currentWidget() == self.pageNewStory:
            self.lineTitle.setFocus()
            self.btnNext.setVisible(True)
            self.btnFinish.setVisible(False)
        elif self.stackedWidget.currentWidget() == self.pageScrivener:
            self.btnNext.setVisible(False)
            self.btnFinish.setVisible(False)
        elif self.stackedWidget.currentWidget() == self.pageScrivenerPreview:
            self.btnNext.setVisible(False)
            self.btnFinish.setVisible(True)

    def _wizardToggled(self, toggled: bool):
        self.btnNext.setText('Start wizard' if toggled else 'Create')
        if toggled:
            icon = IconRegistry.from_name('ph.magic-wand', 'white', 'white')
        else:
            icon = IconRegistry.book_icon('white', 'white')
        self.btnNext.setIcon(icon)

    def _nextClicked(self):
        if self.stackedWidget.currentWidget() == self.pageNewStory and self.toggleWizard.isChecked():
            self._wizardNovel = self.__newNovel()
            self._wizard = NovelCustomizationWizard(self._wizardNovel)
            self._wizard.stack.currentChanged.connect(self._wizardPageChanged)
            self._wizard.finished.connect(self.accept)
            self.pageWizard.layout().addWidget(self._wizard)
            self.wdgBanner.setHidden(True)
            self.wdgTypesContainer.setHidden(True)
            self.btnNext.setVisible(True)
            self.btnNext.setText('Next')
            self.btnNext.setIcon(QIcon())
            self.btnFinish.setVisible(False)
            self.stackedWidget.setCurrentWidget(self.pageWizard)
            self.resize(600, 450)
        elif self.stackedWidget.currentWidget() == self.pageWizard:
            self._wizard.next()
        else:
            self.accept()

    def _wizardPageChanged(self):
        if not self._wizard.hasMore():
            self.btnNext.setVisible(False)
            self.btnFinish.setVisible(True)

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
        self.wdgBanner.setHidden(True)
        self.wdgTypesContainer.setHidden(True)
        self.setMaximumWidth(MAXIMUM_SIZE)
        self.wdgScrivenerImportDetails.setVisible(True)
        self.wdgScrivenerImportDetails.setNovel(self._scrivenerNovel)

    def __newNovel(self) -> Novel:
        return Novel.new_novel(self.lineTitle.text() if self.lineTitle.text() else 'My new novel')
