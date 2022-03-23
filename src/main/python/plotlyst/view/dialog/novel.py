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
from typing import Optional

import qtanim
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QPushButton, QDialogButtonBox
from qthandy import flow

from src.main.python.plotlyst.core.domain import NovelDescriptor, PlotValue
from src.main.python.plotlyst.view.common import OpacityEventFilter, link_editor_to_btn, DisabledClickEventFilter
from src.main.python.plotlyst.view.generated.novel_creation_dialog_ui import Ui_NovelCreationDialog
from src.main.python.plotlyst.view.generated.plot_value_editor_dialog_ui import Ui_PlotValueEditorDialog
from src.main.python.plotlyst.view.icons import IconRegistry


class NovelEditionDialog(QDialog, Ui_NovelCreationDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def display(self, novel: Optional[NovelDescriptor] = None) -> Optional[str]:
        if novel:
            self.lineTitle.setText(novel.title)
        result = self.exec()
        if result == QDialog.Rejected:
            return None
        return self.lineTitle.text()


class _TemplatePlotValueButton(QPushButton):
    def __init__(self, value: PlotValue, parent=None):
        super(_TemplatePlotValueButton, self).__init__(parent)
        if value.negative:
            self.setText(f'{value.text}/{value.negative}')
        else:
            self.setText(value.text)
        if value.icon:
            self.setIcon(IconRegistry.from_name(value.icon, value.icon_color))

        self.setStyleSheet(f'''
            QPushButton {{
                border: 3px solid {value.icon_color};
                border-radius: 6px;
                padding: 2px;
            }}
            QPushButton:pressed {{
                border: 3px solid white;
            }}
        ''')
        self.installEventFilter(OpacityEventFilter(leaveOpacity=0.6, parent=self))
        self.setCursor(Qt.PointingHandCursor)


class PlotValueEditorDialog(QDialog, Ui_PlotValueEditorDialog):
    def __init__(self, parent=None):
        super(PlotValueEditorDialog, self).__init__(parent)
        self.setupUi(self)

        self.btnChargeUp.setIcon(IconRegistry.charge_icon(3))
        self.btnChargeDown.setIcon(IconRegistry.charge_icon(-3))
        self.btnVersusIcon.setIcon(IconRegistry.from_name('fa5s.arrows-alt-v'))

        flow(self.wdgTemplates)
        templates = [
            PlotValue(text='Love', negative='Hate', icon='ei.heart', icon_color='#d1495b'),
            PlotValue(text='Life', negative='Death', icon='mdi.pulse', icon_color='#ef233c'),
            PlotValue(text='Justice', negative='Injustice', icon='fa5s.gavel', icon_color='#a68a64'),
            PlotValue(text='Maturity', negative='Immaturity', icon='fa5s.seedling', icon_color='#95d5b2'),
            PlotValue(text='Truth', negative='Lie', icon='mdi.scale-balance', icon_color='#5390d9'),
            PlotValue(text='Loyalty', negative='Betrayal', icon='fa5.handshake', icon_color='#5390d9'),
            PlotValue(text='Honor', negative='Dishonor', icon='fa5s.award', icon_color='#40916c')
        ]

        for value in templates:
            btn = _TemplatePlotValueButton(value)
            self.wdgTemplates.layout().addWidget(btn)
            btn.clicked.connect(partial(self._fillTemplate, value))

        btnOk = self.buttonBox.button(QDialogButtonBox.Ok)
        btnOk.setEnabled(False)
        btnOk.installEventFilter(DisabledClickEventFilter(lambda: qtanim.shake(self.linePositive), parent=btnOk))
        link_editor_to_btn(self.linePositive, btnOk)

    def display(self) -> Optional[PlotValue]:
        result = self.exec()
        if result == QDialog.Accepted:
            return PlotValue(text=self.linePositive.text(), negative=self.lineNegative.text())

    def _fillTemplate(self, value: PlotValue):
        self.linePositive.setText(value.text)
        self.lineNegative.setText(value.negative)
        if value.icon:
            self.btnIcon.setIcon(IconRegistry.from_name(value.icon, value.icon_color))

        glow_color = QColor(value.icon_color)
        qtanim.glow(self.linePositive, color=glow_color)
        qtanim.glow(self.lineNegative, color=glow_color)
        qtanim.glow(self.btnIcon, color=glow_color)
