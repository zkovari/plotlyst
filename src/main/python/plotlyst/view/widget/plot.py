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
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QFrame, QWidgetAction, QMenu
from qtframes import Frame
from qthandy import gc, bold, flow, incr_font, \
    margins, btn_popup_menu, ask_confirmation, italic, transparent, retain_when_hidden, translucent
from qthandy.filter import VisibilityToggleEventFilter

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Novel, Plot, PlotValue, PlotType
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager, delete_plot
from src.main.python.plotlyst.settings import STORY_LINE_COLOR_CODES
from src.main.python.plotlyst.view.common import action
from src.main.python.plotlyst.view.dialog.novel import PlotValueEditorDialog
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog
from src.main.python.plotlyst.view.generated.plot_editor_widget_ui import Ui_PlotEditor
from src.main.python.plotlyst.view.generated.plot_widget_ui import Ui_PlotWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.labels import PlotValueLabel
from src.main.python.plotlyst.view.widget.utility import ColorPicker


class PlotWidget(QFrame, Ui_PlotWidget):
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
        transparent(self.toolButton_3)
        transparent(self.toolButton_4)
        transparent(self.toolButton_5)
        transparent(self.toolButton_6)
        transparent(self.toolButton_7)
        transparent(self.toolButton_8)
        transparent(self.toolButton_9)
        transparent(self.toolButton_10)

        self.toolButton_3.setIcon(IconRegistry.goal_icon())
        self.toolButton_4.setIcon(IconRegistry.goal_icon())
        self.toolButton_5.setIcon(IconRegistry.goal_icon())
        self.toolButton_6.setIcon(IconRegistry.goal_icon())
        self.toolButton_7.setIcon(IconRegistry.goal_icon())
        self.toolButton_8.setIcon(IconRegistry.goal_icon())
        self.toolButton_9.setIcon(IconRegistry.goal_icon())
        self.toolButton_10.setIcon(IconRegistry.goal_icon())

        flow(self.wdgValues)
        self._btnAddValue = SecondaryActionPushButton(self)
        self._btnAddValue.setIconSize(QSize(14, 14))
        self._btnAddValue.setText('' if self.plot.values else 'Attach story value')
        retain_when_hidden(self._btnAddValue)
        self._btnAddValue.setIcon(IconRegistry.plus_icon('grey'))
        for value in self.plot.values:
            self._addValue(value)

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

    def _updateIcon(self):
        if self.plot.icon:
            self.btnPlotIcon.setIcon(IconRegistry.from_name(self.plot.icon, self.plot.icon_color))

    def _nameEdited(self, name: str):
        self.plot.text = name
        self.repo.update_novel(self.novel)

    def _questionChanged(self):
        self.plot.question = self.textQuestion.toPlainText()
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
        retain_when_hidden(self._btnAddValue, False)

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
        retain_when_hidden(self._btnAddValue, not has_values)


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
