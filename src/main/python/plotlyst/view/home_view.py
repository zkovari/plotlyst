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

from PyQt6.QtCore import pyqtSignal, QSize, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMenu
from overrides import overrides
from qthandy import ask_confirmation, transparent, incr_font, hbox, btn_popup_menu

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import NovelDescriptor
from src.main.python.plotlyst.event.core import emit_event, Event
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import NovelDeletedEvent, NovelUpdatedEvent
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.view._view import AbstractView
from src.main.python.plotlyst.view.common import link_buttons_to_pages
from src.main.python.plotlyst.view.dialog.home import StoryCreationDialog
from src.main.python.plotlyst.view.generated.home_view_ui import Ui_HomeView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.library import ShelvesTreeView


class HomeView(AbstractView):
    loadNovel = pyqtSignal(NovelDescriptor)

    def __init__(self):
        super(HomeView, self).__init__()
        self.ui = Ui_HomeView()
        self.ui.setupUi(self.widget)
        self._selected_novel: Optional[NovelDescriptor] = None
        self._novels: List[NovelDescriptor] = []

        self.ui.lblBanner.setPixmap(QPixmap(resource_registry.banner))
        self.ui.btnTwitter.setIcon(IconRegistry.from_name('fa5b.twitter', 'white'))
        self.ui.btnInstagram.setIcon(IconRegistry.from_name('fa5b.instagram', 'white'))
        self.ui.btnFacebook.setIcon(IconRegistry.from_name('fa5b.facebook', 'white'))
        transparent(self.ui.btnTwitter)
        transparent(self.ui.btnInstagram)
        transparent(self.ui.btnFacebook)

        self.ui.btnLibrary.setIcon(IconRegistry.from_name('mdi.bookshelf', color_on='darkBlue'))
        self.ui.btnProgress.setIcon(IconRegistry.from_name('fa5s.chart-line'))
        self.ui.btnRoadmap.setIcon(IconRegistry.from_name('fa5s.road'))

        self.ui.btnActivate.setIcon(IconRegistry.book_icon(color='white', color_on='white'))
        self.ui.btnActivate.clicked.connect(lambda: self.loadNovel.emit(self._selected_novel))
        self.ui.btnAddNewStoryMain.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnAddNewStoryMain.clicked.connect(self._add_new_novel)

        transparent(self.ui.lineNovelTitle)
        self.ui.lineNovelTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        incr_font(self.ui.lineNovelTitle, 10)
        self.ui.lineNovelTitle.textEdited.connect(self._on_edit_title)
        self.ui.btnNovelSettings.setIcon(IconRegistry.dots_icon(vertical=True))
        menu = QMenu(self.ui.btnNovelSettings)
        menu.addAction(IconRegistry.trash_can_icon(), 'Delete', self._on_delete)
        btn_popup_menu(self.ui.btnNovelSettings, menu)

        self._shelvesTreeView = ShelvesTreeView()
        hbox(self.ui.wdgShelvesParent)
        self.ui.splitterLibrary.setSizes([100, 500])
        self.ui.wdgShelvesParent.layout().addWidget(self._shelvesTreeView)
        self._shelvesTreeView.novelSelected.connect(self._novel_selected)
        self._shelvesTreeView.novelsShelveSelected.connect(self.reset)

        incr_font(self.ui.btnAddNewStoryMain, 8)
        self.ui.btnAddNewStoryMain.setIconSize(QSize(24, 24))

        link_buttons_to_pages(self.ui.stackedWidget,
                              [(self.ui.btnLibrary, self.ui.pageLibrary), (self.ui.btnProgress, self.ui.pageProgress),
                               (self.ui.btnRoadmap, self.ui.pageRoadmap)])

        self.ui.btnLibrary.setChecked(True)
        self.ui.stackWdgNovels.setCurrentWidget(self.ui.pageEmpty)

        self._novels = client.novels()
        self.refresh()

        event_dispatcher.register(self, NovelUpdatedEvent)

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

    def _add_new_novel(self):
        novel = StoryCreationDialog(self.widget).display()
        if novel:
            self.repo.insert_novel(novel)
            self._novels.append(novel)
            for character in novel.characters:
                self.repo.insert_character(novel, character)
            for scene in novel.scenes:
                self.repo.insert_scene(novel, scene)
                if scene.manuscript:
                    self.repo.update_doc(novel, scene.manuscript)

            self.refresh()

    def _on_edit_title(self, title: str):
        if title:
            self._selected_novel.title = title
            self.repo.update_project_novel(self._selected_novel)
            self._shelvesTreeView.updateNovel(self._selected_novel)
            emit_event(NovelUpdatedEvent(self, self._selected_novel))

    def _on_delete(self):
        if ask_confirmation(f'Are you sure you want to delete the novel "{self._selected_novel.title}"?'):
            self.repo.delete_novel(self._selected_novel)
            self._novels.remove(self._selected_novel)
            emit_event(NovelDeletedEvent(self, self._selected_novel))
            self._selected_novel = None
            self.reset()
            self.refresh()
