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

from functools import partial

import qtanim
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QWidget, QFrame, QWidgetAction, QMenu, QPushButton, QAbstractButton, QTextEdit
from qtframes import Frame
from qthandy import gc, bold, flow, incr_font, \
    margins, btn_popup_menu, ask_confirmation, italic, retain_when_hidden, translucent, btn_popup, vbox, transparent
from qthandy.filter import VisibilityToggleEventFilter, OpacityEventFilter, InstantTooltipEventFilter, \
    DisabledClickEventFilter

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Novel, Plot, PlotValue, PlotType, Character, PlotPrinciple, \
    PlotPrincipleType
from src.main.python.plotlyst.core.template import antagonist_role
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import EventListener, Event
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import CharacterChangedEvent, CharacterDeletedEvent
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager, delete_plot
from src.main.python.plotlyst.settings import STORY_LINE_COLOR_CODES
from src.main.python.plotlyst.view.common import action, restyle, pointy
from src.main.python.plotlyst.view.dialog.novel import PlotValueEditorDialog
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog
from src.main.python.plotlyst.view.generated.plot_editor_widget_ui import Ui_PlotEditor
from src.main.python.plotlyst.view.generated.plot_widget_ui import Ui_PlotWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorButton
from src.main.python.plotlyst.view.widget.labels import PlotValueLabel
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


class PlotPrincipleEditor(QWidget):
    principleEdited = pyqtSignal(PlotPrinciple)
    principleSet = pyqtSignal(PlotPrinciple, bool)

    def __init__(self, principle: PlotPrinciple, parent=None):
        super().__init__(parent)
        self._principle = principle

        vbox(self)
        margins(self, bottom=5)
        self._label = QPushButton()
        transparent(self._label)
        bold(self._label)
        self._label.setText(principle.type.name.lower().capitalize())
        self._label.setIcon(principle_icon(principle.type))
        self._label.setCheckable(True)

        self._textedit = QTextEdit(self)
        self._textedit.setText(principle.value)
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


