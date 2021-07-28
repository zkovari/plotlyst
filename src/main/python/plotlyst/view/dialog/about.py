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
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from src.main.python.plotlyst.view.generated.about_dialog_ui import Ui_AboutDialog


class AboutDialog(Ui_AboutDialog, QDialog):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)

        self.setupUi(self)


class DummyDialog(QDialog):
    def __init__(self):
        super(DummyDialog, self).__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
