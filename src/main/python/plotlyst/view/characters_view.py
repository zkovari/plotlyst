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
from typing import Optional, List

import qtawesome
from PyQt5 import QtGui
from PyQt5.QtCore import QItemSelection, pyqtSignal, QSize
from PyQt5.QtWidgets import QFrame
from overrides import overrides

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel, Character
from src.main.python.plotlyst.event.core import emit_event
from src.main.python.plotlyst.events import NovelReloadRequestedEvent, CharacterChangedEvent
from src.main.python.plotlyst.model.characters_model import CharactersTableModel
from src.main.python.plotlyst.model.common import proxy
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.character_editor import CharacterEditor
from src.main.python.plotlyst.view.common import ask_confirmation, busy
from src.main.python.plotlyst.view.generated.character_card_ui import Ui_CharacterCard
from src.main.python.plotlyst.view.generated.characters_view_ui import Ui_CharactersView
from src.main.python.plotlyst.view.icons import IconRegistry, avatars, set_avatar
from src.main.python.plotlyst.view.layout import FlowLayout


class CharactersView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel)
        self.ui = Ui_CharactersView()
        self.ui.setupUi(self.widget)
        self.editor: Optional[CharacterEditor] = None

        self.model = CharactersTableModel(novel)
        self._proxy = proxy(self.model)
        self.ui.listCharacters.setModel(self._proxy)

        self.ui.listCharacters.selectionModel().selectionChanged.connect(self._on_character_selected)
        self.ui.listCharacters.doubleClicked.connect(self.ui.btnEdit.click)
        self.ui.btnCardsView.setIcon(IconRegistry.cards_icon())
        self.ui.btnTableView.setIcon(IconRegistry.table_icon())
        self.ui.btnEdit.setIcon(IconRegistry.edit_icon())
        self.ui.btnEdit.clicked.connect(self._on_edit)
        self.ui.btnNew.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnNew.clicked.connect(self._on_new)
        self.ui.btnDelete.setIcon(IconRegistry.trash_can_icon(color='white'))
        self.ui.btnDelete.clicked.connect(self._on_delete)

        self._cards_layout = FlowLayout(spacing=9)
        self.ui.cards.setLayout(self._cards_layout)
        self.character_cards: List[CharacterCard] = []
        self.selected_card: Optional[CharacterCard] = None
        self._update_cards()

        self.ui.btnGroupViews.buttonToggled.connect(self._switch_view)
        self.ui.btnCardsView.setChecked(True)

    @overrides
    def refresh(self):
        self.model.modelReset.emit()
        self.ui.btnEdit.setDisabled(True)
        self.ui.btnDelete.setDisabled(True)

        self._update_cards()

    def _update_cards(self):
        self.character_cards.clear()
        self.selected_card = None
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item:
                item.widget().deleteLater()

        for character in self.novel.characters:
            card = CharacterCard(character)
            self._cards_layout.addWidget(card)
            self.character_cards.append(card)
            card.selected.connect(self._card_selected)
            card.doubleClicked.connect(self._on_edit)

    def _on_character_selected(self, selection: QItemSelection):
        self._enable_action_buttons(len(selection.indexes()) > 0)

    def _enable_action_buttons(self, enabled: bool):
        self.ui.btnDelete.setEnabled(enabled)
        self.ui.btnEdit.setEnabled(enabled)

    def _card_selected(self, card: 'CharacterCard'):
        if self.selected_card and self.selected_card is not card:
            self.selected_card.clearSelection()
        self.selected_card = card
        self.ui.btnDelete.setEnabled(True)
        self.ui.btnEdit.setEnabled(True)

    def _switch_view(self):
        if self.ui.btnCardsView.isChecked():
            self.ui.stackCharacters.setCurrentWidget(self.ui.pageCardsView)
            self._enable_action_buttons(bool(self.selected_card))
        else:
            self.ui.stackCharacters.setCurrentWidget(self.ui.pageTableView)
            self._enable_action_buttons(len(self.ui.listCharacters.selectedIndexes()) > 0)

    def _on_edit(self):
        character = None
        if self.ui.btnTableView.isChecked():
            indexes = self.ui.listCharacters.selectedIndexes()
            if indexes:
                character = indexes[0].data(role=CharactersTableModel.CharacterRole)
        else:
            character = self.selected_card.character

        if character:
            self.editor = CharacterEditor(self.novel, character)
            self._switch_to_editor()

    def _switch_to_editor(self):
        self.ui.pageEditor.layout().addWidget(self.editor.widget)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageEditor)

        self.editor.ui.btnClose.clicked.connect(self._on_close_editor)

    def _on_close_editor(self):
        character = self.editor.character
        if not character.avatar and character.name:
            avatars.update(character)
        self.ui.pageEditor.layout().removeWidget(self.editor.widget)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageView)
        self.editor.widget.deleteLater()
        self.editor = None
        if character.name:
            emit_event(CharacterChangedEvent(self, character))
        self.refresh()

    def _on_new(self):
        self.editor = CharacterEditor(self.novel)
        self._switch_to_editor()

    @busy
    def _on_delete(self, checked: bool):
        character = None
        if self.ui.btnTableView.isChecked():
            indexes = self.ui.listCharacters.selectedIndexes()
            if indexes:
                character = indexes[0].data(role=CharactersTableModel.CharacterRole)
        else:
            character = self.selected_card.character

        if not ask_confirmation(f'Are you sure you want to delete character {character.name}?'):
            return
        self.novel.characters.remove(character)
        client.delete_character(self.novel, character)
        emit_event(NovelReloadRequestedEvent(self))
        self.refresh()


class CharacterCard(Ui_CharacterCard, QFrame):
    selected = pyqtSignal(object)
    doubleClicked = pyqtSignal(object)

    def __init__(self, character: Character, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.character = character
        self.lblName.setText(self.character.name)
        set_avatar(self.lblPic, self.character)

        enneagram = self.character.enneagram()
        if enneagram:
            self.lblEnneagram.setPixmap(
                qtawesome.icon(enneagram.icon, color=enneagram.icon_color).pixmap(QSize(32, 32)))
        role = self.character.role()
        if role:
            self.lblRole.setPixmap(qtawesome.icon(role.icon, color=role.icon_color).pixmap(QSize(24, 24)))
        self._setStyleSheet()

    @overrides
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self._setStyleSheet(selected=True)
        self.selected.emit(self)

    @overrides
    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        self._setStyleSheet(selected=True)
        self.selected.emit(self)
        self.doubleClicked.emit(self)

    # def update(self):
    #     self.label.setText(self.novel.title)

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
