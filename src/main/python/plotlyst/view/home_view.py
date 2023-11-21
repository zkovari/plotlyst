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
from typing import List, Optional

from PyQt6.QtCore import pyqtSignal, QSize, Qt, QTimer
from PyQt6.QtGui import QPixmap, QColor, QTextDocument
from overrides import overrides
from qthandy import transparent, incr_font, italic, busy, retain_when_hidden, incr_icon, bold, underline
from qthandy.filter import VisibilityToggleEventFilter, InstantTooltipEventFilter, OpacityEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import NAV_BAR_BUTTON_DEFAULT_COLOR, \
    NAV_BAR_BUTTON_CHECKED_COLOR
from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import NovelDescriptor
from src.main.python.plotlyst.core.help import home_page_welcome_text
from src.main.python.plotlyst.event.core import emit_global_event, Event
from src.main.python.plotlyst.event.handler import global_event_dispatcher
from src.main.python.plotlyst.events import NovelDeletedEvent, NovelUpdatedEvent
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.service.persistence import flush_or_fail
from src.main.python.plotlyst.service.tour import TourService
from src.main.python.plotlyst.view._view import AbstractView
from src.main.python.plotlyst.view.common import link_buttons_to_pages, ButtonPressResizeEventFilter, action, \
    TooltipPositionEventFilter
from src.main.python.plotlyst.view.dialog.home import StoryCreationDialog
from src.main.python.plotlyst.view.generated.home_view_ui import Ui_HomeView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.style.base import apply_border_image
from src.main.python.plotlyst.view.widget.confirm import confirmed
from src.main.python.plotlyst.view.widget.library import ShelvesTreeView
from src.main.python.plotlyst.view.widget.tour import TutorialsTreeView, Tutorial
from src.main.python.plotlyst.view.widget.tour.content import tutorial_titles, tutorial_descriptions
from src.main.python.plotlyst.view.widget.tour.core import LibraryTourEvent, NewStoryButtonTourEvent, \
    NewStoryDialogOpenTourEvent, TutorialNovelSelectTourEvent, NovelDisplayTourEvent, tutorial_novel, \
    NovelOpenButtonTourEvent, TutorialNovelCloseTourEvent
from src.main.python.plotlyst.view.widget.tree import TreeSettings
from src.main.python.plotlyst.view.widget.utility import IconSelectorButton