class PlotWidget(QFrame, Ui_PlotWidget, EventListener):
    removalRequested = pyqtSignal()

    def __init__(self, novel: Novel, plot: Plot, parent=None):
        super(PlotWidget, self).__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.plot = plot

        incr_font(self.lineName)
        bold(self.lineName)
        self.lineName.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineName.setText(self.plot.text)
        self.lineName.textChanged.connect(self._nameEdited)
        self.textQuestion.setPlainText(self.plot.question)
        self.textQuestion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.textQuestion.textChanged.connect(self._questionChanged)
        retain_when_hidden(self.btnRemove)

        self.btnGoal.setIcon(principle_icon(PlotPrincipleType.GOAL))
        self.btnAntagonist.setIcon(principle_icon(PlotPrincipleType.ANTAGONIST))
        self.btnConflict.setIcon(principle_icon(PlotPrincipleType.CONFLICT))
        self.btnConsequences.setIcon(principle_icon(PlotPrincipleType.CONSEQUENCES))
        self.btnProgress.setIcon(principle_icon(PlotPrincipleType.PROGRESS))
        self.btnSetback.setIcon(principle_icon(PlotPrincipleType.SETBACK))
        self.btnTurns.setIcon(principle_icon(PlotPrincipleType.TURNS))
        self.btnCrisis.setIcon(principle_icon(PlotPrincipleType.CRISIS))

        for btn in self.buttonGroup.buttons():
            btn.installEventFilter(OpacityEventFilter(btn, ignoreCheckedButton=True))
            btn.installEventFilter(InstantTooltipEventFilter(btn))

        for principle_type in PlotPrincipleType:
            principle = self._principle(principle_type)
            btn = self._btnPrinciple(principle_type)
            btn.setChecked(principle.is_set)
            if principle.is_set:
                self._setPrincipleTooltip(btn, principle)

            editor = PlotPrincipleEditor(principle, btn)
            editor.principleSet.connect(self._principleSet)
            editor.principleEdited.connect(self._principleEdited)
            menu = btn_popup(btn, editor)
            menu.aboutToShow.connect(editor.activate)

        flow(self.wdgValues)
        self._btnAddValue = SecondaryActionPushButton(self)
        self._btnAddValue.setIconSize(QSize(14, 14))
        self._btnAddValue.setText('' if self.plot.values else 'Attach story value')
        retain_when_hidden(self._btnAddValue)
        self._btnAddValue.setIcon(IconRegistry.plus_icon('grey'))
        for value in self.plot.values:
            self._addValue(value)

        self._characterSelector = CharacterSelectorButton(self)
        self._characterSelector.setGeometry(5, 5, 40, 40)
        self._characterSelector.setAvailableCharacters(novel.characters)
        character = self.plot.character(novel)
        if character is not None:
            self._characterSelector.setCharacter(character)

        self._characterSelector.characterSelected.connect(self._characterSelected)

        self.wdgValues.layout().addWidget(self._btnAddValue)
        self._btnAddValue.clicked.connect(self._newValue)

        self.installEventFilter(VisibilityToggleEventFilter(target=self.btnRemove, parent=self))
        self.installEventFilter(VisibilityToggleEventFilter(target=self._btnAddValue, parent=self))

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

        self.btnRemove.clicked.connect(self.removalRequested.emit)

        self.repo = RepositoryPersistenceManager.instance()

        event_dispatcher.register(self, CharacterChangedEvent)
        event_dispatcher.register(self, CharacterDeletedEvent)

    def event_received(self, event: Event):
        self._characterSelector.setAvailableCharacters(self.novel.characters)
        if isinstance(event, CharacterDeletedEvent):
            if self.plot.character_id == event.character.id:
                self.plot.reset_character()
                self.repo.update_novel(self.novel)
                self._characterSelector.clear()

    def _principle(self, principleType: PlotPrincipleType) -> PlotPrinciple:
        for principle in self.plot.principles:
            if principle.type == principleType:
                return principle

        principle = PlotPrinciple(principleType, '')
        self.plot.principles.append(principle)
        return principle

    def _btnPrinciple(self, principleType: PlotPrincipleType) -> QAbstractButton:
        if principleType == PlotPrincipleType.GOAL:
            return self.btnGoal
        elif principleType == PlotPrincipleType.ANTAGONIST:
            return self.btnAntagonist
        elif principleType == PlotPrincipleType.CONFLICT:
            return self.btnConflict
        elif principleType == PlotPrincipleType.CONSEQUENCES:
            return self.btnConsequences
        elif principleType == PlotPrincipleType.PROGRESS:
            return self.btnProgress
        elif principleType == PlotPrincipleType.SETBACK:
            return self.btnSetback
        elif principleType == PlotPrincipleType.TURNS:
            return self.btnTurns
        elif principleType == PlotPrincipleType.CRISIS:
            return self.btnCrisis

    def _principleSet(self, principle: PlotPrinciple, toggled: bool):
        btn = self._btnPrinciple(principle.type)
        btn.setChecked(toggled)
        if toggled:
            qtanim.glow(btn)
        else:
            translucent(btn, 0.4)
        self.repo.update_novel(self.novel)
        self._setPrincipleTooltip(btn, principle)

    def _setPrincipleTooltip(self, btn: QAbstractButton, principle: PlotPrinciple):
        if principle.is_set:
            btn.setToolTip(f'<html>{principle.type.name.lower().capitalize()}<hr/>{principle.value}')
        else:
            btn.setToolTip(principle.type.name.lower().capitalize())

    def _principleEdited(self, principle: PlotPrinciple):
        self.repo.update_novel(self.novel)
        if principle.is_set:
            self._setPrincipleTooltip(self._btnPrinciple(principle.type), principle)

    def _updateIcon(self):
        if self.plot.icon:
            self.btnPlotIcon.setIcon(IconRegistry.from_name(self.plot.icon, self.plot.icon_color))

    def _nameEdited(self, name: str):
        self.plot.text = name
        self.repo.update_novel(self.novel)

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

    def _colorChanged(self, color: QColor):
        self.plot.icon_color = color.name()
        self._updateIcon()
        self.parent().setFrameColor(color)
        self.repo.update_novel(self.novel)

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
        flow(self.scrollAreaWidgetContents, spacing=15)
        margins(self.scrollAreaWidgetContents, left=15)
        for plot in self.novel.plots:
            self._addPlotWidget(plot)

        italic(self.btnAdd)
        self.btnAdd.setIcon(IconRegistry.plus_icon('grey'))
        menu = QMenu(self.btnAdd)
        menu.addAction(IconRegistry.cause_and_effect_icon(), 'Main plot', lambda: self.newPlot(PlotType.Main))
        menu.addAction(IconRegistry.conflict_self_icon(), 'Internal plot', lambda: self.newPlot(PlotType.Internal))
        menu.addAction(IconRegistry.subplot_icon(), 'Subplot', lambda: self.newPlot(PlotType.Subplot))
        btn_popup_menu(self.btnAdd, menu)

        self.repo = RepositoryPersistenceManager.instance()

    def _addPlotWidget(self, plot: Plot) -> PlotWidget:
        frame = Frame()
        frame.setFrameColor(QColor(plot.icon_color))
        frame.setBackgroundColor(QColor(RELAXED_WHITE_COLOR))

        widget = PlotWidget(self.novel, plot, frame)
        margins(widget, left=5, right=5)
        widget.removalRequested.connect(partial(self._remove, widget))

        frame.setWidget(widget)
        self.scrollAreaWidgetContents.layout().addWidget(frame)

        return widget

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
        plot.icon_color = STORY_LINE_COLOR_CODES[(len(self.novel.plots) - 1) % len(STORY_LINE_COLOR_CODES)]
        widget = self._addPlotWidget(plot)
        widget.lineName.setFocus()

        self.repo.update_novel(self.novel)

    def _remove(self, widget: PlotWidget):
        if ask_confirmation(f'Are you sure you want to delete the plot {widget.plot.text}?'):
            if app_env.test_env():
                self.__destroy(widget)
            else:
                anim = qtanim.fade_out(widget, duration=150)
                anim.finished.connect(partial(self.__destroy, widget))

    def __destroy(self, widget: PlotWidget):
        delete_plot(self.novel, widget.plot)
        self.scrollAreaWidgetContents.layout().removeWidget(widget.parent())
