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
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame
from overrides import overrides

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.view._view import AbstractView
from src.main.python.plotlyst.view.common import ask_confirmation
from src.main.python.plotlyst.view.dialog.new_novel import NovelEditionDialog
from src.main.python.plotlyst.view.generated.home_view_ui import Ui_HomeView
from src.main.python.plotlyst.view.generated.novel_card_ui import Ui_NovelCard
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import FlowLayout


class HomeView(AbstractView):
    loadNovel = pyqtSignal(Novel)

    def __init__(self):
        super(HomeView, self).__init__()
        self.ui = Ui_HomeView()
        self.ui.setupUi(self.widget)
        self._layout = FlowLayout(spacing=9)
        self.ui.novels.setLayout(self._layout)

        self.novel_cards: List[NovelCard] = []
        self.selected_card: Optional['NovelCard'] = None
        self.refresh()

        self.ui.btnAdd.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnAdd.clicked.connect(self._add_new_novel)
        self.ui.btnEdit.setIcon(IconRegistry.edit_icon())
        self.ui.btnEdit.clicked.connect(self._on_edit)
        self.ui.btnDelete.setIcon(IconRegistry.trash_can_icon(color='white'))
        self.ui.btnDelete.clicked.connect(self._on_delete)
        self.ui.btnDelete.setDisabled(True)
        self.ui.btnEdit.setDisabled(True)

    @overrides
    def refresh(self):
        self._layout.clear()
        self.novel_cards.clear()
        for novel in client.novels():
            card = NovelCard(novel)
            self._layout.addWidget(card)
            self.novel_cards.append(card)
            card.loadingRequested.connect(self.loadNovel.emit)
            card.selected.connect(self._card_selected)

    def _add_new_novel(self):
        if self.selected_card:
            self.selected_card.clearSelection()
            self.ui.btnDelete.setDisabled(True)
            self.ui.btnEdit.setDisabled(True)
        title = NovelEditionDialog().display()
        if title:
            client.insert_novel(Novel(title))
            self.refresh()

    def _on_edit(self):
        title = NovelEditionDialog().display(self.selected_card.novel)
        if title:
            self.selected_card.novel.title = title
            self.selected_card.update()
            client.update_novel(self.selected_card.novel)

    def _on_delete(self):
        if ask_confirmation(f'Are you sure you want to delete the novel "{self.selected_card.novel.title}"?'):
            client.delete_novel(self.selected_card.novel)
            self.selected_card.deleteLater()
            self.selected_card = None
            self.ui.btnDelete.setDisabled(True)
            self.refresh()

    def _card_selected(self, card: 'NovelCard'):
        if self.selected_card and self.selected_card is not card:
            self.selected_card.clearSelection()
        self.selected_card = card
        self.ui.btnDelete.setEnabled(True)
        self.ui.btnEdit.setEnabled(True)


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

    def update(self):
        self.label.setText(self.novel.title)

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
