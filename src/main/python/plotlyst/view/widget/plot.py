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
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QWidget, QFrame, QWidgetAction, QMenu, QPushButton, QAbstractButton, QTextEdit
from qthandy import gc, bold, flow, incr_font, \
    margins, btn_popup_menu, ask_confirmation, italic, retain_when_hidden, translucent, vbox, transparent, \
    clear_layout, vspacer, underline, decr_font, decr_icon
from qthandy.filter import VisibilityToggleEventFilter, DisabledClickEventFilter

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR, PLOTLYST_SECONDARY_COLOR
from src.main.python.plotlyst.core.domain import Novel, Plot, PlotValue, PlotType, Character, PlotPrinciple, \
    PlotPrincipleType
from src.main.python.plotlyst.core.template import antagonist_role
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import EventListener, Event
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import CharacterChangedEvent, CharacterDeletedEvent
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager, delete_plot
from src.main.python.plotlyst.settings import STORY_LINE_COLOR_CODES
from src.main.python.plotlyst.view.common import action, restyle, pointy, icon_to_html_img, fade_out_and_gc
from src.main.python.plotlyst.view.dialog.novel import PlotValueEditorDialog
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog
from src.main.python.plotlyst.view.generated.plot_editor_widget_ui import Ui_PlotEditor
from src.main.python.plotlyst.view.generated.plot_widget_ui import Ui_PlotWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorButton
from src.main.python.plotlyst.view.widget.labels import PlotValueLabel
from src.main.python.plotlyst.view.widget.list import ListItemWidget
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


principle_hints = {PlotPrincipleType.GOAL: "What's the main goal that drives this plot?",
                   PlotPrincipleType.ANTAGONIST: "Who or what is against achieving that goal?",
                   PlotPrincipleType.CONFLICT: "How the antagonist creates conflict and hinders the goal?",
                   PlotPrincipleType.CONSEQUENCES: "What if the goal won't be achieved? What is at stake?",
                   PlotPrincipleType.PROGRESS: "How the character makes progress and gets closer to accomplishing the goal?",
                   PlotPrincipleType.SETBACK: "How the character gets further away from accomplishing the goal.",
                   PlotPrincipleType.TURNS: "When progress suddenly turns to setback or vice versa.",
                   PlotPrincipleType.CRISIS: "The lowest moment." +
                                             " Often an impossible choice between two equally good or bad outcomes."}


