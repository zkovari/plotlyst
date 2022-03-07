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

from PyQt5.QtCore import QItemSelection
from PyQt5.QtWidgets import QWidget
from overrides import overrides
from qthandy import ask_confirmation, busy, gc, incr_font

from src.main.python.plotlyst.core.domain import Novel, Character
from src.main.python.plotlyst.event.core import emit_event, EventListener, Event
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import NovelReloadRequestedEvent, CharacterChangedEvent, ToggleOutlineViewTitle
from src.main.python.plotlyst.model.characters_model import CharactersTableModel
from src.main.python.plotlyst.model.common import proxy
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.character_editor import CharacterEditor
from src.main.python.plotlyst.view.common import link_buttons_to_pages
from src.main.python.plotlyst.view.generated.characters_title_ui import Ui_CharactersTitle
from src.main.python.plotlyst.view.generated.characters_view_ui import Ui_CharactersView
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.widget.cards import CharacterCard, CardSizeRatio
from src.main.python.plotlyst.view.widget.characters import CharacterTimelineWidget


class CharactersTitle(QWidget, Ui_CharactersTitle, EventListener):

    def __init__(self, novel: Novel, parent=None):
        super(CharactersTitle, self).__init__(parent)
        self.novel = novel
        self.setupUi(self)
        self.btnCharacter.setIcon(IconRegistry.character_icon())
        incr_font(self.lblTitle)

        self.refresh()

        event_dispatcher.register(self, CharacterChangedEvent)

    @overrides
    def event_received(self, event: Event):
        self.refresh()

    def refresh(self):
        self.btnMajor.setText(str(len(self.novel.major_characters())))
        self.btnMinor.setText(str(len(self.novel.minor_characters())))


