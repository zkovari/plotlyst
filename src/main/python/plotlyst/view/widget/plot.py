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

from functools import partial
from typing import Set, Dict, List, Optional

import qtanim
from PyQt6.QtCharts import QSplineSeries, QValueAxis
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QTimer
from PyQt6.QtGui import QColor, QIcon, QPen, QCursor, QEnterEvent, QShowEvent
from PyQt6.QtWidgets import QWidget, QFrame, QPushButton, QTextEdit, QLabel, QGridLayout, QStackedWidget
from overrides import overrides
from qthandy import bold, flow, incr_font, \
    margins, ask_confirmation, italic, retain_when_hidden, vbox, transparent, \
    clear_layout, vspacer, decr_font, decr_icon, hbox, spacer, sp, pointy, incr_icon, translucent, grid, line, vline
from qthandy.filter import VisibilityToggleEventFilter, OpacityEventFilter
from qtmenu import MenuWidget, ActionTooltipDisplayMode, TabularGridMenuWidget

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Novel, Plot, PlotValue, PlotType, Character, PlotPrinciple, \
    PlotPrincipleType, PlotEventType, PlotProgressionItem, \
    PlotProgressionItemType, StorylineLink, StorylineLinkType
from src.main.python.plotlyst.core.template import antagonist_role
from src.main.python.plotlyst.core.text import html
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import EventListener, Event, emit_event
from src.main.python.plotlyst.event.handler import event_dispatchers
from src.main.python.plotlyst.events import CharacterChangedEvent, CharacterDeletedEvent, StorylineCreatedEvent, \
    StorylineRemovedEvent, StorylineCharacterAssociationChanged
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager, delete_plot
from src.main.python.plotlyst.settings import STORY_LINE_COLOR_CODES
from src.main.python.plotlyst.view.common import action, fade_out_and_gc, ButtonPressResizeEventFilter, wrap, \
    insert_before_the_end, shadow, label, tool_btn, push_btn
from src.main.python.plotlyst.view.dialog.novel import PlotValueEditorDialog
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog
from src.main.python.plotlyst.view.generated.plot_editor_widget_ui import Ui_PlotEditor
from src.main.python.plotlyst.view.generated.plot_widget_ui import Ui_PlotWidget
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.style.base import apply_white_menu
from src.main.python.plotlyst.view.widget.button import SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.characters import CharacterAvatar, CharacterSelectorMenu
from src.main.python.plotlyst.view.widget.chart import BaseChart
from src.main.python.plotlyst.view.widget.display import Icon, IdleWidget
from src.main.python.plotlyst.view.widget.input import Toggle
from src.main.python.plotlyst.view.widget.labels import PlotValueLabel
from src.main.python.plotlyst.view.widget.scene.structure import SceneStructureTimeline, SceneStructureBeatWidget
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode
from src.main.python.plotlyst.view.widget.utility import ColorPicker


def principle_icon(type: PlotPrincipleType) -> QIcon:
    if type == PlotPrincipleType.GOAL:
        return IconRegistry.goal_icon('grey')
    elif type == PlotPrincipleType.ANTAGONIST:
        return IconRegistry.from_name(antagonist_role.icon, 'grey', antagonist_role.icon_color)
    elif type == PlotPrincipleType.CONFLICT:
        return IconRegistry.conflict_icon('grey')
    elif type == PlotPrincipleType.STAKES:
        return IconRegistry.from_name('mdi.sack', 'grey', '#e9c46a')
    elif type == PlotPrincipleType.QUESTION:
        return IconRegistry.from_name('ei.question-sign', 'grey', 'darkBlue')
    elif type == PlotPrincipleType.THEME:
        return IconRegistry.theme_icon('grey')

    elif type == PlotPrincipleType.POSITIVE_CHANGE:
        return IconRegistry.from_name('mdi.emoticon-happy', 'grey', '#588157')
    elif type == PlotPrincipleType.NEGATIVE_CHANGE:
        return IconRegistry.from_name('mdi6.emoticon-devil', 'grey', '#c1121f')
    elif type == PlotPrincipleType.DESIRE:
        return IconRegistry.from_name('ei.star-alt', 'grey', '#e9c46a')
    elif type == PlotPrincipleType.NEED:
        return IconRegistry.from_name('mdi.key', 'grey', '#cbc0d3')
    elif type == PlotPrincipleType.EXTERNAL_CONFLICT:
        return IconRegistry.conflict_icon('grey')
    elif type == PlotPrincipleType.INTERNAL_CONFLICT:
        return IconRegistry.conflict_self_icon('grey')
    elif type == PlotPrincipleType.FLAW:
        return IconRegistry.from_name('mdi.virus', 'grey', '#b5179e')

    else:
        return QIcon()


_principle_hints = {
    PlotPrincipleType.GOAL: "Is there a main goal that drives this plot?",
    PlotPrincipleType.ANTAGONIST: "Is there an antagonistic force (human or otherwise) that confronts the plot?",
    PlotPrincipleType.CONFLICT: "Is there conflict that hinders the character's goal?",
    PlotPrincipleType.STAKES: "Is there anything at stake if the storyline is not resolved?",
    PlotPrincipleType.QUESTION: "Is there a major dramatic question associated to this storyline?",
    PlotPrincipleType.THEME: "Is there thematic relevance associated to this storyline?",

    PlotPrincipleType.POSITIVE_CHANGE: "Does the character change positively?",
    PlotPrincipleType.NEGATIVE_CHANGE: "Does the character change negatively?",
    PlotPrincipleType.DESIRE: "Is there an - often wrong - desire that drives the character's decisions?",
    PlotPrincipleType.NEED: "Is there a need that the character does not pursuit yet could solve their problems?",
    PlotPrincipleType.EXTERNAL_CONFLICT: "Are there external obstacles that force the character to change?",
    PlotPrincipleType.INTERNAL_CONFLICT: "Does the character face an internal dilemma?",
    PlotPrincipleType.FLAW: "Is there a major flaw, misbelief, or imperfection the character has to overcome?",
}


def principle_hint(principle_type: PlotPrincipleType, plot_type: PlotType) -> str:
    if plot_type == PlotType.Relation:
        if principle_type == PlotPrincipleType.GOAL:
            return "Is there a shared goal the characters aim for in this relationship plot?"
        if principle_type == PlotPrincipleType.CONFLICT:
            return "Is there any conflict that challenges the relationship?"
        if principle_type == PlotPrincipleType.STAKES:
            return "Is there anything at stake if the characters don't maintain or evolve their relation?"

    return _principle_hints[principle_type]


