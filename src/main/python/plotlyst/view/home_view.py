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
from typing import List, Optional

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QFrame
from overrides import overrides

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.view.common import ask_confirmation
from src.main.python.plotlyst.view.dialog.new_novel import NewNovelDialog
from src.main.python.plotlyst.view.generated.home_view_ui import Ui_HomeView
from src.main.python.plotlyst.view.generated.novel_card_ui import Ui_NovelCard
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import FlowLayout


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
        self._selected_card: Optional['NovelCard'] = None
        self.update()

        self.ui.btnAdd.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnAdd.clicked.connect(self._add_new_novel)
        self.ui.btnDelete.setIcon(IconRegistry.trash_can_icon(color='white'))
        self.ui.btnDelete.clicked.connect(self._on_delete)
        self.ui.btnDelete.setDisabled(True)

    def update(self):
        self._layout.clear()
        self._novel_cards.clear()
        for novel in client.novels():
            card = NovelCard(novel)
            self._layout.addWidget(card)
            self._novel_cards.append(card)
            card.loadingRequested.connect(self.loadNovel.emit)
            card.selected.connect(self._card_selected)

    def _add_new_novel(self):
        if self._selected_card:
            self._selected_card.clearSelection()
            self.ui.btnDelete.setDisabled(True)
        title = NewNovelDialog().display()
        if title:
            client.insert_novel(Novel(title))
            self.update()

    def _on_delete(self):
        if ask_confirmation(f'Are you sure you want to delete the novel "{self._selected_card.novel.title}"?'):
            client.delete_novel(self._selected_card.novel)
            self._selected_card.deleteLater()
            self._selected_card = None
            self.ui.btnDelete.setDisabled(True)
            self.update()

    def _card_selected(self, card: 'NovelCard'):
        if self._selected_card:
            self._selected_card.clearSelection()
        self._selected_card = card
        self.ui.btnDelete.setEnabled(True)


class NovelCard(Ui_NovelCard, QFrame):
    loadingRequested = pyqtSignal(Novel)
    selected = pyqtSignal(object)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.label.setText(self.novel.title)
        self._setStyleSheet()

        self.btnLoad.clicked.connect(lambda: self.loadingRequested.emit(self.novel))

    @overrides
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self._setStyleSheet(selected=True)
        self.selected.emit(self)

    def clearSelection(self):
        self._setStyleSheet()

    def _setStyleSheet(self, selected: bool = False):
        border_color = '#2a4d69' if selected else '#adcbe3'
        border_size = 4 if selected else 2
        background_color = '#dec3c3' if selected else '#f9f4f4'
        self.setStyleSheet(f'''
        QFrame[mainFrame=true] {{
            border: {border_size}px solid {border_color};
            border-radius: 15px;
            background-color: {background_color};
        }}''')
