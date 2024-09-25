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
from typing import List, Optional

from PyQt6.QtCore import pyqtSignal, QSize, Qt, QTimer
from PyQt6.QtGui import QPixmap, QColor
from overrides import overrides
from qthandy import transparent, incr_font, italic, busy, retain_when_hidden, incr_icon
from qthandy.filter import VisibilityToggleEventFilter, InstantTooltipEventFilter, OpacityEventFilter
from qtmenu import MenuWidget

from plotlyst.common import NAV_BAR_BUTTON_DEFAULT_COLOR, \
    NAV_BAR_BUTTON_CHECKED_COLOR, RELAXED_WHITE_COLOR
from plotlyst.core.client import client
from plotlyst.core.domain import NovelDescriptor
from plotlyst.core.help import home_page_welcome_text
from plotlyst.event.core import emit_global_event, Event
from plotlyst.event.handler import global_event_dispatcher
from plotlyst.events import NovelDeletedEvent, NovelUpdatedEvent
from plotlyst.resources import resource_registry
from plotlyst.service.persistence import flush_or_fail
from plotlyst.service.tour import TourService
from plotlyst.view._view import AbstractView
from plotlyst.view.common import link_buttons_to_pages, ButtonPressResizeEventFilter, action, \
    TooltipPositionEventFilter, open_url, push_btn, wrap
from plotlyst.view.dialog.home import StoryCreationDialog
from plotlyst.view.generated.home_view_ui import Ui_HomeView
from plotlyst.view.icons import IconRegistry
from plotlyst.view.roadmap_view import RoadmapView
from plotlyst.view.style.base import apply_border_image
from plotlyst.view.style.button import apply_button_palette_color
from plotlyst.view.widget.confirm import confirmed
from plotlyst.view.widget.library import ShelvesTreeView
from plotlyst.view.widget.tour import Tutorial
from plotlyst.view.widget.tour.content import tutorial_titles, tutorial_descriptions
from plotlyst.view.widget.tour.core import LibraryTourEvent, NewStoryButtonTourEvent, \
    NewStoryDialogOpenTourEvent, TutorialNovelSelectTourEvent, NovelDisplayTourEvent, tutorial_novel, \
    NovelOpenButtonTourEvent, TutorialNovelCloseTourEvent
from plotlyst.view.widget.tree import TreeSettings
from plotlyst.view.widget.utility import IconSelectorButton


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
        self.ui.btnTwitter.setIcon(IconRegistry.from_name('fa5b.twitter', RELAXED_WHITE_COLOR))
        self.ui.btnInstagram.setIcon(IconRegistry.from_name('fa5b.instagram', RELAXED_WHITE_COLOR))
        self.ui.btnFacebook.setIcon(IconRegistry.from_name('fa5b.facebook', RELAXED_WHITE_COLOR))
        self.ui.btnYoutube.setIcon(IconRegistry.from_name('fa5b.youtube', RELAXED_WHITE_COLOR))
        self.ui.btnPinterest.setIcon(IconRegistry.from_name('fa5b.pinterest', RELAXED_WHITE_COLOR))
        self.ui.btnTwitter.installEventFilter(OpacityEventFilter(self.ui.btnTwitter, leaveOpacity=0.8))
        self.ui.btnInstagram.installEventFilter(OpacityEventFilter(self.ui.btnInstagram, leaveOpacity=0.8))
        self.ui.btnFacebook.installEventFilter(OpacityEventFilter(self.ui.btnFacebook, leaveOpacity=0.8))
        self.ui.btnYoutube.installEventFilter(OpacityEventFilter(self.ui.btnYoutube, leaveOpacity=0.8))
        self.ui.btnPinterest.installEventFilter(OpacityEventFilter(self.ui.btnPinterest, leaveOpacity=0.8))
        self.ui.btnTwitter.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnTwitter))
        self.ui.btnInstagram.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnInstagram))
        self.ui.btnFacebook.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnFacebook))
        self.ui.btnYoutube.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnYoutube))
        self.ui.btnPinterest.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnPinterest))
        self.ui.btnTwitter.clicked.connect(lambda: open_url('https://twitter.com/plotlyst'))
        self.ui.btnInstagram.clicked.connect(lambda: open_url('https://www.instagram.com/plotlyst'))
        self.ui.btnFacebook.clicked.connect(
            lambda: open_url('https://www.facebook.com/people/Plotlyst/61557773998679/'))
        self.ui.btnYoutube.clicked.connect(lambda: open_url('https://www.youtube.com/@Plotlyst'))
        self.ui.btnPinterest.clicked.connect(lambda: open_url('https://pinterest.com/Plotlyst'))

        apply_button_palette_color(self.ui.btnWebsite, RELAXED_WHITE_COLOR)
        italic(self.ui.btnWebsite)
        self.ui.btnWebsite.installEventFilter(OpacityEventFilter(self.ui.btnWebsite, leaveOpacity=0.8))
        self.ui.btnWebsite.clicked.connect(lambda: open_url('https://www.plotlyst.com'))

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

        self.ui.btnTutorials.setHidden(True)
        self.ui.btnProgress.setHidden(True)

        self.ui.lblWelcomeMain.setText(home_page_welcome_text)

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

        self._btnAddNew = push_btn(IconRegistry.plus_icon(RELAXED_WHITE_COLOR), tooltip='Add a new story',
                                   properties=['base', 'positive'])
        self._btnAddNew.clicked.connect(self._add_new_novel)
        self._shelvesTreeView = ShelvesTreeView(settings=TreeSettings(font_incr=2))
        self.ui.splitterLibrary.setSizes([150, 500])
        self.ui.wdgShelvesParent.layout().addWidget(wrap(self._btnAddNew, margin_left=10, margin_top=10),
                                                    alignment=Qt.AlignmentFlag.AlignLeft)
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

        self._roadmapView = RoadmapView()
        self.ui.pageRoadmap.layout().addWidget(self._roadmapView)

        # self._tutorialsTreeView = TutorialsTreeView(settings=TreeSettings(font_incr=2))
        # self._tutorialsTreeView.tutorialSelected.connect(self._tutorial_selected)
        # self.ui.splitterTutorials.setSizes([150, 500])
        # self.ui.btnStartTutorial.setIcon(IconRegistry.from_name('fa5s.play-circle', 'white'))
        # self.ui.btnStartTutorial.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnStartTutorial))
        # self.ui.btnStartTutorial.clicked.connect(self._start_tutorial)
        # self.ui.wdgTutorialsParent.layout().addWidget(self._tutorialsTreeView)
        # self.ui.stackTutorial.setCurrentWidget(self.ui.pageTutorialsEmpty)

        # self.ui.textTutorial.setViewportMargins(20, 20, 20, 20)
        # document: QTextDocument = self.ui.textTutorial.document()
        # font = self.ui.textTutorial.font()
        # font.setPointSize(font.pointSize() + 2)
        # document.setDefaultFont(font)
        #
        # transparent(self.ui.lineTutorialTitle)
        # self.ui.lineTutorialTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # incr_font(self.ui.lineTutorialTitle, 10)
        # bold(self.ui.lineTutorialTitle)

        self.ui.btnRoadmap.setChecked(True)
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
        title = f'Are you sure you want to delete the novel "{novel.title}"?'
        msg = '<html><ul><li>This action cannot be undone.</li><li>All characters and scenes will be lost.</li>'
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
