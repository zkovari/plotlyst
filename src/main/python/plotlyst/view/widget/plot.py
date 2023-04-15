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
from typing import Set, Dict

import qtanim
from PyQt6.QtCharts import QSplineSeries, QValueAxis
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QColor, QIcon, QPen, QCursor
from PyQt6.QtWidgets import QWidget, QFrame, QWidgetAction, QMenu, QPushButton, QTextEdit
from overrides import overrides
from qthandy import bold, flow, incr_font, \
    margins, btn_popup_menu, ask_confirmation, italic, retain_when_hidden, vbox, transparent, \
    clear_layout, vspacer, underline, decr_font, decr_icon, hbox, spacer, sp
from qthandy.filter import VisibilityToggleEventFilter, ObjectReferenceMimeData, OpacityEventFilter
from qtmenu import MenuWidget, ActionTooltipDisplayMode

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR, PLOTLYST_SECONDARY_COLOR
from src.main.python.plotlyst.core.domain import Novel, Plot, PlotValue, PlotType, Character, PlotPrinciple, \
    PlotPrincipleType, PlotEvent, PlotEventType
from src.main.python.plotlyst.core.template import antagonist_role
from src.main.python.plotlyst.core.text import html
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import EventListener, Event
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import CharacterChangedEvent, CharacterDeletedEvent
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager, delete_plot
from src.main.python.plotlyst.settings import STORY_LINE_COLOR_CODES
from src.main.python.plotlyst.view.common import action, fade_out_and_gc, pointy
from src.main.python.plotlyst.view.dialog.novel import PlotValueEditorDialog
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog
from src.main.python.plotlyst.view.generated.plot_editor_widget_ui import Ui_PlotEditor
from src.main.python.plotlyst.view.generated.plot_widget_ui import Ui_PlotWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorButton
from src.main.python.plotlyst.view.widget.chart import BaseChart
from src.main.python.plotlyst.view.widget.display import Icon
from src.main.python.plotlyst.view.widget.input import Toggle
from src.main.python.plotlyst.view.widget.labels import PlotValueLabel
from src.main.python.plotlyst.view.widget.list import ListItemWidget, ListView
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode
from src.main.python.plotlyst.view.widget.utility import ColorPicker


def principle_icon(type: PlotPrincipleType) -> QIcon:
    if type == PlotPrincipleType.GOAL:
        return IconRegistry.goal_icon('grey')
    elif type == PlotPrincipleType.ANTAGONIST:
        return IconRegistry.from_name(antagonist_role.icon, 'grey', antagonist_role.icon_color)
    elif type == PlotPrincipleType.CONFLICT:
        return IconRegistry.conflict_icon('grey')
    elif type == PlotPrincipleType.CONSEQUENCES:
        return IconRegistry.cause_and_effect_icon('grey', '#3a5a40')
    elif type == PlotPrincipleType.PROGRESS:
        return IconRegistry.rising_action_icon('grey', '#0096c7')
    elif type == PlotPrincipleType.SETBACK:
        return IconRegistry.from_name('mdi6.slope-downhill', 'grey', '#ae2012')
    elif type == PlotPrincipleType.TURNS:
        return IconRegistry.from_name('mdi.boom-gate-up-outline', 'grey', '#8338ec')
    elif type == PlotPrincipleType.CRISIS:
        return IconRegistry.crisis_icon('grey')
    elif type == PlotPrincipleType.STAKES:
        return IconRegistry.from_name('mdi.sack', 'grey', '#e9c46a')
    elif type == PlotPrincipleType.QUESTION:
        return IconRegistry.from_name('ei.question-sign', 'grey', 'darkBlue')
    elif type == PlotPrincipleType.THEME:
        return IconRegistry.theme_icon('grey')


principle_hints = {PlotPrincipleType.GOAL: "What's the main goal that drives this plot?",
                   PlotPrincipleType.ANTAGONIST: "Who or what is against achieving that goal?",
                   PlotPrincipleType.CONFLICT: "How the antagonist creates conflict and hinders the goal?",
                   PlotPrincipleType.CONSEQUENCES: "What if the goal won't be achieved? What is at stake?",
                   PlotPrincipleType.PROGRESS: "How the character makes progress and gets closer to accomplishing the goal?",
                   PlotPrincipleType.SETBACK: "How the character gets further away from accomplishing the goal.",
                   PlotPrincipleType.TURNS: "When progress suddenly turns to setback or vice versa.",
                   PlotPrincipleType.CRISIS: "The lowest moment." +
                                             " Often an impossible choice between two equally good or bad outcomes.",
                   PlotPrincipleType.STAKES: "What's at stake if the plot goal is not accomplished?",
                   PlotPrincipleType.QUESTION: "What is the main dramatic question of this plot?",
                   PlotPrincipleType.THEME: "How does this plot express the theme?",
                   }

