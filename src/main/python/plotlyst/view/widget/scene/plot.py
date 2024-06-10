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
from abc import abstractmethod
from functools import partial
from typing import Optional, Dict

import qtanim
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QEvent
from PyQt6.QtGui import QColor, QMouseEvent, QEnterEvent, QResizeEvent
from PyQt6.QtWidgets import QWidget, QToolButton, QGraphicsDropShadowEffect, QTextEdit
from overrides import overrides
from qthandy import vbox, hbox, transparent, retain_when_hidden, spacer, sp, decr_icon, line, vline, \
    margins, italic
from qthandy.filter import OpacityEventFilter, VisibilityToggleEventFilter, InstantTooltipEventFilter
from qtmenu import MenuWidget

from plotlyst.core.domain import Novel, Scene, ScenePlotReference, PlotValue, ScenePlotValueCharge, \
    Plot
from plotlyst.view.common import action, tool_btn, wrap
from plotlyst.view.icons import IconRegistry
from plotlyst.view.style.base import apply_white_menu
from plotlyst.view.style.button import apply_button_palette_color
from plotlyst.view.widget.button import SecondaryActionToolButton
from plotlyst.view.widget.display import Icon
from plotlyst.view.widget.input import RemovalButton
from plotlyst.view.widget.labels import PlotValueLabel


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


class ProgressEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        hbox(self, spacing=0)

        self._idleIcon = IconRegistry.from_name('mdi.chevron-double-up', 'lightgrey')
        self._chargeEnabled: bool = True
        self.btnProgress = tool_btn(self._idleIcon, transparent_=True, pointy_=False)
        self.btnProgress.setText('Progress')
        self.btnProgress.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        italic(self.btnProgress)
        apply_button_palette_color(self.btnProgress, 'grey')
        self.btnProgress.setIconSize(QSize(76, 76))

        self.btnProgressAlt = tool_btn(self._idleIcon, transparent_=True, pointy_=False, parent=self.btnProgress)
        self.btnProgressAlt.setHidden(True)

        self.posCharge = tool_btn(IconRegistry.plus_circle_icon('grey'), transparent_=True)
        decr_icon(self.posCharge, 4)
        self.posCharge.clicked.connect(lambda: self._changeCharge(1))
        self.negCharge = tool_btn(IconRegistry.minus_icon('grey'), transparent_=True)
        decr_icon(self.negCharge, 4)
        self.negCharge.clicked.connect(lambda: self._changeCharge(-1))

        self.btnLock = Icon()
        self.btnLock.setIcon(IconRegistry.from_name('fa5s.lock', 'grey'))
        self.btnLock.installEventFilter(InstantTooltipEventFilter(self.btnLock))
        self.btnLock.setHidden(True)

        self.wdgSize = QWidget()
        vbox(self.wdgSize, 0, 0)
        self.wdgSize.layout().addWidget(self.posCharge)
        self.wdgSize.layout().addWidget(self.negCharge)
        retain_when_hidden(self.wdgSize)
        self.wdgSize.setHidden(True)

        self.layout().addWidget(self.btnProgress)
        self.layout().addWidget(self.wdgSize, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.layout().addWidget(self.btnLock, alignment=Qt.AlignmentFlag.AlignVCenter)

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        if self._chargeEnabled:
            self.wdgSize.setVisible(True)
        else:
            self.btnLock.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        self.wdgSize.setHidden(True)
        self.btnLock.setHidden(True)

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.btnProgressAlt.setGeometry(self.btnProgress.size().width() - 20, self.btnProgress.size().height() - 40, 20,
                                        20)

    def refresh(self):
        if self.charge() == 0:
            self.btnProgress.setIcon(self._idleIcon)
        if self.altCharge() == 0:
            self.btnProgressAlt.setHidden(True)

        if self.charge() == abs(self.altCharge()):
            if self.charge():
                self.btnProgress.setIcon(IconRegistry.trade_off_charge_icon(self.charge()))
            else:
                self.btnProgress.setIcon(self._idleIcon)
            self.btnProgressAlt.setHidden(True)
        else:
            self.btnProgress.setIcon(IconRegistry.charge_icon(self.charge()))
            if self.altCharge():
                self.btnProgressAlt.setVisible(True)
                self.btnProgressAlt.setIcon(IconRegistry.charge_icon(self.altCharge()))

        self._updateButtons()

    @abstractmethod
    def charge(self) -> int:
        pass

    def altCharge(self) -> int:
        return 0

    @abstractmethod
    def _changeCharge(self, charge: int):
        pass

    def _updateButtons(self):
        self.posCharge.setEnabled(True)
        self.negCharge.setEnabled(True)

        if self.charge() == 3:
            self.posCharge.setDisabled(True)
        elif self.charge() == -3:
            self.negCharge.setDisabled(True)


class ScenePlotGeneralProgressEditor(ProgressEditor):
    charged = pyqtSignal()

    def __init__(self, plotReference: ScenePlotReference, parent=None):
        super().__init__(parent)
        self.plotReference = plotReference
        self.refresh()

    @abstractmethod
    def charge(self) -> int:
        return self.plotReference.data.charge

    @overrides
    def _changeCharge(self, charge: int):
        self.plotReference.data.charge += charge
        self.refresh()
        self.charged.emit()


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
    generalProgressCharged = pyqtSignal()

    def __init__(self, plotReference: ScenePlotReference, parent=None):
        super().__init__(parent)
        self.plotReference = plotReference

        self.setProperty('relaxed-white-bg', True)
        vbox(self)

        self._text = QTextEdit()
        self._text.setProperty('rounded', True)
        self._text.setProperty('white-bg', True)
        self._text.setPlaceholderText('Describe how the scene is related to this storyline')
        self._text.setMaximumSize(180, 150)
        self._text.setText(self.plotReference.data.comment)
        self._text.textChanged.connect(self._textChanged)
        self.layout().addWidget(self._text)
        self.layout().addWidget(line(color='lightgrey'))

        if self.plotReference.plot.default_value_enabled:
            wdg = ScenePlotGeneralProgressEditor(self.plotReference)
            wdg.charged.connect(self.generalProgressCharged)
            self.layout().addWidget(wrap(wdg, margin_left=15), alignment=Qt.AlignmentFlag.AlignCenter)
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

        self.aboutToShow.connect(self._beforeShow)
        apply_white_menu(self)

    def setScene(self, scene: Scene):
        self._scene = scene

    def _beforeShow(self):
        if self._scene is None:
            return
        self.clear()
        occupied_plot_ids = self._occupiedPlotIds()
        self.addSection('Link storylines to this scene')
        self.addSeparator()
        for plot in self._novel.plots:
            action_ = action(plot.text, IconRegistry.from_name(plot.icon, plot.icon_color),
                             partial(self.plotSelected.emit, plot))
            if plot.id in occupied_plot_ids:
                action_.setDisabled(True)
            self.addAction(action_)

        if not self.actions():
            self.addSection('No corresponding storylines were found')

    def _occupiedPlotIds(self):
        return [x.plot.id for x in self._scene.plot_values]


class SceneFunctionPlotSelectorMenu(ScenePlotSelectorMenu):

    @overrides
    def _occupiedPlotIds(self):
        return [x.ref for x in self._scene.functions.primary]


class ScenePlotLabels(QWidget):
    reset = pyqtSignal()
    generalProgressCharged = pyqtSignal()

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
        self._plotValueEditor.generalProgressCharged.connect(self.generalProgressCharged)

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
