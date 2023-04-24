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
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QMouseEvent, QCursor
from PyQt6.QtWidgets import QWidget, QToolButton, QMenu, QTextEdit, QWidgetAction, QApplication, \
    QMainWindow
from overrides import overrides
from qthandy import vbox, hbox, pointy, gc, transparent, retain_when_hidden, btn_popup, spacer, sp
from qthandy.filter import OpacityEventFilter

from src.main.python.plotlyst.core.domain import Novel, Scene, ScenePlotReference, PlotValue, ScenePlotValueCharge, Plot
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import SecondaryActionToolButton, SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.labels import PlotValueLabel, SelectionItemLabel, PlotLabel, \
    ScenePlotValueLabel


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
        self.chargeIcon.setIconSize(QSize(22, 22))
        self.chargeIcon.setIcon(IconRegistry.charge_icon(self.charge))

        self.posCharge = SecondaryActionToolButton()
        self.posCharge.setIcon(IconRegistry.plus_circle_icon('grey'))
        self.posCharge.setIconSize(QSize(18, 18))
        self.posCharge.clicked.connect(lambda: self._changeCharge(1))
        retain_when_hidden(self.posCharge)
        self.negCharge = SecondaryActionToolButton()
        self.negCharge.setIcon(IconRegistry.minus_icon('grey'))
        self.negCharge.setIconSize(QSize(18, 18))
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

        vbox(self)
        self.textComment = QTextEdit(self)
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

        self.selectorWidget = QWidget()
        vbox(self.selectorWidget)
        occupied_plot_ids = [x.plot.id for x in self.scene.plot_values]
        for plot in self.novel.plots:
            if plot.id in occupied_plot_ids:
                continue
            label = PlotLabel(plot)
            label.installEventFilter(OpacityEventFilter(parent=label, leaveOpacity=0.7))
            label.clicked.connect(partial(self._plotSelected, plot))
            self.selectorWidget.layout().addWidget(label)

        btn_popup(self.btnLinkPlot, self.selectorWidget)

    def setPlot(self, plotValue: ScenePlotReference):
        self.plotValue = plotValue
        self.label = ScenePlotValueLabel(plotValue)
        pointy(self.label)
        self.label.clicked.connect(self._plotValueClicked)

        self.label.removalRequested.connect(self._remove)
        self.layout().addWidget(self.label)
        self.btnLinkPlot.setHidden(True)

    def _plotSelected(self, plot: Plot):
        self.btnLinkPlot.menu().hide()
        plotValue = ScenePlotReference(plot)
        self.scene.plot_values.append(plotValue)
        self.setPlot(plotValue)

        self.plotSelected.emit()

    def _plotValueClicked(self):
        menu = QMenu(self.label)
        action = QWidgetAction(menu)
        action.setDefaultWidget(ScenePlotValueEditor(self.plotValue))
        menu.addAction(action)
        menu.popup(QCursor.pos())

    def _remove(self):
        if self.parent():
            anim = qtanim.fade_out(self, duration=150)
            anim.finished.connect(self.__destroy)

    def __destroy(self):
        self.scene.plot_values.remove(self.plotValue)
        self.parent().layout().removeWidget(self)
        gc(self)


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)

            self.resize(500, 500)

            novel = Novel('test')
            novel.plots.append(Plot('Plot 1'))
            scene = Scene('Scene 1')
            novel.scenes.append(scene)
            self.widget = ScenePlotSelector(novel, scene, parent=self)
            self.setCentralWidget(self.widget)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
