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
from PyQt6.QtCore import QEvent, QObject, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QFrame, QWidgetAction, QMenu
from overrides import overrides
from qthandy import gc, bold, flow, incr_font, \
    margins, btn_popup_menu, ask_confirmation, italic
from qthandy.filter import VisibilityToggleEventFilter

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
        self.lineName.setText(self.plot.text)
        self.lineName.textChanged.connect(self._nameEdited)
        self.textQuestion.setPlainText(self.plot.question)
        self.textQuestion.textChanged.connect(self._questionChanged)

        flow(self.wdgValues)

        for value in self.plot.values:
            self._addValue(value)

        self._btnAddValue = SecondaryActionPushButton(self)
        self._btnAddValue.setText('Attach story value')
        self.wdgValues.layout().addWidget(self._btnAddValue)
        self._btnAddValue.clicked.connect(self._newValue)

        self.installEventFilter(VisibilityToggleEventFilter(target=self.btnRemove, parent=self))

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
        self.installEventFilter(self)

        self.repo = RepositoryPersistenceManager.instance()

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            self.setStyleSheet(f'''
            .PlotWidget {{
                background-color: #dee2e6;
                border-radius: 6px;
                border-left: 8px solid {self.plot.icon_color};
            }}''')
        elif event.type() == QEvent.Type.Leave:
            self.setStyleSheet(f'.PlotWidget {{border-radius: 6px; border-left: 8px solid {self.plot.icon_color};}}')

        return super(PlotWidget, self).eventFilter(watched, event)

    def _updateIcon(self):
        self.setStyleSheet(f'.PlotWidget {{border-radius: 6px; border-left: 8px solid {self.plot.icon_color};}}')
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
        self.wdgValues.layout().addWidget(label)
        label.removalRequested.connect(partial(self._removeValue, label))

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


class PlotEditor(QWidget, Ui_PlotEditor):
    def __init__(self, novel: Novel, parent=None):
        super(PlotEditor, self).__init__(parent)
        self.setupUi(self)
        self.novel = novel
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
        widget = PlotWidget(self.novel, plot)
        margins(widget, left=15)
        widget.removalRequested.connect(partial(self._remove, widget))
        self.scrollAreaWidgetContents.layout().insertWidget(self.scrollAreaWidgetContents.layout().count() - 2, widget)

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

        self.scrollAreaWidgetContents.layout().removeWidget(widget)
        gc(widget)
