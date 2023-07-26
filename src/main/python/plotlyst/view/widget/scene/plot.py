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
import sys
from functools import partial
from typing import Optional

import qtanim
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QShowEvent
from PyQt6.QtWidgets import QWidget, QToolButton, QTextEdit, QApplication, \
    QMainWindow
from overrides import overrides
from qthandy import vbox, hbox, pointy, transparent, retain_when_hidden, spacer, sp, decr_icon, ask_confirmation
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.core.domain import Novel, Scene, ScenePlotReference, PlotValue, ScenePlotValueCharge, Plot
from src.main.python.plotlyst.view.common import action, fade_out_and_gc
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.style.base import apply_white_menu
from src.main.python.plotlyst.view.widget.button import SecondaryActionToolButton, SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.labels import PlotValueLabel, SelectionItemLabel, ScenePlotValueLabel


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
        self.textComment = QTextEdit(self)
        self.textComment.setProperty('white-bg', True)
        self.textComment.setProperty('rounded', True)
        self.textComment.setAcceptRichText(False)
        self.textComment.setFixedHeight(100)
        self.textComment.setPlaceholderText('Describe how this scene is related to the selected plot')
        self.textComment.setText(self.plotReference.data.comment)
        self.textComment.textChanged.connect(self._commentChanged)
        self.layout().addWidget(self.textComment)

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


class ScenePlotSelector(QWidget):
    plotSelected = pyqtSignal()

    def __init__(self, novel: Novel, scene: Scene, simplified: bool = False, parent=None):
        super(ScenePlotSelector, self).__init__(parent)
        self.novel = novel
        self.scene = scene
        self.plotValue: Optional[ScenePlotReference] = None
        hbox(self)

        self.label: Optional[SelectionItemLabel] = None

        self.btnLinkPlot = SecondaryActionPushButton(self)
        if simplified:
            self.btnLinkPlot.setIcon(IconRegistry.plus_circle_icon('grey'))
        else:
            self.btnLinkPlot.setText('Associate plot')
        self.layout().addWidget(self.btnLinkPlot)

        self.btnLinkPlot.installEventFilter(
            OpacityEventFilter(parent=self.btnLinkPlot, leaveOpacity=0.4 if simplified else 0.7))

        self._menu = MenuWidget(self.btnLinkPlot)
        self._menu.aboutToShow.connect(self._beforeShow)

    def setPlot(self, plotValue: ScenePlotReference):
        self.plotValue = plotValue
        self.label = ScenePlotValueLabel(plotValue, self)
        pointy(self.label)
        self.label.clicked.connect(self._plotValueClicked)

        self.label.removalRequested.connect(self._remove)
        self.layout().addWidget(self.label)
        self.btnLinkPlot.setHidden(True)

    def _plotSelected(self, plot: Plot):
        plotValue = ScenePlotReference(plot)
        self.scene.plot_values.append(plotValue)
        self.setPlot(plotValue)

        self.plotSelected.emit()
        self._plotValueClicked()

    def _plotValueClicked(self):
        menu = MenuWidget(self.label)
        apply_white_menu(menu)
        menu.addWidget(ScenePlotValueEditor(self.plotValue))
        menu.exec()

    def _beforeShow(self):
        self._menu.clear()
        occupied_plot_ids = [x.plot.id for x in self.scene.plot_values]
        self._menu.addSection('Link plotlines to this scene')
        self._menu.addSeparator()
        for plot in self.novel.plots:
            action_ = action(plot.text, IconRegistry.from_name(plot.icon, plot.icon_color),
                             partial(self._plotSelected, plot))
            if plot.id in occupied_plot_ids:
                action_.setDisabled(True)
            self._menu.addAction(action_)

    def _remove(self):
        if ask_confirmation(f"Remove scene association for plot '{self.plotValue.plot.text}'?"):
            self.scene.plot_values.remove(self.plotValue)
            fade_out_and_gc(self.parent(), self)


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)

            self.resize(500, 500)

            novel = Novel('test')
            novel.plots.append(Plot('Plot 1', icon='mdi.ray-start-arrow', icon_color='darkBlue'))
            scene = Scene('Scene 1')
            novel.scenes.append(scene)
            self.widget = ScenePlotSelector(novel, scene, parent=self)
            self.setCentralWidget(self.widget)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
