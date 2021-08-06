"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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
from typing import List

import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QToolButton, QWidget, QApplication, QWidgetAction
from overrides import overrides

from src.main.python.plotlyst.common import EXIT_CODE_RESTART
from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import event_log_reporter, EventListener, Event, emit_event, event_sender
from src.main.python.plotlyst.event.handler import EventLogHandler, event_dispatcher
from src.main.python.plotlyst.events import NovelReloadRequestedEvent, NovelReloadedEvent, NovelDeletedEvent, \
    SceneChangedEvent, CharacterChangedEvent, NovelUpdatedEvent
from src.main.python.plotlyst.settings import settings
from src.main.python.plotlyst.view.characters_view import CharactersView
from src.main.python.plotlyst.view.common import EditorCommand, spacer_widget, EditorCommandType, busy
from src.main.python.plotlyst.view.dialog.about import AboutDialog
from src.main.python.plotlyst.view.generated.main_window_ui import Ui_MainWindow
from src.main.python.plotlyst.view.home_view import HomeView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.notes_view import NotesView
from src.main.python.plotlyst.view.novel_view import NovelView
from src.main.python.plotlyst.view.reports_view import ReportsView
from src.main.python.plotlyst.view.scenes_view import ScenesOutlineView
from src.main.python.plotlyst.view.tasks_view import TasksWidget
from src.main.python.plotlyst.view.timeline_view import TimelineView


