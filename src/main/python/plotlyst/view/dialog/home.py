"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFileDialog
from qthandy import incr_font

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.core.scrivener import ScrivenerImporter
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import emit_critical
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.view.common import link_buttons_to_pages, DisabledClickEventFilter, link_editor_to_btn, \
    OpacityEventFilter
from src.main.python.plotlyst.view.generated.story_creation_dialog_ui import Ui_StoryCreationDialog
from src.main.python.plotlyst.view.icons import IconRegistry


class StoryCreationDialog(QDialog, Ui_StoryCreationDialog):
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
        self.btnLoadScrivener.clicked.connect(self._loadFromScrivener)
        incr_font(self.btnNewStory)
        incr_font(self.btnScrivener)

        self.btnSaveNewStory = self.btnBoxStoryCreation.button(QDialogButtonBox.Ok)
        self.btnSaveNewStory.setDisabled(True)
        self.btnSaveNewStory.installEventFilter(
            DisabledClickEventFilter(lambda: qtanim.shake(self.lineTitle), self.btnSaveNewStory))
        link_editor_to_btn(self.lineTitle, self.btnSaveNewStory)

        self.btnSaveScrivener = self.btnBoxScrivener.button(QDialogButtonBox.Ok)
        self.btnSaveScrivener.setDisabled(True)
        self.btnSaveScrivener.installEventFilter(
            DisabledClickEventFilter(lambda: qtanim.shake(self.btnLoadScrivener), self.btnSaveScrivener))
        for btn in [self.btnNewStory, self.btnScrivener]:
            btn.setStyleSheet('''
            QPushButton {
                border: 0px;
                padding: 3px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 0,
                                          stop: 0 #d7e3fc);
                border: 1px hidden black;
            }
            QPushButton:checked {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 0,
                                      stop: 0 #4e4187);
                border: 2px solid black;
                color: white;
            }
            ''')
            btn.installEventFilter(OpacityEventFilter(parent=btn, ignoreCheckedButton=True))
        self.stackedWidget.currentChanged.connect(self._pageChanged)

    def display(self) -> Optional[Novel]:
        result = self.exec()
        if result == QDialog.Rejected:
            return None

        if self.stackedWidget.currentWidget() == self.pageNewStory:
            return Novel(title=self.lineTitle.text())
        elif self.stackedWidget.currentWidget() == self.pageScrivener:
            return self._scrivenerNovel

        return None

    def _pageChanged(self):
        if self.stackedWidget.currentWidget() == self.pageNewStory:
            self.lineTitle.setFocus()

    def _loadFromScrivener(self):
        if app_env.is_dev():
            default_path = 'resources/scrivener/v3/'
        else:
            default_path = None
        if app_env.is_mac():
            project = QFileDialog.getOpenFileName(self, 'Choose a Scrivener project directory', default_path)
        else:
            project = QFileDialog.getExistingDirectory(self, 'Choose a Scrivener project directory', default_path)
        if not project:
            return
        importer = ScrivenerImporter()
        novel: Novel = importer.import_project(project)
        if client.has_novel(novel.id):
            return emit_critical('Cannot import Scrivener project again because it is already present in Plotlyst.')

        self.wdgScrivenerImportDetails.setVisible(True)
        self.wdgScrivenerImportDetails.setNovel(novel)
        self.btnSaveScrivener.setEnabled(True)
        self._scrivenerNovel = novel
        # self.repo.insert_novel(novel)
        # for scene in novel.scenes:
        #     self.repo.insert_scene(novel, scene)