_principle_placeholders = {
    PlotPrincipleType.GOAL: "What's the main goal that drives this plot?",
    PlotPrincipleType.ANTAGONIST: "Who or what stands in opposition to resolve the storyline?",
    PlotPrincipleType.CONFLICT: "How does conflict hinder the goal?",
    PlotPrincipleType.STAKES: "What's at stake if the storyline is not resolved?",
    PlotPrincipleType.QUESTION: "What is the major dramatic question of this storyline?",
    PlotPrincipleType.THEME: "How does the storyline express the theme?",

    PlotPrincipleType.POSITIVE_CHANGE: "How does the character change positively?",
    PlotPrincipleType.NEGATIVE_CHANGE: "How does the character change negatively?",
    PlotPrincipleType.DESIRE: "What does the character want?",
    PlotPrincipleType.NEED: "What does the character actually need?",
    PlotPrincipleType.EXTERNAL_CONFLICT: "What external obstacles force the character to change?",
    PlotPrincipleType.INTERNAL_CONFLICT: "What internal dilemma of conflict the character has to face?",
    PlotPrincipleType.FLAW: "What kind of flaw the character has to overcome?",
}


def principle_placeholder(principle_type: PlotPrincipleType, plot_type: PlotType) -> str:
    if plot_type == PlotType.Relation:
        if principle_type == PlotPrincipleType.GOAL:
            return "What is a shared goal the characters aim for?"
        if principle_type == PlotPrincipleType.CONFLICT:
            return "How does conflict challenge the relationship?"
        if principle_type == PlotPrincipleType.STAKES:
            return "What's at stake if the characters don't maintain or evolve their relation?"
    return _principle_placeholders[principle_type]


principle_type_index: Dict[PlotPrincipleType, int] = {
    PlotPrincipleType.QUESTION: 0,
    PlotPrincipleType.GOAL: 1,
    PlotPrincipleType.ANTAGONIST: 2,
    PlotPrincipleType.CONFLICT: 3,
    PlotPrincipleType.STAKES: 4,
    PlotPrincipleType.THEME: 5,

    PlotPrincipleType.POSITIVE_CHANGE: 0,
    PlotPrincipleType.NEGATIVE_CHANGE: 1,
    PlotPrincipleType.DESIRE: 2,
    PlotPrincipleType.NEED: 3,
    PlotPrincipleType.EXTERNAL_CONFLICT: 4,
    PlotPrincipleType.INTERNAL_CONFLICT: 5,
    PlotPrincipleType.FLAW: 6,
}


def plot_event_icon(type: PlotEventType) -> QIcon:
    if type == PlotEventType.PROGRESS:
        return IconRegistry.charge_icon(1)
    elif type == PlotEventType.SETBACK:
        return IconRegistry.charge_icon(-1)
    elif type == PlotEventType.CRISIS:
        return IconRegistry.crisis_icon()
    elif type == PlotEventType.COST:
        return IconRegistry.cost_icon()
    elif type == PlotEventType.TOOL:
        return IconRegistry.tool_icon()


plot_event_type_hint = {
    PlotEventType.PROGRESS: 'How does the plot progress and get closer to resolution?',
    PlotEventType.SETBACK: 'How does the plot face conflict and get further from resolution?',
    PlotEventType.CRISIS: "The lowest moment. Often an impossible choice between two equally good or bad outcomes.",
    PlotEventType.COST: 'What does the character need to sacrifice to progress further with the plot?',
    PlotEventType.TOOL: 'What kind of tool does the character acquire which helps them resolve the plot?',
}


class _PlotPrincipleToggle(QWidget):
    def __init__(self, pincipleType: PlotPrincipleType, plotType: PlotType, parent=None):
        super().__init__(parent)
        hbox(self)
        margins(self, bottom=0)
        self._principleType = pincipleType

        self._label = QPushButton()
        transparent(self._label)
        self._label.setCheckable(True)
        bold(self._label)
        self._label.setText(self._principleType.name.lower().capitalize().replace('_', ' '))
        self._label.setToolTip(principle_hint(self._principleType, plotType))
        self._label.setIcon(principle_icon(self._principleType))
        self._label.setCheckable(True)

        self.toggle = Toggle(self)

        self.layout().addWidget(self._label)
        self.layout().addWidget(spacer())
        self.layout().addWidget(self.toggle)

        self.toggle.toggled.connect(self._label.setChecked)


class PlotPrinciplesWidget(QWidget):
    principleToggled = pyqtSignal(PlotPrincipleType, bool)

    def __init__(self, plotType: PlotType, principles: List[PlotPrinciple], parent=None):
        super().__init__(parent)
        self.plotType = plotType

        vbox(self, spacing=0)

        active_types = set([x.type for x in principles])
        if self.plotType == PlotType.Internal:
            principles = [PlotPrincipleType.POSITIVE_CHANGE, PlotPrincipleType.NEGATIVE_CHANGE,
                          PlotPrincipleType.DESIRE, PlotPrincipleType.NEED, PlotPrincipleType.EXTERNAL_CONFLICT,
                          PlotPrincipleType.INTERNAL_CONFLICT, PlotPrincipleType.FLAW]
        elif self.plotType == PlotType.Relation:
            principles = [PlotPrincipleType.QUESTION, PlotPrincipleType.GOAL, PlotPrincipleType.CONFLICT,
                          PlotPrincipleType.STAKES]
        else:
            principles = [PlotPrincipleType.QUESTION, PlotPrincipleType.GOAL, PlotPrincipleType.ANTAGONIST,
                          PlotPrincipleType.CONFLICT,
                          PlotPrincipleType.STAKES, PlotPrincipleType.THEME]

        for principle in principles:
            wdg = _PlotPrincipleToggle(principle, self.plotType)
            if principle in active_types:
                wdg.toggle.setChecked(True)
            wdg.toggle.toggled.connect(partial(self.principleToggled.emit, principle))
            self.layout().addWidget(wdg)
            desc = QLabel(principle_hint(principle, self.plotType))
            desc.setProperty('description', True)
            self.layout().addWidget(wrap(desc, margin_left=10, margin_bottom=5))


