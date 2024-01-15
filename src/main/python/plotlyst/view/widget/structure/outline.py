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
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget
from overrides import overrides

from src.main.python.plotlyst.core.domain import StoryBeat
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.outline import OutlineTimelineWidget, OutlineItemWidget


class StoryStructureBeatWidget(OutlineItemWidget):
    def __init__(self, beat: StoryBeat, parent=None):
        super().__init__(beat, parent)
        self.beat = beat
        self._text.setText(self.beat.notes)
        self._initStyle(name=self.beat.text, desc=self.beat.description)

    @overrides
    def mimeType(self) -> str:
        return ''

    @overrides
    def _color(self) -> str:
        return self.beat.icon_color

    @overrides
    def _icon(self) -> QIcon:
        return IconRegistry.from_name(self.beat.icon, self.beat.icon_color)

    @overrides
    def _textChanged(self):
        self.beat.note = self._text.toPlainText()


class StoryStructureOutline(OutlineTimelineWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    @overrides
    def _newBeatWidget(self, item: StoryBeat) -> StoryStructureBeatWidget:
        widget = StoryStructureBeatWidget(item, parent=self)
        widget.removed.connect(self._beatRemoved)

        return widget

    @overrides
    def _showBeatMenu(self, placeholder: QWidget):
        pass
