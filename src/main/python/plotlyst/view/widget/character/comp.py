"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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
from abc import abstractmethod
from enum import Enum
from typing import Dict, Optional

import qtanim
from PyQt6 import sip
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QLabel, QTextEdit
from overrides import overrides
from qthandy import vbox, hbox, line, flow, gc, vspacer, clear_layout, bold, margins

from plotlyst.core.domain import Character, Novel, TemplateValue, LayoutType
from plotlyst.core.template import iq_field, eq_field, rationalism_field, creativity_field, \
    willpower_field, TemplateField
from plotlyst.event.core import EventListener, Event, emit_event
from plotlyst.event.handler import event_dispatchers
from plotlyst.events import CharacterSummaryChangedEvent, CharacterChangedEvent, CharacterDeletedEvent
from plotlyst.service.persistence import RepositoryPersistenceManager
from plotlyst.view.common import fade_out_and_gc
from plotlyst.view.icons import set_avatar, avatars
from plotlyst.view.widget.big_five import BigFiveChart, dimension_from
from plotlyst.view.widget.button import EyeToggle
from plotlyst.view.widget.character.editor import CharacterTimelineWidget
from plotlyst.view.widget.display import RoleIcon, ChartView
from plotlyst.view.widget.template.impl import BarTemplateFieldWidget
from plotlyst.view.widget.tree import TreeView, ContainerNode


class CharacterComparisonAttribute(Enum):
    SUMMARY = 0
    BIG_FIVE = 1
    FACULTIES = 2
    BACKSTORY = 3


class BaseDisplay:

    def __init__(self):
        self.repo = RepositoryPersistenceManager.instance()

    @abstractmethod
    def refresh(self):
        pass


class BigFiveDisplay(ChartView, BaseDisplay):
    def __init__(self, character: Character, parent=None):
        super(BigFiveDisplay, self).__init__(parent)
        self._character = character
        self._bigFive = BigFiveChart()
        self._bigFive.setTitle('')

        self.setChart(self._bigFive)
        self.refresh()

        self.setMinimumSize(250, 250)

    @overrides
    def refresh(self):
        for bf, values in self._character.big_five.items():
            self._bigFive.refreshDimension(dimension_from(bf), values)
            self.update()


class SummaryDisplay(QTextEdit, BaseDisplay):
    def __init__(self, novel: Novel, character: Character, parent=None):
        super(SummaryDisplay, self).__init__(parent)
        self._novel = novel
        self._character = character
        self._blockSave = False
        self.setToolTip('Character summary')
        self.setPlaceholderText('Character summary...')
        self.setProperty('rounded', True)
        self.setProperty('white-bg', True)
        self.setMaximumSize(250, 100)
        self.setMinimumWidth(200)
        self.setTabChangesFocus(True)

        self.refresh()

        self.textChanged.connect(self._save)

    @overrides
    def refresh(self):
        self._blockSave = True
        self.setText(self._character.summary)
        self._blockSave = False

    def _save(self):
        if self._blockSave:
            return

        self._character.summary = self.toPlainText()
        self.repo.update_character(self._character)
        emit_event(self._novel, CharacterSummaryChangedEvent(self, self._character))