class CharactersView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel)
        self.ui = Ui_CharactersView()
        self.ui.setupUi(self.widget)
        self.editor: Optional[CharacterEditor] = None
        self.title = CharactersTitle(self.novel)

        self.model = CharactersTableModel(novel)
        self._proxy = proxy(self.model)
        self.ui.tblCharacters.setModel(self._proxy)
        self._proxy.setSortRole(CharactersTableModel.SortRole)

        self.ui.tblCharacters.setColumnWidth(CharactersTableModel.ColName, 200)
        self.ui.tblCharacters.setColumnWidth(CharactersTableModel.ColRole, 40)
        self.ui.tblCharacters.setColumnWidth(CharactersTableModel.ColEnneagram, 40)
        self.ui.tblCharacters.setColumnWidth(CharactersTableModel.ColMbti, 90)

        self.ui.tblCharacters.selectionModel().selectionChanged.connect(self._on_character_selected)
        self.ui.tblCharacters.doubleClicked.connect(self.ui.btnEdit.click)
        self.ui.btnCardsView.setIcon(IconRegistry.cards_icon())
        self.ui.btnTableView.setIcon(IconRegistry.table_icon())
        self.ui.btnBackstoryView.setIcon(IconRegistry.from_name('mdi.timeline', color_on='darkBlue'))
        self.ui.wdgCharacterSelector.setExclusive(False)
        self.ui.wdgCharacterSelector.characterToggled.connect(self._backstory_character_toggled)

        self.ui.btnEdit.setIcon(IconRegistry.edit_icon())
        self.ui.btnEdit.clicked.connect(self._on_edit)
        self.ui.btnNew.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnNew.clicked.connect(self._on_new)
        self.ui.btnDelete.setIcon(IconRegistry.trash_can_icon(color='white'))
        self.ui.btnDelete.clicked.connect(self._on_delete)

        self.widget.setStyleSheet(
            f'''#scrollAreaBackstoryContent {{background-image: url({resource_registry.cover1});}}
                                       ''')

        self.selected_card: Optional[CharacterCard] = None
        self.ui.cards.selectionCleared.connect(lambda: self._enable_action_buttons(False))
        self.ui.cards.setCardsSizeRatio(CardSizeRatio.RATIO_2_3)
        self.ui.cards.setCardsWidth(142)
        self._update_cards()

        self.ui.btnGroupViews.buttonToggled.connect(self._switch_view)
        link_buttons_to_pages(self.ui.stackCharacters, [(self.ui.btnCardsView, self.ui.pageCardsView),
                                                        (self.ui.btnTableView, self.ui.pageTableView),
                                                        (self.ui.btnBackstoryView, self.ui.pageBackstory)])
        self.ui.btnCardsView.setChecked(True)

        self.ui.cards.swapped.connect(self._characters_swapped)

    @overrides
    def refresh(self):
        self.model.modelReset.emit()
        self.ui.btnEdit.setDisabled(True)
        self.ui.btnDelete.setDisabled(True)

        self._update_cards()

    @overrides
    def can_show_title(self) -> bool:
        return self.ui.stackedWidget.currentWidget() is self.ui.pageView

    def _update_cards(self):
        self.selected_card = None
        self.ui.cards.clear()

        for character in self.novel.characters:
            card = CharacterCard(character)
            self.ui.cards.addCard(card)
            card.selected.connect(self._card_selected)
            card.doubleClicked.connect(self._on_edit)

    def _on_character_selected(self, selection: QItemSelection):
        self._enable_action_buttons(len(selection.indexes()) > 0)

    def _enable_action_buttons(self, enabled: bool):
        self.ui.btnDelete.setEnabled(enabled)
        self.ui.btnEdit.setEnabled(enabled)

    def _card_selected(self, card: CharacterCard):
        if self.selected_card and self.selected_card is not card:
            self.selected_card.clearSelection()
        self.selected_card = card
        self.ui.btnDelete.setEnabled(True)
        self.ui.btnEdit.setEnabled(True)

    def _characters_swapped(self, removed: CharacterCard, moved_to: CharacterCard):
        self.novel.characters.remove(removed.character)
        pos = self.novel.characters.index(moved_to.character)
        self.novel.characters.insert(pos, removed.character)

        self.refresh()
        self.repo.update_novel(self.novel)

    def _switch_view(self):
        if self.ui.btnCardsView.isChecked():
            self._enable_action_buttons(bool(self.selected_card))
            self.ui.wdgToolbar.setVisible(True)
        elif self.ui.btnTableView.isChecked():
            self._enable_action_buttons(len(self.ui.tblCharacters.selectedIndexes()) > 0)
            self.ui.wdgToolbar.setVisible(True)
        else:
            self.ui.wdgToolbar.setVisible(False)
            self.ui.wdgCharacterSelector.updateCharacters(self.novel.characters, checkAll=False)

    def _on_edit(self):
        character = None
        if self.ui.btnTableView.isChecked():
            indexes = self.ui.tblCharacters.selectedIndexes()
            if indexes:
                character = indexes[0].data(role=CharactersTableModel.CharacterRole)
        else:
            character = self.selected_card.character

        if character:
            self.editor = CharacterEditor(self.novel, character)
            self._switch_to_editor()

    def _switch_to_editor(self):
        emit_event(ToggleOutlineViewTitle(self, visible=False))
        self.ui.pageEditor.layout().addWidget(self.editor.widget)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageEditor)

        self.editor.ui.btnClose.clicked.connect(self._on_close_editor)

    def _on_close_editor(self):
        character = self.editor.character
        if not character.avatar and character.name:
            avatars.update_image(character)
        self.ui.pageEditor.layout().removeWidget(self.editor.widget)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageView)
        self.editor.widget.deleteLater()
        self.editor = None
        if character.name:
            emit_event(CharacterChangedEvent(self, character))
        emit_event(ToggleOutlineViewTitle(self, visible=True))
        self.refresh()

    def _on_new(self):
        character = Character('')
        self.novel.characters.append(character)
        self.repo.insert_character(self.novel, character)
        self.editor = CharacterEditor(self.novel, character)
        self._switch_to_editor()

    @busy
    def _on_delete(self, checked: bool):
        character = None
        if self.ui.btnTableView.isChecked():
            indexes = self.ui.tblCharacters.selectedIndexes()
            if indexes:
                character = indexes[0].data(role=CharactersTableModel.CharacterRole)
        else:
            character = self.selected_card.character

        if not ask_confirmation(f'Are you sure you want to delete character {character.name}?'):
            return
        self.novel.characters.remove(character)
        self.ui.wdgCharacterSelector.removeCharacter(character)
        self.repo.delete_character(self.novel, character)
        emit_event(NovelReloadRequestedEvent(self))
        self.refresh()

    @busy
    def _backstory_character_toggled(self, character: Character, toggled: bool):
        if toggled:
            wdg = CharacterTimelineWidget(self.ui.scrollAreaBackstoryContent)
            wdg.setCharacter(character)
            self.ui.scrollAreaBackstoryContent.layout().addWidget(wdg)
            wdg.changed.connect(lambda: self.repo.update_character(character))
        else:
            for i in range(self.ui.scrollAreaBackstoryContent.layout().count()):
                wdg = self.ui.scrollAreaBackstoryContent.layout().itemAt(i).widget()
                if isinstance(wdg, CharacterTimelineWidget) and wdg.character.id == character.id:
                    self.ui.scrollAreaBackstoryContent.layout().removeWidget(wdg)
                    return gc(wdg)