principle_type_index: Dict[PlotPrincipleType, int] = {
    PlotPrincipleType.QUESTION: 0,
    PlotPrincipleType.GOAL: 1,
    PlotPrincipleType.ANTAGONIST: 2,
    PlotPrincipleType.CONFLICT: 3,
    PlotPrincipleType.STAKES: 4,
    PlotPrincipleType.THEME: 5,
}


def plot_event_icon(type: PlotEventType) -> QIcon:
    if type == PlotEventType.PROGRESS:
        return IconRegistry.charge_icon(1)
    elif type == PlotEventType.SETBACK:
        return IconRegistry.charge_icon(-1)
    elif type == PlotEventType.CRISIS:
        return IconRegistry.crisis_icon()
    elif type == PlotEventType.COST:
        return IconRegistry.from_name('ph.coin-bold', '#e9c46a')
    elif type == PlotEventType.TOOL:
        return IconRegistry.from_name('fa5s.hammer', '#d4a373')


plot_event_type_hint = {
    PlotEventType.PROGRESS: 'How does the plot progress and get closer to resolution?',
    PlotEventType.SETBACK: 'How does the plot face conflict and get further from resolution?',
    PlotEventType.CRISIS: "The lowest moment. Often an impossible choice between two equally good or bad outcomes.",
    PlotEventType.COST: 'What does the character need to sacrifice to progress further with the plot?',
    PlotEventType.TOOL: 'What kind of tool does the character acquire which helps them resolve the plot?',
}


class _PlotPrincipleToggle(QWidget):
    def __init__(self, pincipleType: PlotPrincipleType, parent=None):
        super(_PlotPrincipleToggle, self).__init__(parent)
        hbox(self)
        self._principleType = pincipleType

        self._label = QPushButton()
        transparent(self._label)
        self._label.setCheckable(True)
        bold(self._label)
        self._label.setText(self._principleType.name.lower().capitalize())
        self._label.setToolTip(principle_hints[self._principleType])
        self._label.setIcon(principle_icon(self._principleType))
        self._label.setCheckable(True)

        self.toggle = Toggle(self)

        self.layout().addWidget(self._label)
        self.layout().addWidget(spacer())
        self.layout().addWidget(self.toggle)

        self.toggle.toggled.connect(self._label.setChecked)


class PlotPrincipleSelectorMenu(QMenu):
    principleToggled = pyqtSignal(PlotPrincipleType, bool)

    def __init__(self, plot: Plot, parent=None):
        super(PlotPrincipleSelectorMenu, self).__init__(parent)
        self._plot = plot

        self._selector = QWidget()
        vbox(self._selector)

        active_types = set([x.type for x in self._plot.principles])

        for principle in [PlotPrincipleType.QUESTION, PlotPrincipleType.GOAL, PlotPrincipleType.ANTAGONIST,
                          PlotPrincipleType.CONFLICT,
                          PlotPrincipleType.STAKES, PlotPrincipleType.THEME]:
            wdg = _PlotPrincipleToggle(principle)
            if principle in active_types:
                wdg.toggle.setChecked(True)
            wdg.toggle.toggled.connect(partial(self.principleToggled.emit, principle))
            self._selector.layout().addWidget(wdg)

        action = QWidgetAction(self)
        action.setDefaultWidget(self._selector)
        self.addAction(action)


class PlotPrincipleEditor(QWidget):
    principleEdited = pyqtSignal()

    def __init__(self, principle: PlotPrinciple, parent=None):
        super().__init__(parent)
        self._principle = principle

        vbox(self)
        self._label = QPushButton()
        transparent(self._label)
        bold(self._label)
        self._label.setText(principle.type.name.lower().capitalize())
        self._label.setIcon(principle_icon(principle.type))
        self._label.setCheckable(True)
        self._label.setChecked(True)

        self._textedit = QTextEdit(self)
        hint = principle_hints[principle.type]
        self._textedit.setPlaceholderText(hint)
        self._textedit.setToolTip(hint)
        self._textedit.setText(principle.value)
        self._textedit.setMinimumSize(175, 100)
        self._textedit.setMaximumSize(200, 100)
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