class MainWindow(QMainWindow, Ui_MainWindow, EventListener):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.resize(1000, 630)
        if app_env.is_dev():
            self.resize(1200, 830)
        if app_env.is_prod():
            self.setWindowState(Qt.WindowMaximized)
        self.setWindowTitle('Plotlyst')
        self.novel = None
        last_novel_id = settings.last_novel_id()
        if last_novel_id is not None:
            has_novel = client.has_novel(last_novel_id)
            if has_novel:
                self.novel = client.fetch_novel(last_novel_id)
        if self.novel is None:
            _novels = client.novels()
            if _novels:
                self.novel = client.fetch_novel(_novels[0].id)

        self._init_menubar()
        self._init_toolbar()

        self._init_views()

        self.event_log_handler = EventLogHandler(self.statusBar())
        event_log_reporter.error.connect(self.event_log_handler.on_error_event)
        event_sender.send.connect(event_dispatcher.dispatch)
        self._register_events()

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, NovelReloadRequestedEvent):
            updated_novel = client.fetch_novel(self.novel.id)
            self.novel.update_from(updated_novel)
            emit_event(NovelReloadedEvent(self))
        elif isinstance(event, NovelDeletedEvent):
            if self.novel and event.novel.id == self.novel.id:
                self.novel = None
                self._clear_novel_views()
                for btn in self.buttonGroup.buttons():
                    if btn is not self.btnHome:
                        btn.setHidden(True)
        elif isinstance(event, NovelUpdatedEvent):
            if self.novel and event.novel.id == self.novel.id:
                self.novel.title = event.novel.title
        elif isinstance(event, CharacterChangedEvent):
            self.btnScenes.setEnabled(True)
            event_dispatcher.deregister(self, CharacterChangedEvent)
        elif isinstance(event, SceneChangedEvent):
            self.btnNotes.setEnabled(True)
            self.btnReport.setEnabled(True)
            self.btnTimeline.setEnabled(True)
            event_dispatcher.deregister(self, SceneChangedEvent)

    def _init_views(self):
        self.home_view = HomeView()
        self.btnHome.setIcon(IconRegistry.home_icon())
        self.pageHome.layout().addWidget(self.home_view.widget)
        self.home_view.loadNovel.connect(self._load_new_novel)

        self.buttonGroup.buttonToggled.connect(self._on_view_changed)
        self.btnHome.setChecked(True)

        if not self.novel:
            for btn in self.buttonGroup.buttons():
                if btn is not self.btnHome:
                    btn.setHidden(True)
            return

        for btn in self.buttonGroup.buttons():
            btn.setVisible(True)

        self.novel_view = NovelView(self.novel)
        self.characters_view = CharactersView(self.novel)
        self.scenes_outline_view = ScenesOutlineView(self.novel)
        self.scenes_outline_view.commands_sent.connect(self._on_received_commands)

        self.timeline_view = TimelineView(self.novel)
        self.notes_view = NotesView(self.novel)
        self.reports_view = ReportsView(self.novel)

        self.btnNovel.setIcon(IconRegistry.book_icon())
        self.btnCharacters.setIcon(IconRegistry.character_icon())
        self.btnScenes.setIcon(IconRegistry.scene_icon())
        self.btnTimeline.setIcon(IconRegistry.timeline_icon())
        self.btnNotes.setIcon(IconRegistry.notes_icon())
        self.btnReport.setIcon(IconRegistry.reports_icon())

        self.pageNovel.layout().addWidget(self.novel_view.widget)
        self.pageCharacters.layout().addWidget(self.characters_view.widget)
        self.pageScenes.layout().addWidget(self.scenes_outline_view.widget)
        self.pageTimeline.layout().addWidget(self.timeline_view.widget)
        self.pageNotes.layout().addWidget(self.notes_view.widget)
        self.pageReports.layout().addWidget(self.reports_view.widget)

        self.btnScenes.setEnabled(len(self.novel.characters) > 0 or len(self.novel.scenes) > 0)
        self.btnNotes.setEnabled(len(self.novel.scenes) > 0)
        self.btnReport.setEnabled(len(self.novel.scenes) > 0)
        self.btnTimeline.setEnabled(len(self.novel.scenes) > 0)
        if self.novel.scenes:
            self.btnScenes.setChecked(True)
        else:
            self.btnCharacters.setChecked(True)

    def _on_view_changed(self):
        if self.btnHome.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageHome)
            self.home_view.activate()
        elif self.btnNovel.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageNovel)
            self.novel_view.activate()
        elif self.btnCharacters.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageCharacters)
            self.characters_view.activate()
        elif self.btnScenes.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageScenes)
            self.scenes_outline_view.activate()
        elif self.btnTimeline.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageTimeline)
            self.timeline_view.activate()
        elif self.btnNotes.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageNotes)
            self.notes_view.activate()
        elif self.btnReport.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageReports)
            self.reports_view.activate()

    def _init_menubar(self):
        if app_env.is_prod():
            self.menuFile.removeAction(self.actionRestart)
        else:
            self.actionRestart.setIcon(qtawesome.icon('mdi.restart'))
            self.actionRestart.triggered.connect(lambda: QApplication.instance().exit(EXIT_CODE_RESTART))

        self.actionImportScrivener.triggered.connect(self._import_from_scrivener)
        self.actionAbout.triggered.connect(lambda: AboutDialog().exec())
        self.actionIncreaseFontSize.triggered.connect(self._increase_font_size)
        self.actionDecreaseFontSize.triggered.connect(self.decrease_font_size)

    def _init_toolbar(self):
        tasks_button = QToolButton(self.toolBar)
        tasks_button.setPopupMode(QToolButton.InstantPopup)
        tasks_button.setIcon(IconRegistry.tasks_icon())
        tasks_button.setToolTip('Tasks')
        tasks_action = QWidgetAction(tasks_button)
        self._distribution_widget = TasksWidget(self.novel)
        self._distribution_widget.setMinimumWidth(700)
        self._distribution_widget.setMinimumHeight(400)
        tasks_action.setDefaultWidget(self._distribution_widget)
        tasks_button.addAction(tasks_action)
        self.toolBar.addWidget(spacer_widget(5))
        self.toolBar.addWidget(tasks_button)
        self.toolBar.addWidget(spacer_widget())

    def _import_from_scrivener(self):
        self.btnHome.click()
        self.home_view.import_from_scrivener()

    def _increase_font_size(self):
        current_font = QApplication.font()
        self._set_font_size(current_font.pointSize() + 1)

    def decrease_font_size(self):
        current_font = QApplication.font()
        self._set_font_size(current_font.pointSize() - 1)

    def _set_font_size(self, value: int):
        current_font = QApplication.font()
        current_font.setPointSizeF(value)
        QApplication.instance().setFont(current_font)

        for widget in QApplication.allWidgets():
            if widget is self.menubar:
                continue
            font = widget.font()
            font.setPointSizeF(value)
            widget.setFont(font)

    @busy
    def _load_new_novel(self, novel: Novel):
        if self.novel and self.novel.id == novel.id:
            return

        event_dispatcher.clear()
        self.pageHome.layout().removeWidget(self.home_view.widget)
        self.home_view.widget.deleteLater()
        if self.novel:
            self._clear_novel_views()

        self.novel = client.fetch_novel(novel.id)
        self._init_views()
        settings.set_last_novel_id(self.novel.id)
        self._register_events()

    def _register_events(self):
        event_dispatcher.register(self, NovelReloadRequestedEvent)
        event_dispatcher.register(self, NovelDeletedEvent)
        event_dispatcher.register(self, NovelUpdatedEvent)
        if self.novel and not self.novel.scenes:
            event_dispatcher.register(self, SceneChangedEvent)
        if self.novel and not self.novel.characters:
            event_dispatcher.register(self, CharacterChangedEvent)

    def _clear_novel_views(self):
        self.pageNovel.layout().removeWidget(self.novel_view.widget)
        self.novel_view.widget.deleteLater()
        self.pageCharacters.layout().removeWidget(self.characters_view.widget)
        self.characters_view.widget.deleteLater()
        self.pageScenes.layout().removeWidget(self.scenes_outline_view.widget)
        self.scenes_outline_view.widget.deleteLater()
        self.pageTimeline.layout().removeWidget(self.timeline_view.widget)
        self.timeline_view.widget.deleteLater()
        self.pageNotes.layout().removeWidget(self.notes_view.widget)
        self.notes_view.widget.deleteLater()
        self.pageReports.layout().removeWidget(self.reports_view.widget)
        self.reports_view.widget.deleteLater()

    def _on_received_commands(self, widget: QWidget, commands: List[EditorCommand]):
        for cmd in commands:
            if cmd.type == EditorCommandType.UPDATE_SCENE_SEQUENCES:
                for index, scene in enumerate(self.novel.scenes):
                    scene.sequence = index
                client.update_novel(self.novel)