class PlotPrincipleSelectorMenu(MenuWidget):
    principleToggled = pyqtSignal(PlotPrincipleType, bool)

    def __init__(self, plot: Plot, parent=None):
        super(PlotPrincipleSelectorMenu, self).__init__(parent)
        self._plot = plot
        apply_white_menu(self)

        self._selectors = PlotPrinciplesWidget(self._plot.plot_type, self._plot.principles)
        self._selectors.principleToggled.connect(self.principleToggled)
        # vbox(self._selectors, spacing=0)

        # active_types = set([x.type for x in self._plot.principles])
        # if self._plot.plot_type == PlotType.Internal:
        #     principles = [PlotPrincipleType.POSITIVE_CHANGE, PlotPrincipleType.NEGATIVE_CHANGE,
        #                   PlotPrincipleType.DESIRE, PlotPrincipleType.NEED, PlotPrincipleType.EXTERNAL_CONFLICT,
        #                   PlotPrincipleType.INTERNAL_CONFLICT, PlotPrincipleType.FLAW]
        # elif self._plot.plot_type == PlotType.Relation:
        #     principles = [PlotPrincipleType.QUESTION, PlotPrincipleType.GOAL, PlotPrincipleType.CONFLICT,
        #                   PlotPrincipleType.STAKES]
        # else:
        #     principles = [PlotPrincipleType.QUESTION, PlotPrincipleType.GOAL, PlotPrincipleType.ANTAGONIST,
        #                   PlotPrincipleType.CONFLICT,
        #                   PlotPrincipleType.STAKES, PlotPrincipleType.THEME]
        #
        # for principle in principles:
        #     wdg = _PlotPrincipleToggle(principle, self._plot.plot_type)
        #     if principle in active_types:
        #         wdg.toggle.setChecked(True)
        #     wdg.toggle.toggled.connect(partial(self.principleToggled.emit, principle))
        #     self._selectors.layout().addWidget(wdg)
        #     desc = QLabel(principle_hint(principle, self._plot.plot_type))
        #     desc.setProperty('description', True)
        #     self._selectors.layout().addWidget(wrap(desc, margin_left=10, margin_bottom=5))

        self.addSection('Select principles that are relevant to this storyline')
        self.addSeparator()
        self.addWidget(self._selectors)


class PlotPrincipleEditor(QWidget):
    principleEdited = pyqtSignal()

    def __init__(self, principle: PlotPrinciple, plotType: PlotType, parent=None):
        super().__init__(parent)
        self._principle = principle

        vbox(self)
        self._label = QPushButton()
        transparent(self._label)
        bold(self._label)
        self._label.setText(principle.type.name.lower().capitalize().replace('_', ' '))
        self._label.setIcon(principle_icon(principle.type))
        self._label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._label.setCheckable(True)
        self._label.setChecked(True)

        self._textedit = QTextEdit(self)
        self._textedit.setProperty('white-bg', True)
        self._textedit.setProperty('rounded', True)
        hint = principle_placeholder(principle.type, plotType)
        self._textedit.setPlaceholderText(hint)
        self._textedit.setToolTip(hint)
        self._textedit.setTabChangesFocus(True)
        if app_env.is_mac():
            incr_font(self._textedit)
        self._textedit.setText(principle.value)
        self._textedit.setMinimumSize(175, 100)
        self._textedit.setMaximumSize(190, 120)
        self._textedit.verticalScrollBar().setVisible(False)
        shadow(self._textedit)
        self._textedit.textChanged.connect(self._valueChanged)

        self.layout().addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._textedit)

    def activate(self):
        self._textedit.setFocus()

    def principle(self) -> PlotPrinciple:
        return self._principle

    def _valueChanged(self):
        self._principle.value = self._textedit.toPlainText()
        self.principleEdited.emit()


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


class PlotProgressionEventWidget(SceneStructureBeatWidget):
    def __init__(self, novel: Novel, type: PlotType, item: PlotProgressionItem, parent=None):
        self._type = type
        super().__init__(novel, item, parent)
        self._btnIcon.removeEventFilter(self._dragEventFilter)
        self._btnIcon.setCursor(Qt.CursorShape.ArrowCursor)
        self.setAcceptDrops(False)

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
        super()._initStyle()
        if self.beat.type == PlotProgressionItemType.ENDING:
            self._btnName.setText('End')
        elif self.beat.type == PlotProgressionItemType.EVENT:
            self._btnName.setText('')


class PlotEventsTimeline(SceneStructureTimeline):
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

    # @overrides
    # def _addBeatWidget(self, item: PlotProgressionItem):
    #     super()._addBeatWidget(item)

    @overrides
    def _insertWidget(self, item: PlotProgressionItem, widget: PlotProgressionEventWidget):
        super()._insertWidget(item, widget)
        self._hideFirstAndLastItems()

    @overrides
    def _showBeatMenu(self, placeholder: QWidget):
        self._currentPlaceholder = placeholder
        self._insertBeat(PlotProgressionItemType.EVENT)

    @overrides
    def _insertBeat(self, beatType: PlotProgressionItemType):
        item = PlotProgressionItem(beatType)
        widget = self._newBeatWidget(item)
        self._insertWidget(item, widget)

    def _hideFirstAndLastItems(self):
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if i == 0 or i == self.layout().count() - 1:
                item.widget().setVisible(False)
            else:
                item.widget().setVisible(True)


class PlotNode(ContainerNode):
    def __init__(self, plot: Plot, parent=None):
        super(PlotNode, self).__init__(plot.text, parent)
        self._plot = plot
        self.setPlusButtonEnabled(False)
        incr_font(self._lblTitle)
        margins(self._wdgTitle, top=5, bottom=5)

        self.refresh()

    def plot(self) -> Plot:
        return self._plot

    def refresh(self):
        if self._plot.icon:
            self._icon.setIcon(IconRegistry.from_name(self._plot.icon, self._plot.icon_color))
            self._icon.setVisible(True)
        else:
            self._icon.setHidden(True)

        self._lblTitle.setText(self._plot.text)


