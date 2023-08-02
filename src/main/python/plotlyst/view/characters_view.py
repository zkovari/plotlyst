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
from typing import Optional, List

from PyQt6.QtCore import QItemSelection, QPoint
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import QWidget
from overrides import overrides
from qthandy import busy, gc, incr_font, bold, vbox, vspacer, transparent, underline
from qthandy.filter import InstantTooltipEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR
from src.main.python.plotlyst.core.domain import Novel, Character, RelationsNetwork, CharacterNode
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import emit_event, EventListener, Event
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import CharacterChangedEvent, CharacterDeletedEvent, NovelSyncEvent
from src.main.python.plotlyst.model.characters_model import CharactersTableModel
from src.main.python.plotlyst.model.common import proxy
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.service.persistence import delete_character
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.character_editor import CharacterEditor
from src.main.python.plotlyst.view.common import link_buttons_to_pages, ButtonPressResizeEventFilter, \
    action
from src.main.python.plotlyst.view.generated.characters_title_ui import Ui_CharactersTitle
from src.main.python.plotlyst.view.generated.characters_view_ui import Ui_CharactersView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.style.base import apply_bg_image
from src.main.python.plotlyst.view.widget.cards import CharacterCard, CardSizeRatio
from src.main.python.plotlyst.view.widget.character import CharacterComparisonWidget, LayoutType, \
    CharacterComparisonAttribute
from src.main.python.plotlyst.view.widget.character.comp import CharactersTreeView
from src.main.python.plotlyst.view.widget.character.relations import RelationsView, RelationsSelectorBox
from src.main.python.plotlyst.view.widget.characters import CharacterTimelineWidget, CharactersProgressWidget


class CharactersTitle(QWidget, Ui_CharactersTitle, EventListener):

    def __init__(self, novel: Novel, parent=None):
        super(CharactersTitle, self).__init__(parent)
        self.novel = novel
        self.setupUi(self)
        self.btnCharacter.setIcon(IconRegistry.character_icon())
        incr_font(self.lblTitle)
        bold(self.lblTitle)

        self.refresh()

        event_dispatcher.register(self, CharacterChangedEvent)
        event_dispatcher.register(self, CharacterDeletedEvent)
        event_dispatcher.register(self, NovelSyncEvent)

    @overrides
    def event_received(self, event: Event):
        self.refresh()

    def refresh(self):
        self.btnMajor.setText(str(len(self.novel.major_characters())))
        self.btnSecondary.setText(str(len(self.novel.secondary_characters())))
        self.btnMinor.setText(str(len(self.novel.minor_characters())))