class FacultiesDisplay(QWidget, BaseDisplay):
    def __init__(self, character: Character, parent=None):
        super().__init__(parent)
        self._character = character
        self._blockSave = False

        vbox(self)
        margins(self, left=10, right=10)

        self._iqEditor = self.FacultyEditor(self, self._character, iq_field)
        self._eqEditor = self.FacultyEditor(self, self._character, eq_field)
        self._ratEditor = self.FacultyEditor(self, self._character, rationalism_field)
        self._creaEditor = self.FacultyEditor(self, self._character, creativity_field)
        self._willEditor = self.FacultyEditor(self, self._character, willpower_field)

        self.layout().addWidget(self._iqEditor)
        self.layout().addWidget(self._eqEditor)
        self.layout().addWidget(self._ratEditor)
        self.layout().addWidget(self._creaEditor)
        self.layout().addWidget(self._willEditor)

        self.setMaximumWidth(300)
        self.setMinimumWidth(250)

        self.refresh()

    @overrides
    def refresh(self):
        self._blockSave = True
        for value in self._character.template_values:
            if value.id == iq_field.id:
                self._iqEditor.setValue(value)
            elif value.id == eq_field.id:
                self._eqEditor.setValue(value)
            elif value.id == rationalism_field.id:
                self._ratEditor.setValue(value)
            elif value.id == creativity_field.id:
                self._creaEditor.setValue(value)
            elif value.id == willpower_field.id:
                self._willEditor.setValue(value)

        self._blockSave = False

    def save(self):
        if self._blockSave:
            return
        self.repo.update_character(self._character)

    class FacultyEditor(BarTemplateFieldWidget):

        def __init__(self, display: 'FacultiesDisplay', character: Character, field: TemplateField, parent=None):
            super().__init__(field, parent)
            self._character = character
            self._display = display
            self._value: Optional[TemplateValue] = None

            self.lblName.setProperty('description', True)
            self.lblEmoji.setVisible(False)

        @overrides
        def setValue(self, value: TemplateValue):
            self._value = value
            super().setValue(value.value)

        @overrides
        def _valueChanged(self, value: int):
            self._value.value = value
            self._display.save()


class BackstoryDisplay(CharacterTimelineWidget, BaseDisplay):
    def __init__(self, character: Character, parent=None):
        super().__init__(parent)
        self._character = character
        self.setCharacter(self._character)

        self.changed.connect(self._save)

    def _save(self):
        self.repo.update_character(self._character)


class CharacterOverviewWidget(QWidget, EventListener):
    def __init__(self, novel: Novel, character: Character, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._character = character

        self._avatar = QLabel(self)
        set_avatar(self._avatar, self._character, size=118)
        self._roleIcon = RoleIcon(self)
        self._roleIcon.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if self._character.role:
            self._roleIcon.setRole(self._character.role, showText=True)

        vbox(self, 0)
        self._wdgHeader = QWidget()
        vbox(self._wdgHeader, 0)
        self._wdgHeader.layout().addWidget(self._avatar, alignment=Qt.AlignmentFlag.AlignCenter)
        self._wdgHeader.layout().addWidget(self._roleIcon, alignment=Qt.AlignmentFlag.AlignCenter)
        self._wdgHeader.layout().addWidget(line())

        self._display: Optional[BaseDisplay] = None
        self._displayContainer = QWidget()
        hbox(self._displayContainer, 0, 0)

        self.layout().addWidget(self._wdgHeader)
        self.layout().addWidget(self._displayContainer)
        self.layout().addWidget(vspacer())

        dispatcher = event_dispatchers.instance(self._novel)
        dispatcher.register(self, CharacterChangedEvent)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, CharacterChangedEvent):
            if event.character is self._character and self._display is not None:
                self._display.refresh()

    def display(self, attribute: CharacterComparisonAttribute):
        if self._display:
            self._displayContainer.layout().removeWidget(self._display)
            gc(self._display)
            self._display = None

        self._wdgHeader.setVisible(True)

        if attribute == CharacterComparisonAttribute.BIG_FIVE:
            self._display = BigFiveDisplay(self._character)
            self._displayContainer.layout().addWidget(self._display)
        elif attribute == CharacterComparisonAttribute.SUMMARY:
            self._display = SummaryDisplay(self._novel, self._character)
            self._displayContainer.layout().addWidget(self._display, alignment=Qt.AlignmentFlag.AlignCenter)
        elif attribute == CharacterComparisonAttribute.FACULTIES:
            self._display = FacultiesDisplay(self._character)
            self._displayContainer.layout().addWidget(self._display)
        elif attribute == CharacterComparisonAttribute.BACKSTORY:
            self._wdgHeader.setHidden(True)
            self._display = BackstoryDisplay(self._character)
            self._displayContainer.layout().addWidget(self._display)