class PlotListItemWidget(ListItemWidget):
    def __init__(self, plot: Plot, parent=None):
        super(PlotListItemWidget, self).__init__(parent)
        self._plot = plot
        self._lineEdit.setReadOnly(True)
        self.refresh()

    def refresh(self):
        self._lineEdit.setText(self._plot.text)


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


class PlotEventItem(ListItemWidget):
    def __init__(self, event: PlotEvent, parent=None):
        super(PlotEventItem, self).__init__(event, parent)
        self._event = event
        self._lineEdit.setMaximumWidth(800)
        hint = plot_event_type_hint[event.type]
        self._lineEdit.setPlaceholderText(hint)
        self._lineEdit.setToolTip(hint)
        _spacer = spacer()
        sp(_spacer).h_preferred()
        self.layout().addWidget(_spacer)
        margins(self, right=15)

        self._icon = Icon()
        self._icon.setIcon(plot_event_icon(event.type))
        self._icon.setToolTip(hint)
        self.layout().insertWidget(1, self._icon)
        self.refresh()

    def refresh(self):
        self._lineEdit.setText(self._event.text)

    @overrides
    def _textChanged(self, text: str):
        super(PlotEventItem, self)._textChanged(text)
        self._event.text = text


class PlotEventSelectorMenu(MenuWidget):
    eventSelected = pyqtSignal(PlotEventType)

    def __init__(self, parent=None):
        super(PlotEventSelectorMenu, self).__init__(parent)
        self.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)

        for type_ in PlotEventType:
            action_ = action(type_.name.lower().capitalize(), plot_event_icon(type_),
                             partial(self.eventSelected.emit, type_))
            action_.setToolTip(plot_event_type_hint[type_])
            self.addAction(action_)


class PlotEventsList(ListView):
    eventsChanged = pyqtSignal()

    def __init__(self, plot: Plot, parent=None):
        super(PlotEventsList, self).__init__(parent)
        self._plot = plot
        self._btnAdd.setText('Add new event')
        self._btnAdd.setToolTip('Add new event to reflect how the plot will progress or face setback')

        menu = PlotEventSelectorMenu(self._btnAdd)
        menu.eventSelected.connect(self._addNewItem)

        for event in self._plot.events:
            self.addItem(event)

    @overrides
    def _addNewItem(self, eventType: PlotEventType):
        event = PlotEvent('', type=eventType)
        self._plot.events.append(event)
        self.addItem(event)

        self.eventsChanged.emit()

    @overrides
    def _listItemWidgetClass(self):
        return PlotEventItem

    @overrides
    def _deleteItemWidget(self, widget: ListItemWidget):
        super(PlotEventsList, self)._deleteItemWidget(widget)
        self._plot.events.remove(widget.item())
        self.eventsChanged.emit()

    @overrides
    def _dropped(self, mimeData: ObjectReferenceMimeData):
        super(PlotEventsList, self)._dropped(mimeData)
        self._plot.events[:] = [x.item() for x in self.widgets()]

        self.eventsChanged.emit()


class PlotList(TreeView):
    plotSelected = pyqtSignal(Plot)
    plotRemoved = pyqtSignal(Plot)

    def __init__(self, novel: Novel, parent=None):
        super(PlotList, self).__init__(parent)
        self._novel = novel
        self._plots: Dict[Plot, PlotNode] = {}
        self._selectedPlots: Set[Plot] = set()

        self.refresh()

    def refresh(self):
        clear_layout(self._centralWidget, auto_delete=False)

        for plot in self._novel.plots:
            wdg = self.__initPlotWidget(plot)
            self._centralWidget.layout().addWidget(wdg)

        self._centralWidget.layout().addWidget(vspacer())

    def refreshPlot(self, plot: Plot):
        self._plots[plot].refresh()

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
            self.plotSelected.emit(wdg.plot())
        elif wdg.plot() in self._selectedPlots:
            self._selectedPlots.remove(wdg.plot())

    def _removePlot(self, wdg: PlotNode):
        plot = wdg.plot()
        if not ask_confirmation(f"Delete plot '{plot.text}'?", self._centralWidget):
            return
        if plot in self._selectedPlots:
            self._selectedPlots.remove(plot)
        self._plots.pop(plot)

        fade_out_and_gc(wdg.parent(), wdg)

        self.plotRemoved.emit(wdg.plot())

    def __initPlotWidget(self, plot: Plot) -> PlotNode:
        wdg = PlotNode(plot)
        wdg.selectionChanged.connect(partial(self._plotSelectionChanged, wdg))
        wdg.deleted.connect(partial(self._removePlot, wdg))

        self._plots[plot] = wdg
        return wdg


