from typing import List, Optional

import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QToolButton, QMenu, QAction, QWidget, QApplication

from novel_outliner.common import EXIT_CODE_RESTART
from novel_outliner.core.domain import Character, Scene
from novel_outliner.core.persistence import emit_save
from novel_outliner.core.project import ProjectFinder
from novel_outliner.view.character_editor import CharacterEditor
from novel_outliner.view.characters_view import CharactersView
from novel_outliner.view.common import EditorCommand
from novel_outliner.view.generated.main_window_ui import Ui_MainWindow
from novel_outliner.view.icons import IconRegistry
from novel_outliner.view.scene_editor import SceneEditor
from novel_outliner.view.scenes_view import ScenesView


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.resize(1000, 630)
        self.setWindowState(Qt.WindowMaximized)
        self.setWindowTitle('Novel Outliner')
        self.setWindowIcon(IconRegistry.book_icon())

        self.project_finder = ProjectFinder()
        self.novel = self.project_finder.novel
        self.setWindowTitle(self.windowTitle() + f' - {self.novel.title}')

        self.characters_view = CharactersView(self.novel)
        self.characters_view.character_edited.connect(self._on_character_edition)
        self.characters_view.commands_sent.connect(self._on_received_commands)

        self.scenes_view = ScenesView(self.novel)
        self.scenes_view.scene_edited.connect(self._on_scene_edition)
        self.scenes_view.scene_created.connect(self._on_scene_creation)
        self.scenes_view.commands_sent.connect(self._on_received_commands)
        self._init_menuber()
        self._init_toolbar()

        self.tabWidget.addTab(self.characters_view.widget, IconRegistry.character_icon(), '')
        self.tabWidget.addTab(self.scenes_view.widget, IconRegistry.scene_icon(), '')
        self.tabWidget.setCurrentWidget(self.scenes_view.widget)

    def _init_menuber(self):
        self.actionRestart.setIcon(qtawesome.icon('mdi.restart'))
        self.actionRestart.triggered.connect(lambda: QApplication.instance().exit(EXIT_CODE_RESTART))

    def _init_toolbar(self):
        self.btnAdd = QToolButton(self.toolBar)
        self.btnAdd.setIcon(IconRegistry.plus_icon())
        self.btnAdd.setPopupMode(QToolButton.MenuButtonPopup)
        self.btnAdd.clicked.connect(self._on_add)
        menu = QMenu(self.btnAdd)
        char_action = QAction(IconRegistry.character_icon(), 'Character', menu)
        char_action.triggered.connect(self.btnAdd.click)
        location_action = QAction(IconRegistry.location_icon(), 'Location', menu)
        scene_action = QAction(IconRegistry.scene_icon(), 'Scene', menu)
        menu.addAction(char_action)
        menu.addAction(location_action)
        menu.addAction(scene_action)
        self.btnAdd.setPopupMode(QToolButton.MenuButtonPopup)
        self.btnAdd.setMenu(menu)
        self.toolBar.addWidget(self.btnAdd)

    def _on_add(self):
        self._on_character_edition(None)

    def _on_character_edition(self, character: Optional[Character]):
        self.editor = CharacterEditor(self.novel, character)
        self.editor.commands_sent.connect(self._on_received_commands)
        tab = self.tabWidget.addTab(self.editor.widget, 'New Character')
        self.tabWidget.setCurrentIndex(tab)

    def _on_scene_edition(self, scene: Optional[Scene]):
        self._on_scene_creation(scene)

    def _on_scene_creation(self, scene: Optional[Scene] = None):
        self.editor = SceneEditor(self.novel, scene)
        self.editor.commands_sent.connect(self._on_received_commands)
        tab = self.tabWidget.addTab(self.editor.widget, 'New Scene')
        self.tabWidget.setCurrentIndex(tab)

    def _on_received_commands(self, widget: QWidget, commands: List[EditorCommand]):
        for cmd in commands:
            if cmd == EditorCommand.SAVE:
                emit_save(self.novel)
            elif cmd == EditorCommand.CLOSE_CURRENT_EDITOR:
                index = self.tabWidget.indexOf(widget)
                self.tabWidget.removeTab(index)
            elif cmd == EditorCommand.DISPLAY_CHARACTERS:
                self.tabWidget.setCurrentWidget(self.characters_view.widget)
                self.characters_view.refresh()
            elif cmd == EditorCommand.DISPLAY_SCENES:
                self.tabWidget.setCurrentWidget(self.scenes_view.widget)
                self.scenes_view.refresh()