class PlotEventsArcChart(BaseChart):
    MAX: int = 4
    MIN: int = -4

    def __init__(self, plot: Plot, parent=None):
        super(PlotEventsArcChart, self).__init__(parent)
        self._plot = plot
        self.setTitle(html('Arc preview').bold())

    def refresh(self):
        self.reset()

        if not self._plot.events:
            return

        series = QSplineSeries()
        pen = QPen()
        pen.setWidth(2)
        pen.setColor(QColor(self._plot.icon_color))
        series.setPen(pen)
        arc_value: int = 0
        series.append(0, 0)
        for event in self._plot.events:
            if event.type in [PlotEventType.PROGRESS, PlotEventType.TOOL] and arc_value < self.MAX:
                arc_value += 1
            elif event.type in [PlotEventType.SETBACK, PlotEventType.COST] and arc_value > self.MIN:
                arc_value -= 1
            elif event.type == PlotEventType.CRISIS and arc_value > self.MIN + 1:
                arc_value -= 2
            series.append(len(series), arc_value)

        axis = QValueAxis()
        axis.setRange(self.MIN, self.MAX)
        self.addSeries(series)
        self.addAxis(axis, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis)
        axis.setVisible(False)


class PlotTreeView(TreeView, EventListener):
    plotSelected = pyqtSignal(Plot)
    plotRemoved = pyqtSignal(Plot)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._plots: Dict[Plot, PlotNode] = {}
        self._characterNodes: Dict[Character, ContainerNode] = {}
        self._selectedPlots: Set[Plot] = set()

        self.refresh()

        event_dispatchers.instance(self._novel).register(self, StorylineCharacterAssociationChanged)

    @overrides
    def event_received(self, event: Event):
        self.refresh()

    def refresh(self):
        self._selectedPlots.clear()
        self._characterNodes.clear()
        self._plots.clear()
        clear_layout(self._centralWidget)

        characters = [x.character(self._novel) for x in self._novel.plots if x.character_id]
        characters_set = set(characters)
        characters_set.discard(None)
        if len(characters_set) > 1:
            for character in characters:
                if character in self._characterNodes.keys():
                    continue
                self._characterNodes[character] = ContainerNode(character.name, avatars.avatar(character),
                                                                readOnly=True)
                self._centralWidget.layout().addWidget(self._characterNodes[character])

        for plot in self._novel.plots:
            wdg = self.__initPlotWidget(plot)
            if plot.character_id and self._characterNodes:
                character = plot.character(self._novel)
                self._characterNodes[character].addChild(wdg)
            else:
                self._centralWidget.layout().addWidget(wdg)

        self._centralWidget.layout().addWidget(vspacer())

    def refreshPlot(self, plot: Plot):
        self._plots[plot].refresh()

    def refreshCharacters(self):
        self.refresh()

    def addPlot(self, plot: Plot):
        wdg = self.__initPlotWidget(plot)
        self._centralWidget.layout().insertWidget(self._centralWidget.layout().count() - 1, wdg)

    def selectPlot(self, plot: Plot):
        self._plots[plot].select()
        wdg = self._plots[plot]
        self._plotSelectionChanged(wdg, wdg.isSelected())

    def removePlot(self, plot: Plot):
        self._removePlot(self._plots[plot])

    def clearSelection(self):
        for plot in self._selectedPlots:
            self._plots[plot].deselect()
        self._selectedPlots.clear()

    def _plotSelectionChanged(self, wdg: PlotNode, selected: bool):
        if selected:
            self.clearSelection()
            self._selectedPlots.add(wdg.plot())
            QTimer.singleShot(10, lambda: self.plotSelected.emit(wdg.plot()))
        elif wdg.plot() in self._selectedPlots:
            self._selectedPlots.remove(wdg.plot())

    def _removePlot(self, wdg: PlotNode):
        plot = wdg.plot()
        if not ask_confirmation(f"Delete plot '{plot.text}'?", self._centralWidget):
            return
        if plot in self._selectedPlots:
            self._selectedPlots.remove(plot)
        self._plots.pop(plot)

        characterNode = None
        if plot.character_id and self._characterNodes:
            character = plot.character(self._novel)
            characterNode = self._characterNodes[character]
            if len(characterNode.childrenWidgets()) == 1:
                self._characterNodes.pop(character)  # remove parent too
            else:
                characterNode = None  # keep parent

        fade_out_and_gc(wdg.parent(), wdg)
        if characterNode:
            fade_out_and_gc(self._centralWidget, characterNode)

        self.plotRemoved.emit(wdg.plot())

    def __initPlotWidget(self, plot: Plot) -> PlotNode:
        if plot not in self._plots.keys():
            wdg = PlotNode(plot)
            wdg.selectionChanged.connect(partial(self._plotSelectionChanged, wdg))
            wdg.deleted.connect(partial(self._removePlot, wdg))
            self._plots[plot] = wdg

        return self._plots[plot]