class CharacterComparisonWidget(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._characters: Dict[Character, CharacterOverviewWidget] = {}
        hbox(self)
        self._currentDisplay: CharacterComparisonAttribute = CharacterComparisonAttribute.SUMMARY

    def updateCharacter(self, character: Character, enabled: bool):
        if enabled:
            wdg = CharacterOverviewWidget(self._novel, character)
            wdg.display(self._currentDisplay)
            self._characters[character] = wdg
            self.layout().addWidget(wdg)
            qtanim.fade_in(wdg)
        else:
            wdg = self._characters.pop(character)
            fade_out_and_gc(self, wdg)

    def updateLayout(self, layoutType: LayoutType):
        widgets = []
        for i in range(self.layout().count()):
            widgets.append(self.layout().itemAt(i).widget())

        sip.delete(self.layout())

        if layoutType == LayoutType.HORIZONTAL:
            hbox(self)
        elif layoutType == LayoutType.VERTICAL:
            vbox(self)
        elif layoutType == LayoutType.FLOW:
            flow(self)

        for wdg in widgets:
            self.layout().addWidget(wdg)

        for wdg in self._characters.values():
            wdg.display(self._currentDisplay)

    def displayAttribute(self, attribute: CharacterComparisonAttribute):
        if attribute == CharacterComparisonAttribute.BACKSTORY:
            self.updateLayout(LayoutType.HORIZONTAL)

        for wdg in self._characters.values():
            wdg.display(attribute)

        self._currentDisplay = attribute


class CharacterNode(ContainerNode):
    characterToggled = pyqtSignal(Character, bool)

    def __init__(self, character: Character, parent=None):
        super(CharacterNode, self).__init__(character.name, parent)
        self._character = character

        self.setPlusButtonEnabled(False)
        self.setMenuEnabled(False)
        self.setSelectionEnabled(False)

        self._btnVisible = EyeToggle()
        self._btnVisible.setToolTip('Toggle arc')
        self._btnVisible.toggled.connect(self._toggled)
        self._wdgTitle.layout().addWidget(self._btnVisible)

        self.refresh()

    def refresh(self):
        self._lblTitle.setText(self._character.name)
        icon = avatars.avatar(self._character, fallback=False)
        if icon:
            self._icon.setIcon(icon)
            self._icon.setVisible(True)
        else:
            self._icon.setHidden(True)

    def isToggled(self) -> bool:
        return self._btnVisible.isChecked()

    def _toggled(self, toggled: bool):
        bold(self._lblTitle, toggled)
        self.characterToggled.emit(self._character, toggled)


class CharactersTreeView(TreeView, EventListener):
    characterToggled = pyqtSignal(Character, bool)

    def __init__(self, novel: Novel, parent=None):
        super(CharactersTreeView, self).__init__(parent)
        self._novel = novel
        self._centralWidget.setProperty('bg', True)
        self._nodes: Dict[Character, CharacterNode] = {}

        margins(self._centralWidget, top=20)
        self.refresh()

        dispatcher = event_dispatchers.instance(self._novel)
        dispatcher.register(self, CharacterDeletedEvent)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, CharacterDeletedEvent):
            node = self._nodes.pop(event.character, None)
            if node is not None:
                if node.isToggled():
                    self.characterToggled.emit(event.character, False)
                self._centralWidget.layout().removeWidget(node)
                gc(node)

    def refresh(self):
        clear_layout(self._centralWidget, auto_delete=False)

        for character in self._novel.characters:
            if character not in self._nodes.keys():
                node = CharacterNode(character)
                node.characterToggled.connect(self.characterToggled.emit)
                self._nodes[character] = node
            self._centralWidget.layout().addWidget(self._nodes[character])

        self._centralWidget.layout().addWidget(vspacer())
