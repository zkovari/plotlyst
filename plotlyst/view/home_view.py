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

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QFrame

from plotlyst.core.client import client
from plotlyst.core.domain import Novel
from plotlyst.view.dialog.new_novel import NewNovelDialog
from plotlyst.view.generated.home_view_ui import Ui_HomeView
from plotlyst.view.generated.novel_card_ui import Ui_NovelCard
from plotlyst.view.icons import IconRegistry
from plotlyst.view.layout import FlowLayout


class HomeView(QObject):
    loadNovel = pyqtSignal(Novel)

    def __init__(self, parent=None):
        super(HomeView, self).__init__(parent)
        self.widget = QWidget()
        self.ui = Ui_HomeView()
        self.ui.setupUi(self.widget)
        self._layout = FlowLayout(spacing=9)
        self.ui.novels.setLayout(self._layout)

        self._novel_cards: List[NovelCard] = []
        self.update()

        self.ui.btnAdd.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnAdd.clicked.connect(self._add_new_novel)

    def update(self):
        self._layout.clear()
        self._novel_cards.clear()
        for novel in client.novels():
            card = NovelCard(novel)
            self._layout.addWidget(card)
            self._novel_cards.append(card)
            card.loadingRequested.connect(self.loadNovel.emit)

    def _add_new_novel(self):
        title = NewNovelDialog().display()
        if title:
            client.insert_novel(Novel(title))
            self.update()


class NovelCard(Ui_NovelCard, QFrame):
    loadingRequested = pyqtSignal(Novel)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.label.setText(self.novel.title)

        self.btnLoad.clicked.connect(lambda: self.loadingRequested.emit(self.novel))