class PlotWidget(QFrame, Ui_PlotWidget, EventListener):
    titleChanged = pyqtSignal()
    iconChanged = pyqtSignal()
    characterChanged = pyqtSignal()
    removalRequested = pyqtSignal()

    def __init__(self, novel: Novel, plot: Plot, parent=None):
        super(PlotWidget, self).__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.plot: Plot = plot

        incr_font(self.lineName, 6)
        bold(self.lineName)
        self.lineName.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineName.setText(self.plot.text)
        self.lineName.textChanged.connect(self._nameEdited)

        self.btnPincipleEditor.setIcon(IconRegistry.plus_edit_icon('grey'))
        transparent(self.btnPincipleEditor)
        retain_when_hidden(self.btnPincipleEditor)
        decr_icon(self.btnPincipleEditor)

        self._principleSelectorMenu = PlotPrincipleSelectorMenu(self.plot, self.btnPincipleEditor)
        self._principleSelectorMenu.principleToggled.connect(self._principleToggled)
        self.btnPincipleEditor.installEventFilter(ButtonPressResizeEventFilter(self.btnPincipleEditor))
        self.btnPincipleEditor.installEventFilter(OpacityEventFilter(self.btnPincipleEditor, leaveOpacity=0.7))
        self._principles: Dict[PlotPrincipleType, PlotPrincipleEditor] = {}

        self._initFrameColor()
        self.btnPrinciples.setIcon(IconRegistry.from_name('mdi6.note-text-outline', 'grey'))
        incr_icon(self.btnPrinciples, 2)
        incr_font(self.btnPrinciples, 2)
        self.btnPrinciples.installEventFilter(ButtonPressResizeEventFilter(self.btnPrinciples))
        self.btnPrinciples.installEventFilter(OpacityEventFilter(self.btnPrinciples, leaveOpacity=0.7))
        self.btnPrinciples.clicked.connect(lambda: self._principleSelectorMenu.exec())

        flow(self.wdgPrinciples, spacing=6)
        margins(self.wdgPrinciples, left=30)
        for principle in self.plot.principles:
            self._initPrincipleEditor(principle)

        self.btnProgression.setIcon(IconRegistry.rising_action_icon('grey'))
        if self.plot.plot_type == PlotType.Internal:
            self.btnProgression.setText('Transformation')
        elif self.plot.plot_type == PlotType.Relation:
            self.btnProgression.setText('Evolution')

        translucent(self.btnProgression, 0.7)
        incr_icon(self.btnProgression, 2)
        incr_font(self.btnProgression, 2)

        self.btnValues.setText('' if self.plot.values else 'Values')
        self.btnValues.setIcon(IconRegistry.from_name('fa5s.chevron-circle-down', 'grey'))
        self.btnValues.installEventFilter(OpacityEventFilter(self.btnValues, 0.9, 0.7))
        self.btnValues.clicked.connect(self._newValue)
        hbox(self.wdgValues)
        self._btnAddValue = SecondaryActionPushButton(self)
        self._btnAddValue.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        decr_font(self._btnAddValue)
        self._btnAddValue.setIconSize(QSize(14, 14))
        retain_when_hidden(self._btnAddValue)
        self._btnAddValue.setIcon(IconRegistry.plus_icon('grey'))
        for value in self.plot.values:
            self._addValue(value)

        self.btnRelationArrow.setHidden(True)
        self._characterRelationSelector: Optional[CharacterAvatar] = None
        if self.plot.plot_type == PlotType.Global:
            pass
        elif self.plot.plot_type == PlotType.Relation:
            self.btnRelationArrow.setVisible(True)
            self.btnRelationArrow.setIcon(IconRegistry.from_name('ph.arrows-counter-clockwise-fill'))
            self.btnPlotIcon.setIconSize(QSize(32, 32))

            self._characterSelector = CharacterAvatar(self, 60, 100, 64, 8)
            self._characterRelationSelector = CharacterAvatar(self, 60, 100, 64, 8)
            self._characterSelector.setToolTip('Associate a character to this relationship plot')
            self._characterRelationSelector.setToolTip('Associate a character to this relationship plot')
            sourceMenu = CharacterSelectorMenu(self.novel, self._characterSelector.btnAvatar)
            sourceMenu.selected.connect(self._characterSelected)
            targetMenu = CharacterSelectorMenu(self.novel, self._characterRelationSelector.btnAvatar)
            targetMenu.selected.connect(self._relationCharacterSelected)
            self._characterSelector.setFixedSize(90, 90)
            self._characterRelationSelector.setFixedSize(90, 90)
            self.wdgHeader.layout().insertWidget(0, self._characterSelector,
                                                 alignment=Qt.AlignmentFlag.AlignCenter)
            self.wdgHeader.layout().insertWidget(0, spacer())
            self.wdgHeader.layout().addWidget(self._characterRelationSelector, alignment=Qt.AlignmentFlag.AlignCenter)
            self.wdgHeader.layout().addWidget(spacer())

            character = self.plot.character(novel)
            if character is not None:
                self._characterSelector.setCharacter(character)
            character = self.plot.relation_character(novel)
            if character is not None:
                self._characterRelationSelector.setCharacter(character)
        else:
            self._characterSelector = CharacterAvatar(self, 88, 120, 92, 8)
            menu = CharacterSelectorMenu(self.novel, self._characterSelector.btnAvatar)
            menu.selected.connect(self._characterSelected)
            self._characterSelector.setToolTip('Link character to this storyline')
            self._characterSelector.setGeometry(20, 20, 115, 115)
            character = self.plot.character(novel)
            if character is not None:
                self._characterSelector.setCharacter(character)

        self.wdgValues.layout().addWidget(self._btnAddValue)
        self.wdgValues.layout().addWidget(spacer())
        self._btnAddValue.clicked.connect(self._newValue)

        self.installEventFilter(VisibilityToggleEventFilter(target=self.btnSettings, parent=self))
        self.installEventFilter(VisibilityToggleEventFilter(target=self._btnAddValue, parent=self))
        self.installEventFilter(VisibilityToggleEventFilter(target=self.btnPincipleEditor, parent=self))

        self.btnPlotIcon.installEventFilter(OpacityEventFilter(self.btnPlotIcon, enterOpacity=0.7, leaveOpacity=1.0))
        self._updateIcon()

        self._timeline = PlotEventsTimeline(self.novel, self.plot.plot_type)
        self.wdgEventsParent.layout().addWidget(self._timeline)
        self._timeline.setStructure(self.plot.progression)
        self._timeline.timelineChanged.connect(self._timelineChanged)

        iconMenu = MenuWidget(self.btnPlotIcon)

        colorPicker = ColorPicker(self)
        colorPicker.setFixedSize(300, 150)
        colorPicker.colorPicked.connect(self._colorChanged)
        colorMenu = MenuWidget()
        colorMenu.setTitle('Color')
        colorMenu.setIcon(IconRegistry.from_name('fa5s.palette'))
        colorMenu.addWidget(colorPicker)

        iconMenu.addMenu(colorMenu)
        iconMenu.addSeparator()
        iconMenu.addAction(
            action('Change icon', icon=IconRegistry.icons_icon(), slot=self._changeIcon, parent=iconMenu))

        contextMenu = MenuWidget(self.btnSettings)
        progress_action = action('Track general progress',
                                 slot=self._trackGeneralProgressChanged,
                                 checkable=True,
                                 tooltip='Enable tracking a general progression value besides the custom plot values',
                                 parent=contextMenu)
        progress_action.setChecked(self.plot.default_value_enabled)
        contextMenu.addAction(progress_action)
        contextMenu.addSeparator()
        contextMenu.addAction(action('Remove plot', IconRegistry.trash_can_icon(), self.removalRequested.emit))

        self.repo = RepositoryPersistenceManager.instance()

        dispatcher = event_dispatchers.instance(self.novel)
        dispatcher.register(self, CharacterChangedEvent, CharacterDeletedEvent)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, CharacterDeletedEvent):
            if self._characterSelector.character() and self._characterSelector.character().id == event.character.id:
                self._characterSelector.reset()
            if self._characterRelationSelector and self._characterRelationSelector.character() and self._characterRelationSelector.character().id == event.character.id:
                self._characterRelationSelector.reset()

    def _updateIcon(self):
        if self.plot.icon:
            self.btnPlotIcon.setIcon(IconRegistry.from_name(self.plot.icon, self.plot.icon_color))

    def _nameEdited(self, name: str):
        self.plot.text = name
        self._save()
        self.titleChanged.emit()

    def _characterSelected(self, character: Character):
        self._characterSelector.setCharacter(character)
        self.plot.set_character(character)
        self._save()
        self.characterChanged.emit()

    def _relationCharacterSelected(self, character: Character):
        self._characterRelationSelector.setCharacter(character)
        self.plot.set_relation_character(character)
        self._save()

    def _changeIcon(self):
        result = IconSelectorDialog(self).display(QColor(self.plot.icon_color))
        if result:
            self.plot.icon = result[0]
            self._colorChanged(result[1])

    def _colorChanged(self, color: QColor):
        self.plot.icon_color = color.name()
        self._updateIcon()
        self._initFrameColor()
        self._save()
        self.iconChanged.emit()

    def _trackGeneralProgressChanged(self, toggled: bool):
        self.plot.default_value_enabled = toggled
        self._save()

    def _principleToggled(self, principleType: PlotPrincipleType, toggled: bool):
        if toggled:
            principle = PlotPrinciple(principleType)
            self._initPrincipleEditor(principle)
            self.plot.principles.append(principle)
        else:
            principle = next((_principle for _principle in self.plot.principles if _principle.type == principleType),
                             None)
            if principle:
                self.plot.principles.remove(principle)
                wdg = self._principles.pop(principle.type)
                fade_out_and_gc(self.wdgPrinciples, wdg)

        self._btnAddValue.setVisible(True)
        self.btnSettings.setVisible(True)
        self.btnPincipleEditor.setVisible(True)

        self._save()

    def _initPrincipleEditor(self, principle: PlotPrinciple):
        editor = PlotPrincipleEditor(principle, self.plot.plot_type)
        editor.principleEdited.connect(self._save)
        self.wdgPrinciples.layout().insertWidget(principle_type_index[principle.type], editor)
        self._principles[principle.type] = editor

        return editor

    def _save(self):
        self.repo.update_novel(self.novel)

    def _timelineChanged(self):
        self._save()

    def _initFrameColor(self):
        self.setStyleSheet(f'''
            #PlotWidget {{
                background-color: {RELAXED_WHITE_COLOR};
                border: 2px solid {self.plot.icon_color};
            }}
            #scrollAreaWidgetContents {{
                background-color: {RELAXED_WHITE_COLOR};
            }}
            #frame {{
                border: 1px solid {self.plot.icon_color};
            }}
        ''')

    def _newValue(self):
        value = PlotValueEditorDialog().display()
        if value:
            self.plot.values.append(value)
            self.wdgValues.layout().removeWidget(self._btnAddValue)
            self._addValue(value)
            self.wdgValues.layout().addWidget(self._btnAddValue)

            self._save()

    def _addValue(self, value: PlotValue):
        label = PlotValueLabel(value, parent=self.wdgValues, simplified=True)
        sp(label).h_max()
        label.installEventFilter(OpacityEventFilter(label, leaveOpacity=0.7))
        pointy(label)
        insert_before_the_end(self.wdgValues, label)
        label.removalRequested.connect(partial(self._removeValue, label))
        label.clicked.connect(partial(self._plotValueClicked, label))

        self.btnValues.setText('')

    def _removeValue(self, label: PlotValueLabel):
        if app_env.test_env():
            self.__destroyValue(label)
        else:
            anim = qtanim.fade_out(label, duration=150, hide_if_finished=False)
            anim.finished.connect(partial(self.__destroyValue, label))

    def _editValue(self, label: PlotValueLabel):
        value = PlotValueEditorDialog().display(label.value)
        if value:
            label.value.text = value.text
            label.value.negative = value.negative
            label.value.icon = value.icon
            label.value.icon_color = value.icon_color
            label.refresh()
            self._save()

    def _plotValueClicked(self, label: PlotValueLabel):
        menu = MenuWidget()
        menu.addAction(action('Edit', IconRegistry.edit_icon(), partial(self._editValue, label)))
        menu.addSeparator()
        menu.addAction(action('Remove', IconRegistry.trash_can_icon(), label.removalRequested.emit))
        menu.exec(QCursor.pos())

    def __destroyValue(self, label: PlotValueLabel):
        self.plot.values.remove(label.value)
        self._save()
        fade_out_and_gc(self.wdgValues, label)
        self.btnValues.setText('' if self.plot.values else 'Values')


