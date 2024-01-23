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

from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QEnterEvent
from PyQt6.QtWidgets import QWidget
from overrides import overrides
from qthandy import flow, vbox

from src.main.python.plotlyst.core.domain import Novel, PlotType, PlotProgressionItem, \
    PlotProgressionItemType, DynamicPlotPrincipleGroupType, OutlineItem
from src.main.python.plotlyst.view.common import frame
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.style.button import apply_button_palette_color
from src.main.python.plotlyst.view.widget.display import IconText
from src.main.python.plotlyst.view.widget.outline import OutlineItemWidget, OutlineTimelineWidget

storyline_progression_steps_descriptions = {
    PlotType.Main: {
        PlotProgressionItemType.BEGINNING: 'The initial state of the plot',
        PlotProgressionItemType.MIDDLE: "The middle state of the plot's progression",
        PlotProgressionItemType.ENDING: 'The resolution of the plot',
        PlotProgressionItemType.EVENT: "A progress or setback in the plot"
    },
    PlotType.Internal: {
        PlotProgressionItemType.BEGINNING: "The starting point of the character's change",
        PlotProgressionItemType.MIDDLE: 'The middle stage of the character transformation',
        PlotProgressionItemType.ENDING: 'How the character changed by the end of the story',
        PlotProgressionItemType.EVENT: "A step towards or away from the character's change"
    },
    PlotType.Subplot: {
        PlotProgressionItemType.BEGINNING: 'The initial state of the subplot',
        PlotProgressionItemType.MIDDLE: "The middle state of the subplot's progression",
        PlotProgressionItemType.ENDING: 'The resolution of the subplot',
        PlotProgressionItemType.EVENT: 'A progress or setback in the subplot'
    },
    PlotType.Relation: {
        PlotProgressionItemType.BEGINNING: 'The initial state of the relationship',
        PlotProgressionItemType.MIDDLE: "The middle state of the relationship's evolution",
        PlotProgressionItemType.ENDING: 'The final state of the relationship',
        PlotProgressionItemType.EVENT: 'A change in the relationship where it gets either worse or better'
    },
    PlotType.Global: {
        PlotProgressionItemType.BEGINNING: 'The initial state of the global storyline',
        PlotProgressionItemType.MIDDLE: "The middle state of the global storyline's progression",
        PlotProgressionItemType.ENDING: 'The resolution of the global storyline',
        PlotProgressionItemType.EVENT: "A progress or setback in the global storyline"
    },
}


class PlotProgressionEventWidget(OutlineItemWidget):
    def __init__(self, novel: Novel, type: PlotType, item: PlotProgressionItem, parent=None):
        self._type = type
        self.beat = item
        self.novel = novel
        super().__init__(item, parent)
        self._btnIcon.removeEventFilter(self._dragEventFilter)
        self._btnIcon.setCursor(Qt.CursorShape.ArrowCursor)
        self.setAcceptDrops(False)

        self._initStyle()

    @overrides
    def mimeType(self) -> str:
        return ''

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        if self.beat.type == PlotProgressionItemType.EVENT:
            self._btnRemove.setVisible(True)

    @overrides
    def _descriptions(self) -> dict:
        return storyline_progression_steps_descriptions[self._type]

    @overrides
    def _icon(self) -> QIcon:
        color = self._color()
        if self.beat.type == PlotProgressionItemType.BEGINNING:
            return IconRegistry.cause_icon(color)
        elif self.beat.type == PlotProgressionItemType.MIDDLE:
            return IconRegistry.from_name('mdi.middleware-outline', color)
        elif self.beat.type == PlotProgressionItemType.ENDING:
            return IconRegistry.from_name('mdi.ray-end', color)
        else:
            return IconRegistry.from_name('msc.debug-stackframe-dot', color)

    @overrides
    def _color(self) -> str:
        return 'grey'

    @overrides
    def _initStyle(self):
        name = None
        if self.beat.type == PlotProgressionItemType.ENDING:
            name = 'End'
        elif self.beat.type == PlotProgressionItemType.EVENT:
            name = ''
        super()._initStyle(name=name)


class PlotEventsTimeline(OutlineTimelineWidget):
    def __init__(self, novel: Novel, type: PlotType, parent=None):
        super().__init__(parent)
        self._type = type
        self.setNovel(novel)

    @overrides
    def setStructure(self, items: List[PlotProgressionItem]):
        super().setStructure(items)
        self._hideFirstAndLastItems()

    @overrides
    def _newBeatWidget(self, item: PlotProgressionItem) -> PlotProgressionEventWidget:
        widget = PlotProgressionEventWidget(self._novel, self._type, item, parent=self)
        widget.removed.connect(self._beatRemoved)

        return widget

    @overrides
    def _insertWidget(self, item: PlotProgressionItem, widget: PlotProgressionEventWidget):
        super()._insertWidget(item, widget)
        self._hideFirstAndLastItems()

    @overrides
    def _placeholderClicked(self, placeholder: QWidget):
        self._currentPlaceholder = placeholder
        self._insertBeat(PlotProgressionItemType.EVENT)

    def _insertBeat(self, beatType: PlotProgressionItemType):
        item = PlotProgressionItem(type=beatType)
        widget = self._newBeatWidget(item)
        self._insertWidget(item, widget)

    def _hideFirstAndLastItems(self):
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if i == 0 or i == self.layout().count() - 1:
                item.widget().setVisible(False)
            else:
                item.widget().setVisible(True)


class DynamicPlotPrinciplesWidget(OutlineTimelineWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    @overrides
    def _newBeatWidget(self, item: OutlineItem) -> OutlineItemWidget:
        pass

    @overrides
    def _placeholderClicked(self, placeholder: QWidget):
        pass


class DynamicPlotPrinciplesGroupWidget(QWidget):

    def __init__(self, group: DynamicPlotPrincipleGroupType, parent=None):
        super().__init__(parent)
        self.group = group
        self.frame = frame()
        self.frame.setObjectName('frame')
        vbox(self.frame, 5, 0)
        self.setStyleSheet(f'''
            #frame {{
                border: 1px solid {self.group.color()};
                border-radius: 15px;
            }}''')

        vbox(self)
        self._wdgPrinciples = DynamicPlotPrinciplesWidget()
        self._wdgPrinciples.setStructure([])

        self._title = IconText()
        self._title.setText(group.display_name())
        self._title.setIcon(IconRegistry.from_name(group.icon(), group.color()))
        apply_button_palette_color(self._title, group.color())

        self.frame.layout().addWidget(self._wdgPrinciples)
        self.layout().addWidget(self._title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self.frame)


class DynamicPlotPrinciplesEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        flow(self, 5, 10)

    def addGroup(self, group: DynamicPlotPrincipleGroupType):
        wdg = DynamicPlotPrinciplesGroupWidget(group)
        self.layout().addWidget(wdg)