class HomeView(AbstractView):
    loadNovel = pyqtSignal(NovelDescriptor)

    def __init__(self):
        super(HomeView, self).__init__(
            [LibraryTourEvent, NewStoryButtonTourEvent, NewStoryDialogOpenTourEvent, TutorialNovelSelectTourEvent,
             NovelDisplayTourEvent, NovelOpenButtonTourEvent, TutorialNovelCloseTourEvent])
        self.ui = Ui_HomeView()
        self.ui.setupUi(self.widget)
        self._selected_novel: Optional[NovelDescriptor] = None
        self._novels: List[NovelDescriptor] = []
        self._tour_service = TourService.instance()

        self.ui.lblBanner.setPixmap(QPixmap(resource_registry.banner))
        self.ui.btnTwitter.setIcon(IconRegistry.from_name('fa5b.twitter', 'white'))
        self.ui.btnInstagram.setIcon(IconRegistry.from_name('fa5b.instagram', 'white'))
        self.ui.btnFacebook.setIcon(IconRegistry.from_name('fa5b.facebook', 'white'))
        transparent(self.ui.btnTwitter)
        transparent(self.ui.btnInstagram)
        transparent(self.ui.btnFacebook)

        self.ui.btnLibrary.setIcon(
            IconRegistry.from_name('mdi.bookshelf', NAV_BAR_BUTTON_DEFAULT_COLOR, NAV_BAR_BUTTON_CHECKED_COLOR))
        self.ui.btnTutorials.setIcon(
            IconRegistry.from_name('mdi6.school-outline', NAV_BAR_BUTTON_DEFAULT_COLOR, NAV_BAR_BUTTON_CHECKED_COLOR))
        self.ui.btnProgress.setIcon(
            IconRegistry.from_name('fa5s.chart-line', NAV_BAR_BUTTON_DEFAULT_COLOR, NAV_BAR_BUTTON_CHECKED_COLOR))
        self.ui.btnRoadmap.setIcon(
            IconRegistry.from_name('fa5s.road', NAV_BAR_BUTTON_DEFAULT_COLOR, NAV_BAR_BUTTON_CHECKED_COLOR))

        for btn in self.ui.buttonGroup.buttons():
            btn.installEventFilter(OpacityEventFilter(btn, leaveOpacity=0.7, ignoreCheckedButton=True))
            btn.installEventFilter(TooltipPositionEventFilter(btn))

        self.ui.btnProgress.setHidden(True)
        self.ui.btnRoadmap.setHidden(True)

        self.ui.lblWelcomeMain.setText(home_page_welcome_text)
        self.ui.btnVisitTutorials.setIcon(IconRegistry.from_name('mdi6.school-outline', NAV_BAR_BUTTON_DEFAULT_COLOR))
        transparent(self.ui.btnVisitTutorials)
        underline(self.ui.btnVisitTutorials)
        self.ui.btnVisitTutorials.installEventFilter(OpacityEventFilter(self.ui.btnVisitTutorials, leaveOpacity=0.5))
        self.ui.btnVisitTutorials.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnVisitTutorials))

        self.ui.btnFirstStory.setIcon(IconRegistry.book_icon())
        self.ui.btnFirstStory.installEventFilter(OpacityEventFilter(self.ui.btnFirstStory, leaveOpacity=0.7))
        self.ui.btnFirstStory.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnFirstStory))

        self.ui.btnActivate.setIcon(IconRegistry.book_icon(color='white', color_on='white'))
        self.ui.btnActivate.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnActivate))
        self.ui.btnActivate.setIconSize(QSize(28, 28))
        self.ui.btnActivate.clicked.connect(lambda: self.loadNovel.emit(self._selected_novel))
        self.ui.btnAddNewStoryMain.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnAddNewStoryMain.clicked.connect(self._add_new_novel)
        self.ui.btnAddNewStoryMain.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnAddNewStoryMain))

        self.ui.iconImportOrigin.setIcon(IconRegistry.from_name('mdi.alpha-s-circle-outline', color='#410253'))
        self.ui.iconImportOrigin.setToolTip('Synced from Scrivener')
        self.ui.iconImportOrigin.installEventFilter(InstantTooltipEventFilter(self.ui.iconImportOrigin))
        incr_icon(self.ui.iconImportOrigin, 8)

        self.ui.wdgTitle.setFixedHeight(150)
        apply_border_image(self.ui.wdgTitle, resource_registry.frame1)

        transparent(self.ui.lineNovelTitle)
        self.ui.lineNovelTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        incr_font(self.ui.lineNovelTitle, 10)
        self.ui.lineNovelTitle.textEdited.connect(self._title_edited)
        self.ui.btnNovelSettings.setIcon(IconRegistry.dots_icon(vertical=True))
        retain_when_hidden(self.ui.btnNovelSettings)
        self.ui.btnNovelSettings.setHidden(True)

        transparent(self.ui.lineSubtitle)
        italic(self.ui.lineSubtitle)
        incr_font(self.ui.lineSubtitle, 2)
        transparent(self.ui.iconSubtitle)
        self.ui.lineSubtitle.textEdited.connect(self._subtitle_edited)
        self.ui.iconSubtitle.setIcon(IconRegistry.from_name('mdi.send'))
        self._iconSelector = IconSelectorButton()
        self._iconSelector.iconSelected.connect(self._icon_changed)
        self.ui.wdgSubtitleParent.layout().insertWidget(0, self._iconSelector)

        menu = MenuWidget(self.ui.btnNovelSettings)
        menu.addAction(action('Delete', IconRegistry.trash_can_icon(), lambda: self._on_delete()))

        self._shelvesTreeView = ShelvesTreeView(settings=TreeSettings(font_incr=1))
        self.ui.splitterLibrary.setSizes([150, 500])
        self.ui.wdgShelvesParent.layout().addWidget(self._shelvesTreeView)
        self._shelvesTreeView.novelSelected.connect(self._novel_selected)
        self._shelvesTreeView.novelChanged.connect(self._novel_changed_in_browser)
        self._shelvesTreeView.novelsShelveSelected.connect(self.reset)
        self._shelvesTreeView.newNovelRequested.connect(self._add_new_novel)
        self._shelvesTreeView.novelDeletionRequested.connect(self._on_delete)

        self.ui.pageNovelDisplay.installEventFilter(
            VisibilityToggleEventFilter(self.ui.btnNovelSettings, self.ui.pageNovelDisplay))

        self.ui.btnAddNewStoryMain.setIconSize(QSize(24, 24))

        link_buttons_to_pages(self.ui.stackedWidget,
                              [(self.ui.btnLibrary, self.ui.pageLibrary), (self.ui.btnTutorials, self.ui.pageTutorials),
                               (self.ui.btnProgress, self.ui.pageProgress),
                               (self.ui.btnRoadmap, self.ui.pageRoadmap)])

        self._tutorialsTreeView = TutorialsTreeView(settings=TreeSettings(font_incr=2))
        self._tutorialsTreeView.tutorialSelected.connect(self._tutorial_selected)
        self.ui.splitterTutorials.setSizes([150, 500])
        self.ui.btnStartTutorial.setIcon(IconRegistry.from_name('fa5s.play-circle', 'white'))
        self.ui.btnStartTutorial.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnStartTutorial))
        self.ui.btnStartTutorial.clicked.connect(self._start_tutorial)
        self.ui.wdgTutorialsParent.layout().addWidget(self._tutorialsTreeView)
        self.ui.stackTutorial.setCurrentWidget(self.ui.pageTutorialsEmpty)

        self.ui.textTutorial.setViewportMargins(20, 20, 20, 20)
        document: QTextDocument = self.ui.textTutorial.document()
        font = self.ui.textTutorial.font()
        font.setPointSize(font.pointSize() + 2)
        document.setDefaultFont(font)

        transparent(self.ui.lineTutorialTitle)
        self.ui.lineTutorialTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        incr_font(self.ui.lineTutorialTitle, 10)
        bold(self.ui.lineTutorialTitle)

        self.ui.btnLibrary.setChecked(True)
        self.ui.stackWdgNovels.setCurrentWidget(self.ui.pageEmpty)

        self._novels = client.novels()
        self.refresh()

        global_event_dispatcher.register(self, NovelUpdatedEvent)

    def novels(self) -> List[NovelDescriptor]:
        return self._novels

    def shelves(self) -> ShelvesTreeView:
        return self._shelvesTreeView

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, NovelUpdatedEvent):
            for novel in self._novels:
                if novel.id == event.novel.id:
                    novel.title = event.novel.title
            if self._selected_novel and self._selected_novel.id == event.novel.id:
                self.ui.lineNovelTitle.setText(self._selected_novel.title)
            self.refresh()
        elif isinstance(event, LibraryTourEvent):
            self._tour_service.addWidget(self.ui.btnLibrary, event)
        elif isinstance(event, NewStoryButtonTourEvent):
            self.ui.stackWdgNovels.setCurrentWidget(self.ui.pageEmpty)
            self._tour_service.addWidget(self.ui.btnAddNewStoryMain, event)
        elif isinstance(event, NewStoryDialogOpenTourEvent):
            dialog = StoryCreationDialog(self.widget.window())
            dialog.show()
            QTimer.singleShot(100, self._tour_service.next)
        elif isinstance(event, TutorialNovelSelectTourEvent):
            self._novel_selected(tutorial_novel)
            self._tour_service.next()
        elif isinstance(event, NovelDisplayTourEvent):
            self._tour_service.addWidget(self.ui.pageNovelDisplay, event)
        elif isinstance(event, NovelOpenButtonTourEvent):
            self._tour_service.addWidget(self.ui.btnActivate, event)
        elif isinstance(event, TutorialNovelCloseTourEvent):
            self.ui.stackWdgNovels.setCurrentWidget(self.ui.pageEmpty)
        else:
            super(HomeView, self).event_received(event)

    def reset(self):
        self._selected_novel = None
        self.ui.stackWdgNovels.setCurrentWidget(self.ui.pageEmpty)
        self._shelvesTreeView.clearSelection()

    @overrides
    def refresh(self):
        self._shelvesTreeView.setNovels(self._novels)

    def _novel_selected(self, novel: NovelDescriptor):
        self._selected_novel = novel

        self.ui.stackWdgNovels.setCurrentWidget(self.ui.pageNovelDisplay)

        self.ui.lineNovelTitle.setText(novel.title)
        self.ui.lineSubtitle.setText(novel.subtitle)
        if novel.icon:
            self._iconSelector.selectIcon(novel.icon, novel.icon_color)
        else:
            self._iconSelector.reset()

        self.ui.iconImportOrigin.setVisible(novel.is_scrivener_sync())

    def _add_new_novel(self):
        @busy
        def flush():
            flush_or_fail()

        novel = StoryCreationDialog(self.widget).display()
        if novel:
            self.repo.insert_novel(novel)
            self._novels.append(novel)
            flush()
            for character in novel.characters:
                self.repo.insert_character(novel, character)
            for scene in novel.scenes:
                self.repo.insert_scene(novel, scene)
                if scene.manuscript:
                    self.repo.update_doc(novel, scene.manuscript)

            flush()

            self.refresh()
            self._shelvesTreeView.selectNovel(novel)

    def _title_edited(self, title: str):
        if title:
            self._selected_novel.title = title
            self._shelvesTreeView.updateNovel(self._selected_novel)
            self.repo.update_project_novel(self._selected_novel)
            emit_global_event(NovelUpdatedEvent(self, self._selected_novel))

    def _subtitle_edited(self, subtitle: str):
        self._selected_novel.subtitle = subtitle
        self.repo.update_project_novel(self._selected_novel)

    def _icon_changed(self, icon: str, color: QColor):
        self._selected_novel.icon = icon
        self._selected_novel.icon_color = color.name()
        self._shelvesTreeView.updateNovel(self._selected_novel)
        self.repo.update_project_novel(self._selected_novel)

    def _novel_changed_in_browser(self, novel: NovelDescriptor):
        if self._selected_novel and self._selected_novel.id == novel.id:
            self.ui.lineNovelTitle.setText(self._selected_novel.title)
            if novel.icon:
                self._iconSelector.selectIcon(novel.icon, novel.icon_color)
            else:
                self._iconSelector.reset()
        self.repo.update_project_novel(novel)

    def _on_delete(self, novel: Optional[NovelDescriptor] = None):
        if novel is None:
            novel = self._selected_novel
        title = f'Delete the novel "{novel.title}"?'
        msg = '<html>This cannot be undone.<br>All characters and scenes will be lost.'
        if confirmed(msg, title):
            self.repo.delete_novel(novel)
            self._novels.remove(novel)
            emit_global_event(NovelDeletedEvent(self, novel))
            if self._selected_novel and novel.id == self._selected_novel.id:
                self._selected_novel = None
                self.reset()
            self.refresh()

    def _tutorial_selected(self, tutorial: Tutorial):
        if tutorial.is_container():
            self.ui.stackTutorial.setCurrentWidget(self.ui.pageTutorialsEmpty)
        else:
            self._tour_service.setTutorial(tutorial)
            self.ui.stackTutorial.setCurrentWidget(self.ui.pageTutorialDisplay)
            self.ui.lineTutorialTitle.setText(tutorial_titles[tutorial])
            self.ui.textTutorial.setMarkdown(tutorial_descriptions.get(tutorial, 'Click Start to learn this tutorial.'))

    def _start_tutorial(self):
        self._tour_service.start()