class PlotEditor(QWidget, Ui_PlotEditor):
    def __init__(self, novel: Novel, parent=None):
        super(PlotEditor, self).__init__(parent)
        self.setupUi(self)
        self.novel = novel

        self._wdgList = PlotTreeView(self.novel)
        self.wdgPlotListParent.layout().addWidget(self._wdgList)
        self._wdgList.plotSelected.connect(self._plotSelected)
        self._wdgList.plotRemoved.connect(self._plotRemoved)
        self.stack.setCurrentWidget(self.pageDisplay)

        self._wdgImpactMatrix = StorylinesImpactMatrix(self.novel)
        self.scrollMatrix.layout().addWidget(self._wdgImpactMatrix)

        self.splitter.setSizes([150, 550])

        italic(self.btnAdd)
        self.btnAdd.setIcon(IconRegistry.plus_icon('white'))
        self.btnImpactMatrix.setIcon(IconRegistry.from_name('mdi6.camera-metering-matrix'))
        self.btnImpactMatrix.clicked.connect(self._displayImpactMatrix)

        menu = MenuWidget(self.btnAdd)
        menu.addAction(action('Main plot', IconRegistry.storylines_icon(), lambda: self.newPlot(PlotType.Main)))
        menu.addAction(
            action('Character arc', IconRegistry.conflict_self_icon(), lambda: self.newPlot(PlotType.Internal)))
        menu.addAction(action('Subplot', IconRegistry.subplot_icon(), lambda: self.newPlot(PlotType.Subplot)))

        submenu = MenuWidget()
        submenu.setTitle('Other')
        submenu.addAction(action('Relationship plot', IconRegistry.from_name('fa5s.people-arrows'),
                                 slot=lambda: self.newPlot(PlotType.Relation)))
        submenu.addAction(action('Global storyline', IconRegistry.from_name('fa5s.globe'),
                                 slot=lambda: self.newPlot(PlotType.Global)))
        menu.addSeparator()
        menu.addMenu(submenu)

        self.repo = RepositoryPersistenceManager.instance()

        if self.novel.plots:
            self._wdgList.selectPlot(self.novel.plots[0])

    def widgetList(self) -> PlotTreeView:
        return self._wdgList

    def newPlot(self, plot_type: PlotType):
        if plot_type == PlotType.Internal:
            name = 'Character arc'
            icon = 'mdi.mirror'
        elif plot_type == PlotType.Subplot:
            name = 'Subplot'
            icon = 'mdi.source-branch'
        elif plot_type == PlotType.Relation:
            name = 'Relationship'
            icon = 'fa5s.people-arrows'
        elif plot_type == PlotType.Global:
            name = 'Global storyline'
            icon = 'fa5s.globe'
        else:
            name = 'Main plot'
            icon = 'fa5s.theater-masks'
        plot = Plot(name, plot_type=plot_type, icon=icon,
                    progression=[PlotProgressionItem(PlotProgressionItemType.BEGINNING),
                                 PlotProgressionItem(PlotProgressionItemType.MIDDLE),
                                 PlotProgressionItem(PlotProgressionItemType.ENDING)])
        self.novel.plots.append(plot)

        plot_colors = list(STORY_LINE_COLOR_CODES[plot_type.value])
        for plot in self.novel.plots:
            if plot.plot_type == plot_type and plot.icon_color in plot_colors:
                plot_colors.remove(plot.icon_color)
        if plot_colors:
            plot.icon_color = plot_colors[0]
        else:
            plot_colors = STORY_LINE_COLOR_CODES[plot_type.value]
            number_of_plots = len([x for x in self.novel.plots if x.plot_type == plot_type])
            plot.icon_color = plot_colors[(number_of_plots - 1) % len(plot_colors)]

        self._wdgList.addPlot(plot)
        self.repo.update_novel(self.novel)
        self._wdgList.selectPlot(plot)
        self._wdgImpactMatrix.refresh()

        emit_event(self.novel, StorylineCreatedEvent(self))

    def _plotSelected(self, plot: Plot) -> PlotWidget:
        self.btnImpactMatrix.setChecked(False)
        self.stack.setCurrentWidget(self.pageDisplay)

        widget = PlotWidget(self.novel, plot, self.pageDisplay)
        widget.removalRequested.connect(partial(self._remove, widget))
        widget.titleChanged.connect(partial(self._wdgList.refreshPlot, widget.plot))
        widget.iconChanged.connect(partial(self._wdgList.refreshPlot, widget.plot))
        widget.characterChanged.connect(self._wdgList.refreshCharacters)

        clear_layout(self.pageDisplay)
        self.pageDisplay.layout().addWidget(widget)

        return widget

    def _remove(self, wdg: PlotWidget):
        self._wdgList.removePlot(wdg.plot)

    def _plotRemoved(self, plot: Plot):
        if self.pageDisplay.layout().count():
            item = self.pageDisplay.layout().itemAt(0)
            if item.widget() and isinstance(item.widget(), PlotWidget):
                if item.widget().plot == plot:
                    clear_layout(self.pageDisplay)
        delete_plot(self.novel, plot)

        self._wdgImpactMatrix.refresh()
        emit_event(self.novel, StorylineRemovedEvent(self, plot))

    # def _remove(self, widget: PlotWidget):
    #     if ask_confirmation(f'Are you sure you want to delete the plot {widget.plot.text}?'):
    #         if app_env.test_env():
    #             self.__destroy(widget)
    #         else:
    #             anim = qtanim.fade_out(widget, duration=150)
    #             anim.finished.connect(partial(self.__destroy, widget))
    #
    # def __destroy(self, widget: PlotWidget):
    #     delete_plot(self.novel, widget.plot)
    #     self.scrollAreaWidgetContents.layout().removeWidget(widget.parent())

    def _displayImpactMatrix(self, checked: bool):
        self._wdgList.clearSelection()
        if checked:
            self.stack.setCurrentWidget(self.pageMatrix)
        else:
            self.stack.setCurrentWidget(self.pageDisplay)


