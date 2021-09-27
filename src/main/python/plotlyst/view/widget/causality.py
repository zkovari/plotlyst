"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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

from PyQt5.QtCore import QEvent, QObject
from PyQt5.QtWidgets import QWidget
from overrides import overrides

from src.main.python.plotlyst.core.domain import Causality
from src.main.python.plotlyst.model.causality import CaualityTreeModel
from src.main.python.plotlyst.view.delegates import TextItemDelegate
from src.main.python.plotlyst.view.generated.causality_item_widget_ui import Ui_CausalityItemWidget
from src.main.python.plotlyst.view.generated.cause_and_effect_editor_ui import Ui_CauseAndEffectEditor
from src.main.python.plotlyst.view.icons import IconRegistry


class CauseAndEffectDiagram(QWidget, Ui_CauseAndEffectEditor):

    def __init__(self, causality: Causality, reversed_: bool = False, parent=None):
        super(CauseAndEffectDiagram, self).__init__(parent)
        self.setupUi(self)
        self.causality: Causality = causality
        self.model = CaualityTreeModel(self.causality)
        self.treeView.setModel(self.model)
        self.treeView.setItemDelegate(TextItemDelegate())
        self.treeView.expandAll()
        self.treeView.selectionModel().selectionChanged.connect(self._selected)
        self.model.modelReset.connect(self.treeView.expandAll)

        if reversed_:
            self.btnAddChild.setIcon(IconRegistry.cause_icon())
            self.btnAddChild.setToolTip('Add cause')
        self.btnEdit.setIcon(IconRegistry.edit_icon())
        self.btnDelete.setIcon(IconRegistry.wrong_icon('black'))

        self.btnEdit.clicked.connect(lambda: self.treeView.edit(self.treeView.selectedIndexes()[0]))
        self.btnAddChild.clicked.connect(self._addChild)
        self.btnDelete.clicked.connect(self._delete)

    def _selected(self):
        selected = bool(self.treeView.selectedIndexes())
        self.btnAddChild.setEnabled(selected)
        self.btnEdit.setEnabled(selected)
        self.btnDelete.setEnabled(selected)

    def _addChild(self):
        index = self.treeView.selectedIndexes()[0]
        self.model.addChild(index, 'Cause')

    def _delete(self):
        index = self.treeView.selectedIndexes()[0]
        self.model.delete(index)


class CausalityItemWidget(QWidget, Ui_CausalityItemWidget):
    def __init__(self, title: str = 'Effect', parent=None):
        super(CausalityItemWidget, self).__init__(parent)
        self.setupUi(self)
        font = self.lineText.font()
        font.setBold(True)
        self.lineText.setFont(font)
        self.lineText.setText(title)

        self.btnCause.setIcon(IconRegistry.cause_icon())
        # self.btnEffect.setIcon(IconRegistry.cause_and_effect_icon())

        self.btnCause.setVisible(False)
        self.wdgHeader.installEventFilter(self)

        self.btnCause.clicked.connect(self._addCause)
        # self.btnEffect.installEventFilter(self)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Enter or event.type() == QEvent.Leave:
            visible = event.type() == QEvent.Enter
            if watched == self.wdgHeader:
                self.btnCause.setVisible(visible)
            # elif watched == self.btnCause:
            #     self.lblCause.setText('Add cause' if visible else '')
            #     self.lblCause.setVisible(visible)
            # elif watched == self.btnEffect:
            #     self.lblCause.setText('Add effect' if visible else '')
            #     self.lblCause.setVisible(visible)
        return super(CausalityItemWidget, self).eventFilter(watched, event)

    def _addCause(self):
        self.wdgChildren.layout().addWidget(CausalityItemWidget('Cause'))
