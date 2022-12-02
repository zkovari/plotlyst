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
from typing import Optional, List

from overrides import overrides

from src.main.python.plotlyst.core.domain import Character
from src.main.python.plotlyst.core.template import TemplateField, SelectionItem, \
    enneagram_field, traits_field, ProfileTemplate
from src.main.python.plotlyst.view.widget.template.base import TemplateWidgetBase
from src.main.python.plotlyst.view.widget.template.impl import TextSelectionWidget, TraitSelectionWidget
from src.main.python.plotlyst.view.widget.template.profile import ProfileTemplateView


class CharacterProfileTemplateView(ProfileTemplateView):
    def __init__(self, character: Character, profile: ProfileTemplate):
        super().__init__(character.template_values, profile, character.disabled_template_headers)
        self.character = character
        self._required_headers_toggled: bool = False
        self._enneagram_widget: Optional[TextSelectionWidget] = None
        self._traits_widget: Optional[TraitSelectionWidget] = None
        self._goals_widget: Optional[TemplateWidgetBase] = None
        for widget in self.widgets:
            if widget.field.id == enneagram_field.id:
                self._enneagram_widget = widget.wdgEditor
            elif widget.field.id == traits_field.id:
                self._traits_widget = widget.wdgEditor

        if self._enneagram_widget:
            self._enneagram_widget.selectionChanged.connect(self._enneagram_changed)

    def toggleRequiredHeaders(self, toggled: bool):
        if self._required_headers_toggled == toggled:
            return

        self._required_headers_toggled = toggled
        for row, header in self._headers:
            if not header.field.required:
                header.collapse(toggled)
                header.setHidden(toggled)

    @overrides
    def _headerEnabledChanged(self, header: TemplateField, enabled: bool):
        self.character.disabled_template_headers[str(header.id)] = enabled

    def _enneagram_changed(self, previous: Optional[SelectionItem], current: SelectionItem):
        if self._traits_widget:
            traits: List[str] = self._traits_widget.value()
            if previous:
                for pos_trait in previous.meta['positive']:
                    if pos_trait in traits:
                        traits.remove(pos_trait)
                for neg_trait in previous.meta['negative']:
                    if neg_trait in traits:
                        traits.remove(neg_trait)
            for pos_trait in current.meta['positive']:
                if pos_trait not in traits:
                    traits.append(pos_trait)
            for neg_trait in current.meta['negative']:
                if neg_trait not in traits:
                    traits.append(neg_trait)
            self._traits_widget.setValue(traits)