class StorylineHeaderWidget(QWidget):
    def __init__(self, storyline: Plot, parent=None):
        super().__init__(parent)
        self._storyline = storyline

        vbox(self, 5)
        self._icon = Icon()
        self._lbl = label(storyline.text, wordWrap=True)
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setMaximumWidth(220)

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        self._lbl.setText(self._storyline.text)
        self._icon.setIcon(IconRegistry.from_name(self._storyline.icon, self._storyline.icon_color))


class StorylinesConnectionWidget(QWidget):
    linked = pyqtSignal()
    linkChanged = pyqtSignal()
    unlinked = pyqtSignal()

    def __init__(self, source: Plot, target: Plot, parent=None):
        super().__init__(parent)
        self._source = source
        self._target = target
        self._link: Optional[StorylineLink] = None

        self.stack = QStackedWidget()
        self._wdgActive = QWidget()
        self._wdgDefault = QWidget()
        self.stack.addWidget(self._wdgActive)
        self.stack.addWidget(self._wdgDefault)

        self._btnLink = tool_btn(IconRegistry.from_name('fa5s.link'), transparent_=True)
        self._btnLink.setIconSize(QSize(32, 32))
        self._btnLink.installEventFilter(OpacityEventFilter(self._btnLink))
        self._btnLink.clicked.connect(self._linkClicked)
        self._btnLink.setHidden(True)
        vbox(self._wdgDefault)
        self._wdgDefault.layout().addWidget(self._btnLink, alignment=Qt.AlignmentFlag.AlignCenter)
        self._wdgDefault.installEventFilter(VisibilityToggleEventFilter(self._btnLink, self._wdgDefault))

        self._icon = push_btn(properties=['transparent', 'no-menu'])
        self._text = QTextEdit()
        self._text.setProperty('rounded', True)
        self._text.setProperty('white-bg', True)
        self._text.setMinimumSize(175, 100)
        self._text.setMaximumSize(200, 120)
        self._text.verticalScrollBar().setVisible(False)
        self._text.textChanged.connect(self._textChanged)
        vbox(self._wdgActive)
        self._wdgActive.layout().addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignCenter)
        self._wdgActive.layout().addWidget(self._text, alignment=Qt.AlignmentFlag.AlignCenter)

        self._plotTypes = (PlotType.Main, PlotType.Subplot)

        self._menu = MenuWidget(self._icon)
        self._menu.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
        self._menu.addSection('Connection type')
        self._menu.addSeparator()
        self._addAction(StorylineLinkType.Catalyst)
        self._addAction(StorylineLinkType.Impact)
        self._addAction(StorylineLinkType.Contrast)

        if self._source.plot_type in self._plotTypes:
            if self._target.plot_type in self._plotTypes:
                self._addAction(StorylineLinkType.Compete)

        elif self._source.plot_type == PlotType.Internal:
            if self._target.plot_type in self._plotTypes:
                self._addAction(StorylineLinkType.Resolve)
            elif self._target.plot_type == PlotType.Relation:
                self._addAction(StorylineLinkType.Reveal)
        elif self._source.plot_type == PlotType.Relation:
            if self._target.plot_type == PlotType.Internal:
                self._addAction(StorylineLinkType.Reflect_char)
            elif self._target.plot_type != PlotType.Relation:
                self._addAction(StorylineLinkType.Reflect_plot)

        self._menu.addSeparator()
        self._menu.addAction(
            action('Remove', IconRegistry.trash_can_icon(), tooltip='Remove connection', slot=self._remove))

        self.stack.setCurrentWidget(self._wdgDefault)

        vbox(self, 0, 0)
        self.layout().addWidget(self.stack)

        sp(self).h_max().v_max()

    def activate(self):
        QTimer.singleShot(10, self._menu.exec)

    def setLink(self, link: StorylineLink):
        self._link = None
        self._text.setText(link.text)
        self._link = link
        self._updateType()
        self.stack.setCurrentWidget(self._wdgActive)

    def _linkClicked(self):
        link = StorylineLink(self._source.id, self._target.id, StorylineLinkType.Connection)
        self._source.links.append(link)

        self.setLink(link)
        qtanim.fade_in(self._wdgActive, teardown=self.activate)

    def _typeChanged(self, type: StorylineLinkType):
        self._link.type = type
        self._updateType()
        self.linkChanged.emit()

    def _textChanged(self):
        if self._link:
            self._link.text = self._text.toPlainText()
            self.linkChanged.emit()

    def _updateType(self):
        self._icon.setIcon(IconRegistry.from_name(self._link.type.icon()))
        self._icon.setText(self._link.type.name)
        self._icon.setToolTip(self._link.type.desc())
        self._text.setPlaceholderText(self._link.type.desc())

    def _remove(self):
        self._source.links.remove(self._link)
        self._link = None
        self._text.clear()
        self.stack.setCurrentWidget(self._wdgDefault)
        self.unlinked.emit()

    def _addAction(self, type: StorylineLinkType):
        self._menu.addAction(action(type.name, IconRegistry.from_name(type.icon())
                                    , tooltip=type.desc(), slot=partial(self._typeChanged, type)))