class PlotWidget(QFrame, Ui_PlotWidget, EventListener):
    titleChanged = pyqtSignal()
    iconChanged = pyqtSignal()
    removalRequested = pyqtSignal()

    def __init__(self, novel: Novel, plot: Plot, parent=None):
        super(PlotWidget, self).__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.plot = plot

        incr_font(self.lineName, 2)
        bold(self.lineName)
        self.lineName.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineName.setText(self.plot.text)
        self.lineName.textChanged.connect(self._nameEdited)
        self.btnPincipleEditor.setIcon(IconRegistry.plus_edit_icon())
        retain_when_hidden(self.btnPincipleEditor)
        decr_icon(self.btnPincipleEditor)
        self.btnArcToggle.setIcon(IconRegistry.rising_action_icon('black', color_on=PLOTLYST_SECONDARY_COLOR))
        decr_icon(self.btnArcToggle)

        self.splitter.setSizes([300, 300])

        self._principleSelectorMenu = PlotPrincipleSelectorMenu(self.plot, self.btnPincipleEditor)
        self._principleSelectorMenu.principleToggled.connect(self._principleToggled)
        btn_popup_menu(self.btnPincipleEditor, self._principleSelectorMenu)
        self._principles: Dict[PlotPrincipleType, PlotPrincipleEditor] = {}

        self._initFrameColor()
        for lbl in [self.lblValues, self.lblPrinciples, self.lblProgression]:
            underline(lbl)

        flow(self.wdgPrinciples)
        for principle in self.plot.principles:
            # TODO remove later
            if principle.type in [PlotPrincipleType.TURNS, PlotPrincipleType.CRISIS, PlotPrincipleType.PROGRESS,
                                  PlotPrincipleType.SETBACK, PlotPrincipleType.CONSEQUENCES]:
                continue
            self._initPrincipleEditor(principle)

        flow(self.wdgValues)
        self._btnAddValue = SecondaryActionPushButton(self)
        decr_font(self._btnAddValue)
        self._btnAddValue.setIconSize(QSize(14, 14))
        self._btnAddValue.setText('' if self.plot.values else 'Attach story value')
        retain_when_hidden(self._btnAddValue)
        self._btnAddValue.setIcon(IconRegistry.plus_icon('grey'))
        for value in self.plot.values:
            self._addValue(value)

        self._characterSelector = CharacterSelectorButton(novel, self)
        self._characterSelector.setToolTip('Link character to this plot')
        self._characterSelector.setGeometry(10, 10, 40, 40)
        character = self.plot.character(novel)
        if character is not None:
            self._characterSelector.setCharacter(character)

        self._characterSelector.characterSelected.connect(self._characterSelected)

        self.wdgValues.layout().addWidget(self._btnAddValue)
        self._btnAddValue.clicked.connect(self._newValue)

        self._lstEvents = PlotEventsList(self.plot)
        self._lstEvents.centralWidget().setStyleSheet(f'.QWidget {{background-color: {RELAXED_WHITE_COLOR};}}')
        self._lstEvents.eventsChanged.connect(self._eventsChanged)
        self.wdgEventsParent.layout().addWidget(self._lstEvents)

        self._arcChart = PlotEventsArcChart(self.plot)
        self.chartViewArcPreview.setChart(self._arcChart)
        self._arcChart.refresh()

        self.installEventFilter(VisibilityToggleEventFilter(target=self.btnSettings, parent=self))
        self.installEventFilter(VisibilityToggleEventFilter(target=self._btnAddValue, parent=self))
        self.installEventFilter(VisibilityToggleEventFilter(target=self.btnPincipleEditor, parent=self))

        self._updateIcon()

        iconMenu = QMenu(self.btnPlotIcon)

        colorAction = QWidgetAction(iconMenu)
        colorPicker = ColorPicker(self)
        colorPicker.setFixedSize(300, 150)
        colorPicker.colorPicked.connect(self._colorChanged)
        colorAction.setDefaultWidget(colorPicker)
        colorMenu = QMenu('Color', iconMenu)
        colorMenu.setIcon(IconRegistry.from_name('fa5s.palette'))
        colorMenu.addAction(colorAction)

        iconMenu.addMenu(colorMenu)
        iconMenu.addSeparator()
        iconMenu.addAction(
            action('Change icon', icon=IconRegistry.icons_icon(), slot=self._changeIcon, parent=iconMenu))
        btn_popup_menu(self.btnPlotIcon, iconMenu)

        contextMenu = QMenu()
        contextMenu.addMenu(colorMenu)
        contextMenu.addSeparator()
        contextMenu.addAction(IconRegistry.trash_can_icon(), 'Remove plot', self.removalRequested.emit)
        btn_popup_menu(self.btnSettings, contextMenu)

        self.repo = RepositoryPersistenceManager.instance()

        event_dispatcher.register(self, CharacterChangedEvent)
        event_dispatcher.register(self, CharacterDeletedEvent)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, CharacterDeletedEvent):
            if self.plot.character_id == event.character.id:
                self.plot.reset_character()
                self._save()
                self._characterSelector.clear()

    def _updateIcon(self):
        if self.plot.icon:
            self.btnPlotIcon.setIcon(IconRegistry.from_name(self.plot.icon, self.plot.icon_color))

    def _nameEdited(self, name: str):
        self.plot.text = name
        self._save()
        self.titleChanged.emit()

    def _characterSelected(self, character: Character):
        self.plot.set_character(character)
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
        self._arcChart.refresh()
        self._save()
        self.iconChanged.emit()

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

        self._save()

    def _initPrincipleEditor(self, principle: PlotPrinciple):
        editor = PlotPrincipleEditor(principle)
        editor.principleEdited.connect(self._save)
        self.wdgPrinciples.layout().insertWidget(principle_type_index[principle.type], editor)
        self._principles[principle.type] = editor

        return editor

    def _save(self):
        self.repo.update_novel(self.novel)

    def _eventsChanged(self):
        self._arcChart.refresh()
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
        label = PlotValueLabel(value, parent=self.wdgValues)
        label.installEventFilter(OpacityEventFilter(label, leaveOpacity=0.7))
        pointy(label)
        self.wdgValues.layout().addWidget(label)
        label.removalRequested.connect(partial(self._removeValue, label))
        label.clicked.connect(partial(self._plotValueClicked, label))

        self._btnAddValue.setText('')

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
        menu = QMenu(label)
        menu.addAction(IconRegistry.edit_icon(), 'Edit', partial(self._editValue, label))
        menu.addSeparator()
        menu.addAction(IconRegistry.trash_can_icon(), 'Remove', label.removalRequested.emit)
        menu.popup(QCursor.pos())

    def __destroyValue(self, label: PlotValueLabel):
        self.plot.values.remove(label.value)
        self._save()
        fade_out_and_gc(self.wdgValues, label)
        has_values = len(self.plot.values) > 0
        self._btnAddValue.setText('' if has_values else 'Attach story value')


