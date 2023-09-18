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
from typing import Optional

import qtanim
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QShowEvent
from PyQt6.QtWidgets import QWidget, QToolButton, QTextEdit, QLabel, QPushButton
from overrides import overrides
from qthandy import vbox, hbox, transparent, retain_when_hidden, spacer, sp, decr_icon, line, pointy, underline
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.core.domain import Novel, Scene, ScenePlotReference, PlotValue, ScenePlotValueCharge, Plot
from src.main.python.plotlyst.view.common import action
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import SecondaryActionToolButton
from src.main.python.plotlyst.view.widget.display import IconText
from src.main.python.plotlyst.view.widget.labels import PlotValueLabel


class ScenePlotValueChargeWidget(QWidget):
    def __init__(self, plotReference: ScenePlotReference, value: PlotValue, parent=None):
        super(ScenePlotValueChargeWidget, self).__init__(parent)
        self.plotReference = plotReference
        self.value: PlotValue = value
        lbl = PlotValueLabel(value)
        sp(lbl).h_max()
        hbox(self)

        self.charge: int = 0
        self.plot_value_charge: Optional[ScenePlotValueCharge] = None
        for v in self.plotReference.data.values:
            if v.plot_value_id == value.id:
                self.charge = v.charge
                self.plot_value_charge = v

        self.chargeIcon = QToolButton()
        transparent(self.chargeIcon)
        self.chargeIcon.setIcon(IconRegistry.charge_icon(self.charge))

        self.posCharge = SecondaryActionToolButton()
        self.posCharge.setIcon(IconRegistry.plus_circle_icon('grey'))
        decr_icon(self.posCharge, 4)
        self.posCharge.clicked.connect(lambda: self._changeCharge(1))
        retain_when_hidden(self.posCharge)
        self.negCharge = SecondaryActionToolButton()
        self.negCharge.setIcon(IconRegistry.minus_icon('grey'))
        decr_icon(self.negCharge, 4)
        self.negCharge.clicked.connect(lambda: self._changeCharge(-1))
        retain_when_hidden(self.negCharge)

        self.layout().addWidget(self.chargeIcon)
        self.layout().addWidget(lbl, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(spacer())
        self.layout().addWidget(self.negCharge)
        self.layout().addWidget(self.posCharge)

        self._updateButtons()

    def _changeCharge(self, increment: int):
        self.charge += increment
        if self.plot_value_charge is None:
            self.plot_value_charge = ScenePlotValueCharge(self.value.id, self.charge)
            self.plotReference.data.values.append(self.plot_value_charge)
        self.plot_value_charge.charge = self.charge

        self.chargeIcon.setIcon(IconRegistry.charge_icon(self.charge))
        if increment > 0:
            qtanim.glow(self.chargeIcon, color=QColor('#52b788'))
        else:
            qtanim.glow(self.chargeIcon, color=QColor('#9d0208'))

        self._updateButtons()

    def _updateButtons(self):
        if not self.negCharge.isEnabled():
            self.negCharge.setEnabled(True)
            self.negCharge.setVisible(True)
        if not self.posCharge.isEnabled():
            self.posCharge.setEnabled(True)
            self.posCharge.setVisible(True)
        if self.charge == 3:
            self.posCharge.setDisabled(True)
            self.posCharge.setHidden(True)
        if self.charge == -3:
            self.negCharge.setDisabled(True)
            self.negCharge.setHidden(True)


class ScenePlotValueEditor(QWidget):
    def __init__(self, plotReference: ScenePlotReference, parent=None):
        super(ScenePlotValueEditor, self).__init__(parent)
        self.plotReference = plotReference

        self.setProperty('relaxed-white-bg', True)

        vbox(self)

        self._title = IconText()
        if plotReference.plot.icon:
            self._title.setIcon(IconRegistry.from_name(plotReference.plot.icon, plotReference.plot.icon_color))
        self._title.setText(plotReference.plot.text)
        self.layout().addWidget(self._title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.textComment = QTextEdit(self)
        self.textComment.setProperty('white-bg', True)
        self.textComment.setProperty('rounded', True)
        self.textComment.setAcceptRichText(False)
        self.textComment.setFixedHeight(100)
        self.textComment.setPlaceholderText('Describe how this scene is related to the selected plot')
        self.textComment.setText(self.plotReference.data.comment)
        self.textComment.textChanged.connect(self._commentChanged)
        self.layout().addWidget(self.textComment)

        if self.plotReference.plot.default_value_enabled:
            wdg = ScenePlotValueChargeWidget(self.plotReference, self.plotReference.plot.default_value)
            self.layout().addWidget(QLabel('General progress or setback'))
            self.layout().addWidget(wdg)
            self.layout().addWidget(line(color='lightgrey'))

        if self.plotReference.plot.values:
            self.layout().addWidget(QLabel('Custom values'))

        for value in self.plotReference.plot.values:
            wdg = ScenePlotValueChargeWidget(self.plotReference, value)
            self.layout().addWidget(wdg)

    @overrides
    def showEvent(self, _: QShowEvent) -> None:
        self.textComment.setFocus()

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        pass

    def _commentChanged(self):
        self.plotReference.data.comment = self.textComment.toPlainText()


class ScenePlotSelectorMenu(MenuWidget):
    plotSelected = pyqtSignal(Plot)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._scene: Optional[Scene] = None

        self.aboutToShow.connect(self._beforeShow)

    def setScene(self, scene: Scene):
        self._scene = scene

    def _beforeShow(self):
        if self._scene is None:
            return
        self.clear()
        occupied_plot_ids = [x.plot.id for x in self._scene.plot_values]
        self.addSection('Link storylines to this scene')
        self.addSeparator()
        for plot in self._novel.plots:
            action_ = action(plot.text, IconRegistry.from_name(plot.icon, plot.icon_color),
                             partial(self.plotSelected.emit, plot))
            if plot.id in occupied_plot_ids:
                action_.setDisabled(True)
            self.addAction(action_)


class ScenePlotSelectorButton(QPushButton):
    plotSelected = pyqtSignal(Plot)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._scene: Optional[Scene] = None
        self.plotValue: Optional[ScenePlotReference] = None

        transparent(self)
        self.setProperty('no-menu', True)
        self.setText('Storyline')

        self.installEventFilter(OpacityEventFilter(parent=self, leaveOpacity=0.7))

        if self._novel.plots:
            pointy(self)
            underline(self)
            self._menu = ScenePlotSelectorMenu(self._novel, self)
            self._menu.plotSelected.connect(self._plotSelected)

    def setScene(self, scene: Scene):
        self._scene = scene
        self._menu.setScene(scene)

    def setPlot(self, plotValue: ScenePlotReference):
        self.plotValue = plotValue
        self.setText(plotValue.plot.text)
        underline(self, False)

    def _plotSelected(self, plot: Plot):
        plotValue = ScenePlotReference(plot)
        # TODO add back later
        # self._scene.plot_values.append(plotValue)
        self.setPlot(plotValue)

        self.plotSelected.emit(plot)