class StorylinesImpactMatrix(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._refreshOnShown = True

        self._grid: QGridLayout = grid(self)
        self.repo = RepositoryPersistenceManager.instance()

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        if self._refreshOnShown:
            self._refreshMatrix()
            self._refreshOnShown = False

    def refresh(self):
        if self.isVisible():
            self._refreshMatrix()
        else:
            self._refreshOnShown = True

    def _refreshMatrix(self):
        clear_layout(self)

        for i, storyline in enumerate(self._novel.plots):
            refs: Dict[str, StorylineLink] = {}
            for ref in storyline.links:
                refs[str(ref.target_id)] = ref

            header = StorylineHeaderWidget(storyline)
            self._grid.addWidget(header, 0, i + 1, alignment=Qt.AlignmentFlag.AlignCenter)

            row = StorylineHeaderWidget(storyline)
            row.setMinimumHeight(70)
            self._grid.addWidget(row, i + 1, 0, alignment=Qt.AlignmentFlag.AlignVCenter)

            self._grid.addWidget(self._emptyCellWidget(), i + 1, i + 1)

            for j, ref_storyline in enumerate(self._novel.plots):
                if storyline is ref_storyline:
                    continue
                wdg = StorylinesConnectionWidget(storyline, ref_storyline)
                wdg.linked.connect(self._save)
                wdg.linkChanged.connect(self._save)
                wdg.unlinked.connect(self._save)
                if str(ref_storyline.id) in refs.keys():
                    wdg.setLink(refs[str(ref_storyline.id)])
                self._grid.addWidget(wdg, i + 1, j + 1)

        self._grid.addWidget(line(), 0, 1, 1, len(self._novel.plots), alignment=Qt.AlignmentFlag.AlignBottom)
        self._grid.addWidget(vline(), 1, 0, len(self._novel.plots), 1, alignment=Qt.AlignmentFlag.AlignRight)
        self._grid.addWidget(spacer(), 0, len(self._novel.plots) + 1)

        self._grid.addWidget(vspacer(), len(self._novel.plots) + 1, 0)

    def _emptyCellWidget(self) -> QWidget:
        wdg = IdleWidget()
        wdg.setMinimumSize(50, 50)

        return wdg

    def _save(self):
        self.repo.update_novel(self._novel)


class StorylineSelectorMenu(MenuWidget):
    storylineSelected = pyqtSignal(Plot)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._filters: Dict[PlotType, bool] = {
            PlotType.Global: True,
            PlotType.Main: True,
            PlotType.Internal: True,
            PlotType.Subplot: True,
            PlotType.Relation: False,
        }
        self.aboutToShow.connect(self._beforeShow)

    def filterPlotType(self, plotType: PlotType, filtered: bool):
        self._filters[plotType] = filtered

    def filterAll(self, filtered: bool):
        for k in self._filters.keys():
            self._filters[k] = filtered

    def _beforeShow(self):
        self.clear()
        for plot in self._novel.plots:
            if not self._filters[plot.plot_type]:
                continue
            action_ = action(plot.text, IconRegistry.from_name(plot.icon, plot.icon_color),
                             partial(self.storylineSelected.emit, plot))
            self.addAction(action_)
        if not self.actions():
            self.addSection('No corresponding storylines were found')
