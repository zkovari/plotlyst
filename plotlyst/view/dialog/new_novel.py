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

from PyQt5.QtWidgets import QDialog

from plotlyst.view.generated.novel_creation_dialog_ui import Ui_NovelCreationDialog
from plotlyst.view.icons import IconRegistry


class NewNovelDialog(QDialog, Ui_NovelCreationDialog):
    def __init__(self, parent=None):
        super(NewNovelDialog, self).__init__(parent)
        self.setupUi(self)

        self.btnCancel.setIcon(IconRegistry.cancel_icon())
        self.btnConfirm.setIcon(IconRegistry.ok_icon())
        self.btnCancel.clicked.connect(self.reject)
        self.btnConfirm.clicked.connect(self.accept)

    def display(self) -> Optional[str]:
        result = self.exec()
        if result == QDialog.Rejected:
            return None
        return self.lineTitle.text()