class PlotEditor(QWidget, Ui_PlotEditor):
    def __init__(self, novel: Novel, parent=None):
        super(PlotEditor, self).__init__(parent)
        self.setupUi(self)
        self.novel = novel

        self._wdgList = PlotList(self.novel)
        self.wdgPlotListParent.layout().addWidget(self._wdgList)
        self._wdgList.plotSelected.connect(self._plotSelected)
        self._wdgList.plotRemoved.connect(self._plotRemoved)
        self.stack.setCurrentWidget(self.pageDisplay)

        self.splitter.setSizes([150, 550])

        italic(self.btnAdd)
        self.btnAdd.setIcon(IconRegistry.plus_icon('white'))
        menu = MenuWidget(self.btnAdd)
        menu.addAction(action('Main plot', IconRegistry.cause_and_effect_icon(), lambda: self.newPlot(PlotType.Main)))
        menu.addAction(
            action('Internal plot', IconRegistry.conflict_self_icon(), lambda: self.newPlot(PlotType.Internal)))
        menu.addAction(action('Subplot', IconRegistry.subplot_icon(), lambda: self.newPlot(PlotType.Subplot)))

        self.repo = RepositoryPersistenceManager.instance()

    def widgetList(self) -> PlotList:
        return self._wdgList

    def newPlot(self, plot_type: PlotType):
        if plot_type == PlotType.Internal:
            name = 'Internal plot'
            icon = 'mdi.mirror'
        elif plot_type == PlotType.Subplot:
            name = 'Subplot'
            icon = 'mdi.source-branch'
        else:
            name = 'Main plot'
            icon = 'mdi.ray-start-arrow'
        plot = Plot(name, plot_type=plot_type, icon=icon)
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

    def _plotSelected(self, plot: Plot) -> PlotWidget:
        widget = PlotWidget(self.novel, plot, self.pageDisplay)
        widget.removalRequested.connect(partial(self._remove, widget))
        widget.titleChanged.connect(partial(self._wdgList.refreshPlot, widget.plot))
        widget.iconChanged.connect(partial(self._wdgList.refreshPlot, widget.plot))

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