class PlotPrincipleEditor(QWidget):
    principleEdited = pyqtSignal(PlotPrinciple)
    principleSet = pyqtSignal(PlotPrinciple, bool)

    def __init__(self, principle: PlotPrinciple, parent=None):
        super().__init__(parent)
        self._principle = principle

        vbox(self)
        margins(self, bottom=5, top=5)
        self._label = QPushButton()
        transparent(self._label)
        bold(self._label)
        self._label.setText(principle.type.name.lower().capitalize())
        self._label.setIcon(principle_icon(principle.type))
        self._label.setCheckable(True)

        self._textedit = QTextEdit(self)
        hint = principle_hints[principle.type]
        self._textedit.setPlaceholderText(hint)
        self._textedit.setToolTip(hint)
        self._textedit.setText(principle.value)
        self._textedit.setMinimumSize(175, 100)
        self._textedit.setMaximumSize(200, 100)
        self._textedit.textChanged.connect(self._valueChanged)

        self._btnSet = QPushButton('Set', self)
        pointy(self._btnSet)
        self._btnSet.setProperty('base', True)
        self._btnSet.setProperty('highlighted', True)
        self._btnSet.setMinimumWidth(80)
        self._btnSet.setCheckable(True)
        self._btnSet.clicked.connect(self._btnSetClicked)
        self._btnSet.toggled.connect(self._btnSetToggled)
        self._btnSet.setChecked(self._principle.is_set)
        self._checkSetEnabled()
        self._btnSet.installEventFilter(
            DisabledClickEventFilter(self._btnSet, slot=lambda: qtanim.shake(self._textedit)))

        self.layout().addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._textedit)
        self.layout().addWidget(self._btnSet, alignment=Qt.AlignmentFlag.AlignRight)

    def activate(self):
        self._textedit.setFocus()

    def _btnSetClicked(self, toggled: bool):
        self._principle.is_set = toggled
        self.principleSet.emit(self._principle, toggled)
        if toggled and isinstance(self.parent(), QMenu):
            self.parent().hide()

    def _btnSetToggled(self, toggled: bool):
        self._btnSet.setText('Unset' if toggled else 'Set')
        self._btnSet.setProperty('highlighted', not toggled)
        self._btnSet.setProperty('deconstructive', toggled)
        restyle(self._btnSet)
        self._label.setChecked(toggled)

        self._checkSetEnabled()

    def _valueChanged(self):
        self._principle.value = self._textedit.toPlainText()
        self._checkSetEnabled()
        self.principleEdited.emit(self._principle)

    def _checkSetEnabled(self):
        if not self._btnSet.isChecked():
            if self._principle.value:
                self._btnSet.setEnabled(True)
            else:
                self._btnSet.setDisabled(True)


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
        margins(self, top=5, bottom=5)

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
        self.btnArcToggle.setIcon(IconRegistry.rising_action_icon('black', color_on=PLOTLYST_SECONDARY_COLOR))
        decr_icon(self.btnArcToggle)
        # self.textQuestion.setPlainText(self.plot.question)
        # self.textQuestion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.textQuestion.textChanged.connect(self._questionChanged)

        self._initFrameColor()
        for lbl in [self.lblValues, self.lblPrinciples, self.lblProgression]:
            underline(lbl)

        # self.btnGoal.setIcon(principle_icon(PlotPrincipleType.GOAL))
        # self.btnAntagonist.setIcon(principle_icon(PlotPrincipleType.ANTAGONIST))
        # self.btnConflict.setIcon(principle_icon(PlotPrincipleType.CONFLICT))
        # self.btnConsequences.setIcon(principle_icon(PlotPrincipleType.CONSEQUENCES))
        # self.btnProgress.setIcon(principle_icon(PlotPrincipleType.PROGRESS))
        # self.btnSetback.setIcon(principle_icon(PlotPrincipleType.SETBACK))
        # self.btnTurns.setIcon(principle_icon(PlotPrincipleType.TURNS))
        # self.btnCrisis.setIcon(principle_icon(PlotPrincipleType.CRISIS))

        # for btn in self.buttonGroup.buttons():
        #     btn.installEventFilter(OpacityEventFilter(btn, ignoreCheckedButton=True))
        #     btn.installEventFilter(InstantTooltipEventFilter(btn))

        # for principle_type in PlotPrincipleType:
        #     principle = self._principle(principle_type)
        #     btn = self._btnPrinciple(principle_type)
        #     btn.setChecked(principle.is_set)
        #     self._setPrincipleTooltip(btn, principle)
        #
        #     editor = PlotPrincipleEditor(principle, btn)
        #     editor.principleSet.connect(self._principleSet)
        #     editor.principleEdited.connect(self._principleEdited)
        #     menu = btn_popup(btn, editor)
        #     menu.aboutToShow.connect(editor.activate)

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
        self._characterSelector.setGeometry(10, 10, 40, 40)
        character = self.plot.character(novel)
        if character is not None:
            self._characterSelector.setCharacter(character)

        self._characterSelector.characterSelected.connect(self._characterSelected)

        self.wdgValues.layout().addWidget(self._btnAddValue)
        self._btnAddValue.clicked.connect(self._newValue)

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

        # self.btnRemove.clicked.connect(self.removalRequested.emit)

        self.repo = RepositoryPersistenceManager.instance()

        event_dispatcher.register(self, CharacterChangedEvent)
        event_dispatcher.register(self, CharacterDeletedEvent)

    def event_received(self, event: Event):
        if isinstance(event, CharacterDeletedEvent):
            if self.plot.character_id == event.character.id:
                self.plot.reset_character()
                self.repo.update_novel(self.novel)
                self._characterSelector.clear()

    # def _principle(self, principleType: PlotPrincipleType) -> PlotPrinciple:
    #     for principle in self.plot.principles:
    #         if principle.type == principleType:
    #             return principle
    #
    #     principle = PlotPrinciple(principleType, '')
    #     self.plot.principles.append(principle)
    #     return principle

    # def _btnPrinciple(self, principleType: PlotPrincipleType) -> QAbstractButton:
    #     if principleType == PlotPrincipleType.GOAL:
    #         return self.btnGoal
    #     elif principleType == PlotPrincipleType.ANTAGONIST:
    #         return self.btnAntagonist
    #     elif principleType == PlotPrincipleType.CONFLICT:
    #         return self.btnConflict
    #     elif principleType == PlotPrincipleType.CONSEQUENCES:
    #         return self.btnConsequences
    #     elif principleType == PlotPrincipleType.PROGRESS:
    #         return self.btnProgress
    #     elif principleType == PlotPrincipleType.SETBACK:
    #         return self.btnSetback
    #     elif principleType == PlotPrincipleType.TURNS:
    #         return self.btnTurns
    #     elif principleType == PlotPrincipleType.CRISIS:
    #         return self.btnCrisis

    # def _principleSet(self, principle: PlotPrinciple, toggled: bool):
    #     btn = self._btnPrinciple(principle.type)
    #     btn.setChecked(toggled)
    #     if toggled:
    #         qtanim.glow(btn)
    #     else:
    #         translucent(btn, 0.4)
    #     self.repo.update_novel(self.novel)
    #     self._setPrincipleTooltip(btn, principle)

    def _setPrincipleTooltip(self, btn: QAbstractButton, principle: PlotPrinciple):
        tooltip = f'<html><body style="font-size:{btn.font().pointSize() + 2}pt;">'
        tooltip += f'{icon_to_html_img(btn.icon())} {principle.type.name.lower().capitalize()}'

        if principle.is_set:
            tooltip += f'<hr/>{principle.value}'
        btn.setToolTip(tooltip)

    # def _principleEdited(self, principle: PlotPrinciple):
    #     self.repo.update_novel(self.novel)
    #     if principle.is_set:
    #         self._setPrincipleTooltip(self._btnPrinciple(principle.type), principle)

    def _updateIcon(self):
        if self.plot.icon:
            self.btnPlotIcon.setIcon(IconRegistry.from_name(self.plot.icon, self.plot.icon_color))

    def _nameEdited(self, name: str):
        self.plot.text = name
        self.repo.update_novel(self.novel)
        self.titleChanged.emit()

    def _questionChanged(self):
        self.plot.question = self.textQuestion.toPlainText()
        self.repo.update_novel(self.novel)

    def _characterSelected(self, character: Character):
        self.plot.set_character(character)
        self.repo.update_novel(self.novel)

    def _changeIcon(self):
        result = IconSelectorDialog(self).display(QColor(self.plot.icon_color))
        if result:
            self.plot.icon = result[0]
            self.plot.icon_color = result[1].name()
            self._updateIcon()
            self.repo.update_novel(self.novel)
            self.iconChanged.emit()

    def _colorChanged(self, color: QColor):
        self.plot.icon_color = color.name()
        self._updateIcon()
        self._initFrameColor()
        # self.parent().setFrameColor(color)
        self.repo.update_novel(self.novel)
        self.iconChanged.emit()

    def _initFrameColor(self):
        self.setStyleSheet(f'''
            #PlotWidget {{
                background-color: {RELAXED_WHITE_COLOR};
                border: 2px solid {self.plot.icon_color};
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

            self.repo.update_novel(self.novel)

    def _addValue(self, value: PlotValue):
        label = PlotValueLabel(value, parent=self.wdgValues, removalEnabled=True)
        translucent(label)
        self.wdgValues.layout().addWidget(label)
        label.removalRequested.connect(partial(self._removeValue, label))

        self._btnAddValue.setText('')

    def _removeValue(self, widget: PlotValueLabel):
        if app_env.test_env():
            self.__destroyValue(widget)
        else:
            anim = qtanim.fade_out(widget, duration=150, hide_if_finished=False)
            anim.finished.connect(partial(self.__destroyValue, widget))

    def __destroyValue(self, widget: PlotValueLabel):
        self.plot.values.remove(widget.value)
        self.repo.update_novel(self.novel)
        self.wdgValues.layout().removeWidget(widget)
        gc(widget)
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
        menu = QMenu(self.btnAdd)
        menu.addAction(IconRegistry.cause_and_effect_icon(), 'Main plot', lambda: self.newPlot(PlotType.Main))
        menu.addAction(IconRegistry.conflict_self_icon(), 'Internal plot', lambda: self.newPlot(PlotType.Internal))
        menu.addAction(IconRegistry.subplot_icon(), 'Subplot', lambda: self.newPlot(PlotType.Subplot))
        btn_popup_menu(self.btnAdd, menu)

        self.repo = RepositoryPersistenceManager.instance()

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
        pass

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
