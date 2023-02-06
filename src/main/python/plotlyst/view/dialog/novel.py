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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QPushButton, QDialogButtonBox, QApplication
from qthandy import flow
from qthandy.filter import DisabledClickEventFilter, OpacityEventFilter

from src.main.python.plotlyst.core.domain import NovelDescriptor, PlotValue, Novel
from src.main.python.plotlyst.view.common import link_editor_to_btn
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog
from src.main.python.plotlyst.view.generated.novel_creation_dialog_ui import Ui_NovelCreationDialog
from src.main.python.plotlyst.view.generated.plot_value_editor_dialog_ui import Ui_PlotValueEditorDialog
from src.main.python.plotlyst.view.generated.synopsis_editor_dialog_ui import Ui_SynopsisEditorDialog
from src.main.python.plotlyst.view.icons import IconRegistry


class NovelEditionDialog(QDialog, Ui_NovelCreationDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def display(self, novel: Optional[NovelDescriptor] = None) -> Optional[str]:
        if novel:
            self.lineTitle.setText(novel.title)
        result = self.exec()
        if result == QDialog.DialogCode.Rejected:
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
                border: 3px solid black;
            }}
        ''')
        self.installEventFilter(OpacityEventFilter(self, leaveOpacity=0.5))
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class PlotValueEditorDialog(QDialog, Ui_PlotValueEditorDialog):
    def __init__(self, parent=None):
        super(PlotValueEditorDialog, self).__init__(parent)
        self.setupUi(self)

        self._value = PlotValue('')

        self.btnChargeUp.setIcon(IconRegistry.charge_icon(3))
        self.btnChargeDown.setIcon(IconRegistry.charge_icon(-3))
        self.btnVersusIcon.setIcon(IconRegistry.from_name('fa5s.arrows-alt-v'))

        self.btnIcon.setIcon(IconRegistry.icons_icon('grey'))
        self.btnIcon.clicked.connect(self._changeIcon)

        flow(self.wdgTemplates)
        templates = [
            PlotValue(text='Love', negative='Hate', icon='ei.heart', icon_color='#d1495b'),
            PlotValue(text='Life', negative='Death', icon='mdi.pulse', icon_color='#ef233c'),
            PlotValue(text='Wealth', negative='Poverty', icon='fa5s.hand-holding-usd', icon_color='#e9c46a'),
            PlotValue(text='Justice', negative='Injustice', icon='fa5s.gavel', icon_color='#a68a64'),
            PlotValue(text='Maturity', negative='Immaturity', icon='fa5s.seedling', icon_color='#95d5b2'),
            PlotValue(text='Truth', negative='Lie', icon='mdi.scale-balance', icon_color='#5390d9'),
            PlotValue(text='Loyalty', negative='Betrayal', icon='fa5.handshake', icon_color='#5390d9'),
            PlotValue(text='Honor', negative='Dishonor', icon='fa5s.award', icon_color='#40916c'),
            PlotValue(text='Morality', negative='Immorality', icon='ph.scales-bold', icon_color='#560bad'),
            PlotValue(text='Esteem', negative='Disrespect', icon='mdi.account-star', icon_color='#f72585'),
        ]

        for value in templates:
            btn = _TemplatePlotValueButton(value)
            self.wdgTemplates.layout().addWidget(btn)
            btn.clicked.connect(partial(self._fillTemplate, value))

        btnOk = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        btnOk.setEnabled(False)
        btnOk.installEventFilter(DisabledClickEventFilter(btnOk, lambda: qtanim.shake(self.linePositive)))
        link_editor_to_btn(self.linePositive, btnOk)

    def display(self) -> Optional[PlotValue]:
        result = self.exec()
        if result == QDialog.DialogCode.Accepted:
            self._value.text = self.linePositive.text()
            self._value.negative = self.lineNegative.text()
            return self._value

    def _fillTemplate(self, value: PlotValue):
        self.linePositive.setText(value.text)
        self.lineNegative.setText(value.negative)
        if value.icon:
            self.btnIcon.setIcon(IconRegistry.from_name(value.icon, value.icon_color))
            self._value.icon = value.icon
            self._value.icon_color = value.icon_color
            self.btnIcon.setBorderColor(self._value.icon_color)

        glow_color = QColor(value.icon_color)
        qtanim.glow(self.linePositive, color=glow_color)
        qtanim.glow(self.lineNegative, color=glow_color)
        qtanim.glow(self.btnIcon, color=glow_color)

    def _changeIcon(self):
        result = IconSelectorDialog().display()
        if result:
            self._value.icon = result[0]
            self._value.icon_color = result[1].name()
            self.btnIcon.setIcon(IconRegistry.from_name(self._value.icon, self._value.icon_color))
            self.btnIcon.setBorderColor(self._value.icon_color)


class SynopsisEditorDialog(QDialog, Ui_SynopsisEditorDialog):
    def __init__(self, parent=None):
        super(SynopsisEditorDialog, self).__init__(parent,
                                                   Qt.WindowType.CustomizeWindowHint
                                                   | Qt.WindowType.Window
                                                   | Qt.WindowType.WindowMaximizeButtonHint
                                                   | Qt.WindowType.WindowCloseButtonHint)
        self.setupUi(self)
        self.textSynopsis.setPlaceholderText("Write down your story's main events")
        self.textSynopsis.setMargins(0, 10, 0, 10)
        self.textSynopsis.setGrammarCheckEnabled(True)

        self.textSynopsis.setToolbarVisible(False)
        self.textSynopsis.setTitleVisible(False)

    @staticmethod
    def display(novel: Novel) -> str:
        dialog = SynopsisEditorDialog()
        dialog.textSynopsis.setText(novel.synopsis.content)

        screen = QApplication.screenAt(dialog.pos())
        if screen:
            dialog.resize(screen.size().width(), screen.size().height())
        else:
            dialog.resize(600, 500)

        dialog.exec()

        return dialog.textSynopsis.textEdit.toHtml()
