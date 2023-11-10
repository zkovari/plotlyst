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
from typing import Optional, Dict

import qtanim
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent
from PyQt6.QtWidgets import QWidget, QToolButton, QGraphicsDropShadowEffect, QTextEdit
from overrides import overrides
from qthandy import vbox, hbox, transparent, retain_when_hidden, spacer, sp, decr_icon, line, vline, \
    margins
from qthandy.filter import OpacityEventFilter, VisibilityToggleEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.core.domain import Novel, Scene, ScenePlotReference, PlotValue, ScenePlotValueCharge, \
    Plot, PlotType
from src.main.python.plotlyst.view.common import action, tool_btn
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.style.base import apply_white_menu
from src.main.python.plotlyst.view.widget.button import SecondaryActionToolButton
from src.main.python.plotlyst.view.widget.input import RemovalButton
from src.main.python.plotlyst.view.widget.labels import PlotValueLabel


class PlotValuesDisplay(QWidget):
    def __init__(self, plotReference: ScenePlotReference, parent=None):
        super().__init__(parent)
        self._plotReference = plotReference
        self._values: Dict[PlotValue, PlotValueLabel] = {}

        hbox(self, spacing=9)
        margins(self, right=8)
        for value in self._plotReference.plot.values:
            lbl = PlotValueLabel(value, simplified=True)
            sp(lbl).h_max()
            lbl.setHidden(True)
            self._values[value] = lbl
            self.layout().addWidget(lbl)

    def updateValue(self, value: PlotValue, charge: ScenePlotValueCharge):
        lbl = self._values[value]
        if charge.charge == 0:
            lbl.setHidden(True)
        else:
            lbl.setVisible(True)
            effect = QGraphicsDropShadowEffect()
            if charge.charge > 0:
                effect.setColor(QColor('#52b788'))
                lbl.setEnabled(True)
            else:
                effect.setColor(QColor('#9d0208'))
                lbl.setEnabled(False)

            effect.setOffset(5 * abs(charge.charge), 0)
            effect.setBlurRadius(25)
            lbl.setGraphicsEffect(effect)


class ScenePlotValueChargeWidget(QWidget):
    charged = pyqtSignal(PlotValue, ScenePlotValueCharge)

    def __init__(self, plotReference: ScenePlotReference, value: PlotValue, parent=None):
        super(ScenePlotValueChargeWidget, self).__init__(parent)
        self.plotReference = plotReference
        self.value: PlotValue = value
        self._lbl = PlotValueLabel(value)
        sp(self._lbl).h_max()
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
        self.layout().addWidget(self._lbl, alignment=Qt.AlignmentFlag.AlignLeft)
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
        self.charged.emit(self.value, self.plot_value_charge)

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
    charged = pyqtSignal(PlotValue, ScenePlotValueCharge)

    def __init__(self, plotReference: ScenePlotReference, parent=None):
        super().__init__(parent)
        self.plotReference = plotReference

        self.setProperty('relaxed-white-bg', True)
        vbox(self)

        self._text = QTextEdit()
        self._text.setProperty('rounded', True)
        self._text.setProperty('white-bg', True)
        self._text.setPlaceholderText('Describe how the scene is related to this storyline')
        self._text.setMaximumSize(200, 180)
        self._text.setText(self.plotReference.data.comment)
        self._text.textChanged.connect(self._textChanged)
        self.layout().addWidget(self._text)
        self.layout().addWidget(line(color='lightgrey'))

        if self.plotReference.plot.default_value_enabled:
            wdg = ScenePlotValueChargeWidget(self.plotReference, self.plotReference.plot.default_value)
            wdg.charged.connect(self.charged.emit)
            # self.layout().addWidget(QLabel('General progress or setback'))
            self.layout().addWidget(wdg)
            self.layout().addWidget(line(color='lightgrey'))

        # if self.plotReference.plot.values:
        #     self.layout().addWidget(QLabel('Custom values'))

        for value in self.plotReference.plot.values:
            wdg = ScenePlotValueChargeWidget(self.plotReference, value)
            wdg.charged.connect(self.charged.emit)
            self.layout().addWidget(wdg)

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        pass

    def _textChanged(self):
        self.plotReference.data.comment = self._text.toPlainText()


class ScenePlotSelectorMenu(MenuWidget):
    plotSelected = pyqtSignal(Plot)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._scene: Optional[Scene] = None
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
            if not self._filters[plot.plot_type]:
                continue
            action_ = action(plot.text, IconRegistry.from_name(plot.icon, plot.icon_color),
                             partial(self.plotSelected.emit, plot))
            if plot.id in occupied_plot_ids:
                action_.setDisabled(True)
            self.addAction(action_)

        if not self.actions():
            self.addSection('No corresponding storylines were found')


class ScenePlotLabels(QWidget):
    reset = pyqtSignal()

    def __init__(self, plotref: ScenePlotReference, parent=None):
        super().__init__(parent)
        self._plotref = plotref
        hbox(self)

        self._icon = tool_btn(IconRegistry.from_name(self._plotref.plot.icon, self._plotref.plot.icon_color),
                              transparent_=True)

        tooltip = f'{self._plotref.plot.text}<hr><i>Click to charge storyline values</p>'
        self._icon.setToolTip(tooltip)

        self._icon.installEventFilter(OpacityEventFilter(self._icon, leaveOpacity=1.0, enterOpacity=0.7))
        self._plotValueMenu = MenuWidget(self._icon)
        apply_white_menu(self._plotValueMenu)

        self._plotValueEditor = ScenePlotValueEditor(self._plotref)
        self._plotValueMenu.addWidget(self._plotValueEditor)

        self._plotValueDisplay = PlotValuesDisplay(self._plotref)
        self._plotValueEditor.charged.connect(self._plotValueDisplay.updateValue)

        for value in self._plotref.data.values:
            plot_value = value.plot_value(self._plotref.plot)
            if plot_value:
                self._plotValueDisplay.updateValue(plot_value, value)

        self._btnReset = RemovalButton()
        self._btnReset.clicked.connect(self.reset.emit)
        retain_when_hidden(self._btnReset)

        self.layout().addWidget(vline())
        self.layout().addWidget(self._icon)
        self.layout().addWidget(self._plotValueDisplay)
        self.layout().addWidget(self._btnReset)

        self.installEventFilter(VisibilityToggleEventFilter(self._btnReset, self))

    def icon(self) -> QToolButton:
        return self._icon

    def storylineRef(self) -> ScenePlotReference:
        return self._plotref

    def activate(self):
        self._plotValueMenu.exec()
