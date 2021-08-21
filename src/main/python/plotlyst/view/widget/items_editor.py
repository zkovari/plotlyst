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
from typing import Optional

from PyQt5.QtWidgets import QWidget

from src.main.python.plotlyst.model.common import EditableItemsModel
from src.main.python.plotlyst.view.delegates import TextItemDelegate
from src.main.python.plotlyst.view.generated.items_editor_widget_ui import Ui_ItemsEditorWidget
from src.main.python.plotlyst.view.icons import IconRegistry


class ItemsEditorWidget(QWidget, Ui_ItemsEditorWidget):
    def __init__(self, parent=None):
        super(ItemsEditorWidget, self).__init__(parent)
        self.setupUi(self)
        self.model: Optional[EditableItemsModel] = None

        self.btnAdd.setIcon(IconRegistry.plus_icon())
        self.btnAdd.clicked.connect(self._add)

        self.btnEdit.clicked.connect(self._edit)
        self.btnEdit.setIcon(IconRegistry.edit_icon())
        self.btnEdit.setDisabled(True)

        self.btnRemove.clicked.connect(self._remove)
        self.btnRemove.setDisabled(True)
        self.btnRemove.setIcon(IconRegistry.minus_icon())

    def setModel(self, model: EditableItemsModel):
        self.model = model
        self.tableView.setModel(self.model)
        self.tableView.selectionModel().selectionChanged.connect(self._item_selected)
        self.tableView.setItemDelegate(TextItemDelegate())

    def refresh(self):
        self.model.modelReset.emit()
        self.btnEdit.setEnabled(False)
        self.btnRemove.setEnabled(False)

    def _add(self):
        self.model.add()
        default_editable_col = self.model.defaultEditableColumn()
        if default_editable_col >= 0:
            self.tableView.edit(self.model.index(self.model.rowCount() - 1, default_editable_col))

    def _edit(self):
        indexes = self.tableView.selectedIndexes()
        if not indexes:
            return
        if self.model.columnIsEditable(indexes[0].column()):
            self.tableView.edit(indexes[0])

    def _remove(self):
        indexes = self.tableView.selectedIndexes()
        if not indexes:
            return
        self.model.remove(indexes[0])

    def _item_selected(self):
        selection = len(self.tableView.selectedIndexes()) > 0
        self.btnEdit.setEnabled(selection)
        self.btnRemove.setEnabled(selection)