class CharactersView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel)
        self.ui = Ui_CharactersView()
        self.ui.setupUi(self.widget)
        self.editor: Optional[CharacterEditor] = None
        self.title = CharactersTitle(self.novel)
        self.ui.wdgTitleParent.layout().addWidget(self.title)

        self.model = CharactersTableModel(novel)
        self._proxy = proxy(self.model)
        self.ui.tblCharacters.setModel(self._proxy)
        self._proxy.setSortRole(CharactersTableModel.SortRole)

        self.ui.tblCharacters.setColumnWidth(CharactersTableModel.ColName, 200)
        self.ui.tblCharacters.setColumnWidth(CharactersTableModel.ColRole, 40)
        self.ui.tblCharacters.setColumnWidth(CharactersTableModel.ColEnneagram, 40)
        self.ui.tblCharacters.setColumnWidth(CharactersTableModel.ColMbti, 90)
        self.ui.tblCharacters.horizontalHeader().setProperty('main-header', True)

        self.ui.tblCharacters.selectionModel().selectionChanged.connect(self._on_character_selected)
        self.ui.tblCharacters.doubleClicked.connect(self.ui.btnEdit.click)
        self.ui.btnCardsView.setIcon(IconRegistry.cards_icon())
        self.ui.btnTableView.setIcon(IconRegistry.table_icon())
        self.ui.btnBackstoryView.setIcon(IconRegistry.from_name('mdi.timeline', color_on=PLOTLYST_SECONDARY_COLOR))
        self.ui.btnComparison.setIcon(
            IconRegistry.from_name('mdi.compare-horizontal', color_on=PLOTLYST_SECONDARY_COLOR))
        self.ui.btnRelationsView.setIcon(
            IconRegistry.from_name('ph.share-network-bold', color_on=PLOTLYST_SECONDARY_COLOR))
        self.ui.btnProgressView.setIcon(IconRegistry.progress_check_icon('black'))
        self.setNavigableButtonGroup(self.ui.btnGroupViews)

        self.ui.wdgCharacterSelector.setExclusive(False)
        self.ui.wdgCharacterSelector.characterToggled.connect(self._backstory_character_toggled)

        self.ui.btnEdit.setIcon(IconRegistry.edit_icon())
        self.ui.btnEdit.clicked.connect(self._on_edit)
        self.ui.btnNew.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnNew.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnNew))
        self.ui.btnNew.clicked.connect(self._on_new)
        if app_env.is_mac():
            self.ui.btnDelete.setShortcut(QKeySequence('Ctrl+Backspace'))
        self.ui.btnDelete.setIcon(IconRegistry.trash_can_icon(color='white'))
        self.ui.btnDelete.clicked.connect(self._on_delete)

        if self.novel.is_readonly():
            for btn in [self.ui.btnNew, self.ui.btnDelete]:
                btn.setDisabled(True)
                btn.setToolTip('Option disabled in Scrivener synchronization mode')
                btn.installEventFilter(InstantTooltipEventFilter(btn))

        apply_bg_image(self.ui.scrollAreaBackstoryContent, resource_registry.cover1)

        self.selected_card: Optional[CharacterCard] = None
        self.ui.cards.selectionCleared.connect(lambda: self._enable_action_buttons(False))
        self.ui.cards.cardSelected.connect(self._card_selected)
        self.ui.cards.cardDoubleClicked.connect(self._on_edit)
        self.ui.cards.cardCustomContextMenuRequested.connect(self._show_card_menu)
        self.ui.cards.setCardsSizeRatio(CardSizeRatio.RATIO_2_3)
        self.ui.cards.setCardsWidth(142)
        self._init_cards()

        transparent(self.ui.btnComparisonLabel)
        underline(self.ui.btnComparisonLabel)
        self.ui.btnComparisonLabel.setIcon(IconRegistry.from_name('mdi.compare-horizontal'))
        self.ui.btnHorizontalComparison.setIcon(IconRegistry.from_name('ph.columns-bold'))
        self.ui.btnVerticalComparison.setIcon(IconRegistry.from_name('ph.rows-bold'))
        self.ui.btnGridComparison.setIcon(IconRegistry.from_name('ph.grid-four-bold'))
        self.ui.btnSummaryComparison.setIcon(IconRegistry.synopsis_icon())
        self.ui.btnBigFiveComparison.setIcon(IconRegistry.big_five_icon())

        self.ui.splitterCompTree.setSizes([150, 500])
        self._wdgComparison = CharacterComparisonWidget(self.ui.pageComparison)
        self.ui.scrollAreaComparisonContent.layout().addWidget(self._wdgComparison)
        self._wdgCharactersCompTree = CharactersTreeView(self.novel)
        self.ui.wdgCharactersCompTreeParent.layout().addWidget(self._wdgCharactersCompTree)

        self._wdgCharactersCompTree.characterToggled.connect(self._wdgComparison.updateCharacter)
        self.ui.btnHorizontalComparison.clicked.connect(lambda: self._wdgComparison.updateLayout(LayoutType.HORIZONTAL))
        self.ui.btnVerticalComparison.clicked.connect(lambda: self._wdgComparison.updateLayout(LayoutType.VERTICAL))
        self.ui.btnGridComparison.clicked.connect(lambda: self._wdgComparison.updateLayout(LayoutType.FLOW))
        self.ui.btnSummaryComparison.clicked.connect(
            lambda: self._wdgComparison.displayAttribute(CharacterComparisonAttribute.SUMMARY))
        self.ui.btnBigFiveComparison.clicked.connect(
            lambda: self._wdgComparison.displayAttribute(CharacterComparisonAttribute.BIG_FIVE))

        self._relations = RelationsView(self.novel)
        self.ui.relationsParent.layout().addWidget(self._relations)

        self._relationsSelector = RelationsSelectorBox(self.novel)
        vbox(self.ui.wdgGraphSelectorParent).addWidget(self._relationsSelector)
        self.ui.wdgGraphSelectorParent.layout().addWidget(vspacer())
        self._relationsSelector.currentChanged.connect(lambda i, w: self._relations.refresh(w.network()))

        self._relations.relationsScene().charactersChanged.connect(self._relationsSelector.refreshCharacters)

        node = CharacterNode(50, 50)
        if self.novel.characters:
            node.set_character(self.novel.characters[0])
        network1 = RelationsNetwork('Network 1', icon='ph.share-network-bold', nodes=[node])
        self._relationsSelector.addNetwork(network1)
        self._relationsSelector.addNetwork(RelationsNetwork('Network 2', icon='ph.share-network-bold'))

        self.ui.networkSplitter.setSizes([100, 500])

        self._progress = CharactersProgressWidget()
        self.ui.pageProgressView.layout().addWidget(self._progress)
        self._progress.setNovel(self.novel)
        self._progress.characterClicked.connect(self._edit_character)
        self._progress.refresh()

        self.ui.btnGroupViews.buttonToggled.connect(self._switch_view)
        link_buttons_to_pages(self.ui.stackCharacters, [(self.ui.btnCardsView, self.ui.pageCardsView),
                                                        (self.ui.btnTableView, self.ui.pageTableView),
                                                        (self.ui.btnBackstoryView, self.ui.pageBackstory),
                                                        (self.ui.btnRelationsView, self.ui.pageRelationsView),
                                                        (self.ui.btnComparison, self.ui.pageComparison),
                                                        (self.ui.btnProgressView, self.ui.pageProgressView)])
        self.ui.btnCardsView.setChecked(True)

        self.ui.cards.orderChanged.connect(self._characters_swapped)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageView)

    @overrides
    def refresh(self):
        self.model.modelReset.emit()
        self.ui.btnEdit.setDisabled(True)
        self.ui.btnDelete.setDisabled(True)

        self._init_cards()
        self._progress.refresh()

    def _show_card_menu(self, card: CharacterCard, pos: QPoint):
        menu = MenuWidget()
        menu.addAction(action('Edit', IconRegistry.edit_icon(), self._on_edit))
        menu.addSeparator()
        action_ = action('Delete', IconRegistry.trash_can_icon(), self.ui.btnDelete.click)
        action_.setDisabled(self.novel.is_readonly())
        menu.addAction(action_)
        menu.exec()

    def _init_cards(self):
        self.selected_card = None
        self.ui.cards.clear()

        for character in self.novel.characters:
            card = CharacterCard(character, self.ui.cards)
            self.ui.cards.addCard(card)

    def _on_character_selected(self, selection: QItemSelection):
        self._enable_action_buttons(len(selection.indexes()) > 0)

    def _enable_action_buttons(self, enabled: bool):
        if not self.novel.is_readonly():
            self.ui.btnDelete.setEnabled(enabled)
        self.ui.btnEdit.setEnabled(enabled)

    def _card_selected(self, card: CharacterCard):
        if self.selected_card and self.selected_card is not card:
            self.selected_card.clearSelection()
        self.selected_card = card
        if not self.novel.is_readonly():
            self.ui.btnDelete.setEnabled(True)
        self.ui.btnEdit.setEnabled(True)

    def _characters_swapped(self, characters: List[Character]):
        self.novel.characters[:] = characters

        self.refresh()
        self.repo.update_novel(self.novel)

    def _switch_view(self):
        if self.ui.btnCardsView.isChecked():
            self._enable_action_buttons(bool(self.selected_card))
            self.ui.wdgToolbar.setVisible(True)
        elif self.ui.btnTableView.isChecked():
            self._enable_action_buttons(len(self.ui.tblCharacters.selectedIndexes()) > 0)
            self.ui.wdgToolbar.setVisible(True)
        elif self.ui.btnBackstoryView.isChecked():
            self.ui.wdgToolbar.setVisible(False)
            self.ui.wdgCharacterSelector.updateCharacters(self.novel.characters, checkAll=False)
        elif self.ui.btnComparison.isChecked():
            self.ui.wdgToolbar.setVisible(False)
            self._wdgCharactersCompTree.refresh()
        else:
            self.ui.wdgToolbar.setVisible(False)

    def _on_edit(self):
        character = None
        if self.ui.btnTableView.isChecked():
            indexes = self.ui.tblCharacters.selectedIndexes()
            if indexes:
                character = indexes[0].data(role=CharactersTableModel.CharacterRole)
        else:
            character = self.selected_card.character

        if character:
            self._edit_character(character)

    @busy
    def _edit_character(self, character: Character):
        self.editor = CharacterEditor(self.novel, character)
        self._switch_to_editor()

    def _switch_to_editor(self):
        self.title.setHidden(True)
        self.ui.pageEditor.layout().addWidget(self.editor.widget)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageEditor)

        self.editor.close.connect(self._on_close_editor)

    @busy
    def _on_close_editor(self):
        character = self.editor.character
        self.ui.pageEditor.layout().removeWidget(self.editor.widget)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageView)
        self.title.setVisible(True)

        emit_event(CharacterChangedEvent(self, character))
        gc(self.editor.widget)
        gc(self.editor)
        self.editor = None
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

        if character and delete_character(self.novel, character):
            self.ui.wdgCharacterSelector.removeCharacter(character)
            emit_event(CharacterDeletedEvent(self, character))
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
