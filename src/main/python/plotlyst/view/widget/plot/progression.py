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
from functools import partial
from typing import List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QEnterEvent
from PyQt6.QtWidgets import QWidget
from overrides import overrides
from qthandy import vbox, incr_icon, bold, spacer, retain_when_hidden, translucent
from qthandy.filter import VisibilityToggleEventFilter

from src.main.python.plotlyst.core.domain import Novel, PlotType, PlotProgressionItem, \
    PlotProgressionItemType, DynamicPlotPrincipleGroupType, DynamicPlotPrinciple, DynamicPlotPrincipleType, Plot, \
    DynamicPlotPrincipleGroup
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import frame, fade_out_and_gc
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.style.button import apply_button_palette_color
from src.main.python.plotlyst.view.widget.confirm import confirmed
from src.main.python.plotlyst.view.widget.display import IconText
from src.main.python.plotlyst.view.widget.input import RemovalButton
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


class DynamicPlotPrincipleWidget(OutlineItemWidget):
    def __init__(self, principle: DynamicPlotPrinciple, parent=None):
        self.principle = principle
        super().__init__(principle, parent, colorfulShadow=True)
        self._initStyle(name=self.principle.type.display_name(), desc=self.principle.type.placeholder())
        self._btnIcon.setHidden(True)
        self._btnName.setIcon(IconRegistry.from_name(self.principle.type.icon()))
        translucent(self._btnName, 0.7)

    @overrides
    def mimeType(self) -> str:
        return f'application/{self.principle.type.name.lower()}'

    @overrides
    def _color(self) -> str:
        return self.principle.type.color()


class DynamicPlotPrinciplesWidget(OutlineTimelineWidget):
    def __init__(self, group: DynamicPlotPrincipleGroup, parent=None):
        super().__init__(parent, paintTimeline=False)
        self.group = group

    @overrides
    def _newBeatWidget(self, item: DynamicPlotPrinciple) -> OutlineItemWidget:
        wdg = DynamicPlotPrincipleWidget(item)
        wdg.removed.connect(self._beatRemoved)
        return wdg

    @overrides
    def _newPlaceholderWidget(self, displayText: bool = False) -> QWidget:
        wdg = super()._newPlaceholderWidget(displayText)
        if displayText:
            wdg.btn.setText('Insert principle')
        wdg.btn.setToolTip('Insert new principle')
        return wdg

    @overrides
    def _placeholderClicked(self, placeholder: QWidget):
        self._currentPlaceholder = placeholder
        if self.group.type == DynamicPlotPrincipleGroupType.ELEMENTS_OF_WONDER:
            self._insertPrinciple(DynamicPlotPrincipleType.WONDER)
        elif self.group.type == DynamicPlotPrincipleGroupType.EVOLUTION_OF_THE_MONSTER:
            self._insertPrinciple(DynamicPlotPrincipleType.MONSTER)

    def _insertPrinciple(self, principleType: DynamicPlotPrincipleType):
        item = DynamicPlotPrinciple(type=principleType)

        widget = self._newBeatWidget(item)
        self._insertWidget(item, widget)


class DynamicPlotPrinciplesGroupWidget(QWidget):
    remove = pyqtSignal()

    def __init__(self, principleGroup: DynamicPlotPrincipleGroup, parent=None):
        super().__init__(parent)
        self.group = principleGroup
        self.frame = frame()
        self.frame.setObjectName('frame')
        vbox(self.frame, 0, 0)
        self.setStyleSheet(f'''
            #frame {{
                border: 2px solid {self.group.type.color()};
                border-radius: 15px;
            }}''')

        vbox(self)
        self._wdgPrinciples = DynamicPlotPrinciplesWidget(self.group)
        self._wdgPrinciples.setStructure(self.group.principles)

        self._title = IconText()
        self._title.setText(self.group.type.display_name())
        self._title.setIcon(IconRegistry.from_name(self.group.type.icon(), self.group.type.color()))
        incr_icon(self._title, 4)
        bold(self._title)
        apply_button_palette_color(self._title, self.group.type.color())

        self.btnRemove = RemovalButton()
        retain_when_hidden(self.btnRemove)
        self.installEventFilter(VisibilityToggleEventFilter(self.btnRemove, self))
        self.btnRemove.clicked.connect(self.remove)

        self.frame.layout().addWidget(self._wdgPrinciples)
        self.layout().addWidget(group(spacer(), self._title, spacer(), self.btnRemove))
        self.layout().addWidget(self.frame)


class DynamicPlotPrinciplesEditor(QWidget):
    def __init__(self, novel: Novel, plot: Plot, parent=None):
        super().__init__(parent)
        self.novel = novel
        self.plot = plot
        vbox(self, 5, 10)

        for group in self.plot.dynamic_principles:
            self._addGroup(group)

        self.repo = RepositoryPersistenceManager.instance()

    def addGroup(self, groupType: DynamicPlotPrincipleGroupType):
        group = DynamicPlotPrincipleGroup(groupType)
        if groupType == DynamicPlotPrincipleGroupType.ELEMENTS_OF_WONDER:
            group.principles.append(DynamicPlotPrinciple(type=DynamicPlotPrincipleType.WONDER))
        elif groupType == DynamicPlotPrincipleGroupType.EVOLUTION_OF_THE_MONSTER:
            group.principles.append(DynamicPlotPrinciple(type=DynamicPlotPrincipleType.MONSTER))
            group.principles.append(DynamicPlotPrinciple(type=DynamicPlotPrincipleType.MONSTER))
        self.plot.dynamic_principles.append(group)
        self._addGroup(group)
        self._save()

    def _addGroup(self, group: DynamicPlotPrincipleGroup) -> DynamicPlotPrinciplesGroupWidget:
        wdg = DynamicPlotPrinciplesGroupWidget(group)
        wdg.remove.connect(partial(self._removeGroup, wdg))
        self.layout().addWidget(wdg)

        return wdg

    def _removeGroup(self, wdg: DynamicPlotPrinciplesGroupWidget):
        if wdg.group.principles and not confirmed("All principles within will be lost.", "Remove principle group?"):
            return

        self.plot.dynamic_principles.remove(wdg.group)
        fade_out_and_gc(self, wdg)
        self._save()

    def _save(self):
        self.repo.update_novel(self.novel)
