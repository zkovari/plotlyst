import typing
from typing import List, Optional

import qtawesome
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QMainWindow, QToolButton, QWidget, QApplication, QTabWidget, QWidgetAction, QProxyStyle, \
    QStyle, QStyleOption, QTabBar, QStyleOptionTab
from overrides import overrides

from novel_outliner.common import EXIT_CODE_RESTART
from novel_outliner.core.client import client
from novel_outliner.core.domain import Character, Scene
from novel_outliner.core.persistence import emit_save
from novel_outliner.core.project import ProjectFinder
from novel_outliner.event.core import event_log_reporter
from novel_outliner.event.handler import EventAuthorizationHandler, EventLogHandler
from novel_outliner.view.character_editor import CharacterEditor
from novel_outliner.view.characters_view import CharactersView
from novel_outliner.view.common import EditorCommand, spacer_widget, EditorCommandType
from novel_outliner.view.generated.main_window_ui import Ui_MainWindow
from novel_outliner.view.icons import IconRegistry
from novel_outliner.view.notes_view import NotesView
from novel_outliner.view.novel_view import NovelView
from novel_outliner.view.reports_view import ReportsView
from novel_outliner.view.scene_editor import SceneEditor
from novel_outliner.view.scenes_view import ScenesOutlineView, DraftScenesView
from novel_outliner.view.tasks_view import TasksWidget
from novel_outliner.view.timeline_view import TimelineView


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.resize(1000, 630)
        self.setWindowState(Qt.WindowMaximized)
        self.setWindowTitle('Plotlyst')
        self.setWindowIcon(IconRegistry.book_icon())

        self.project_finder = ProjectFinder()
        self.novel = self.project_finder.novel

        self.novel_view = NovelView(self.novel)

        self.characters_view = CharactersView(self.novel)
        self.characters_view.character_edited.connect(self._on_character_edition)
        self.characters_view.character_created.connect(self._on_character_creation)
        self.characters_view.commands_sent.connect(self._on_received_commands)

        self.scenes_outline_view = ScenesOutlineView(self.novel)
        self.scenes_outline_view.scene_edited.connect(self._on_scene_edition)
        self.scenes_outline_view.scene_created.connect(self._on_scene_creation)
        self.scenes_outline_view.commands_sent.connect(self._on_received_commands)

        self.timeline_view = TimelineView(self.novel)
        self.notes_view = NotesView(self.novel)
        self.reports_view = ReportsView(self.novel)
        self.draft_scenes_view = DraftScenesView(self.novel)
        self._init_menuber()
        self._init_toolbar()

        self._tabstyle = TabStyle()
        self.tabWidget.tabBar().setStyle(self._tabstyle)
        self.tabWidget.addTab(self.novel_view.widget, IconRegistry.book_icon(), '')
        self.tabWidget.addTab(self.characters_view.widget, IconRegistry.character_icon(), '')
        self.scenes_tab = QTabWidget()
        self.scenes_tab.addTab(self.scenes_outline_view.widget, 'Outline')
        self.scenes_tab.addTab(self.draft_scenes_view.widget, 'Draft')
        self.tabWidget.addTab(self.scenes_tab, IconRegistry.scene_icon(), '')
        self.tabWidget.addTab(self.timeline_view.widget, IconRegistry.timeline_icon(), '')
        self.tabWidget.addTab(self.notes_view.widget, IconRegistry.notes_icon(), '')
        self.tabWidget.addTab(self.reports_view.widget, IconRegistry.reports_icon(), '')
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.characters_view.widget), 'Characters')
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.scenes_tab), 'Scenes')
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.timeline_view.widget), 'Timeline & events')
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.notes_view.widget), 'Notes')
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.reports_view.widget), 'Reports')
        self.tabWidget.setCurrentWidget(self.scenes_tab)

        self.tabWidget.currentChanged.connect(self._on_current_tab_changed)

        EventAuthorizationHandler.parent = self
        self.event_log_handler = EventLogHandler(self.statusBar())
        event_log_reporter.info.connect(self.event_log_handler.on_info_event)
        event_log_reporter.warning.connect(self.event_log_handler.on_warning_event)
        event_log_reporter.error.connect(self.event_log_handler.on_error_event)

    def _init_menuber(self):
        self.actionRestart.setIcon(qtawesome.icon('mdi.restart'))
        self.actionRestart.triggered.connect(lambda: QApplication.instance().exit(EXIT_CODE_RESTART))

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

    def _on_add(self):
        self._on_character_edition(None)

    def _on_character_edition(self, character: Optional[Character]):
        self.editor = CharacterEditor(self.novel, character)
        self.editor.commands_sent.connect(self._on_received_commands)
        tab = self.tabWidget.addTab(self.editor.widget, 'New Character')
        self.tabWidget.setCurrentIndex(tab)

    def _on_character_creation(self):
        self._on_character_edition(None)

    def _on_current_tab_changed(self, index: int):
        pass

    def _on_scene_edition(self, scene: Optional[Scene]):
        self._on_scene_creation(scene)

    def _on_scene_creation(self, scene: Optional[Scene] = None):
        self.editor = SceneEditor(self.novel, scene)
        self.editor.commands_sent.connect(self._on_received_commands)
        tab = self.tabWidget.addTab(self.editor.widget, 'Edit Scene' if scene else 'New Scene')
        self.tabWidget.setCurrentIndex(tab)

    def _on_received_commands(self, widget: QWidget, commands: List[EditorCommand]):
        for cmd in commands:
            if cmd.type == EditorCommandType.SAVE:
                emit_save(self.novel)
            elif cmd.type == EditorCommandType.CLOSE_CURRENT_EDITOR:
                index = self.tabWidget.indexOf(widget)
                self.tabWidget.removeTab(index)
            elif cmd.type == EditorCommandType.DISPLAY_CHARACTERS:
                self.tabWidget.setCurrentWidget(self.characters_view.widget)
                self.characters_view.refresh()
            elif cmd.type == EditorCommandType.DISPLAY_SCENES:
                self.tabWidget.setCurrentWidget(self.scenes_tab)
                self.scenes_outline_view.refresh()
            elif cmd.type == EditorCommandType.EDIT_SCENE:
                if cmd.value is not None and cmd.value < len(self.novel.scenes):
                    self._on_scene_edition(self.novel.scenes[cmd.value])
            elif cmd.type == EditorCommandType.UPDATE_SCENE_SEQUENCES:
                for index, scene in enumerate(self.novel.scenes):
                    scene.sequence = index
                client.update_scene_sequences(self.novel)


class TabStyle(QProxyStyle):
    @overrides
    def sizeFromContents(self, type: QStyle.ContentsType, option: QStyleOption, size: QtCore.QSize,
                         widget: QWidget) -> QtCore.QSize:
        size: QSize = super(TabStyle, self).sizeFromContents(type, option, size, widget)
        if type == QStyle.CT_TabBarTab:
            size.transpose()
        return size

    @overrides
    def drawControl(self, element: QStyle.ControlElement, option: QStyleOption, painter: QtGui.QPainter,
                    widget: typing.Optional[QWidget] = ...) -> None:
        if element == QStyle.CE_TabBarTabLabel:
            opt = QStyleOptionTab(option)
            opt.shape = QTabBar.RoundedNorth
            super(TabStyle, self).drawControl(element, opt, painter, widget)
            return
        super(TabStyle, self).drawControl(element, option, painter, widget)
