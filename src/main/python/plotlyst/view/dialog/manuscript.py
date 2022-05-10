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

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPageSize
from PyQt5.QtPrintSupport import QPrintPreviewWidget, QPrinter
from PyQt5.QtWidgets import QDialog, QTextEdit
from qthandy import vbox

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.service.manuscript import format_manuscript


class ManuscriptPreviewDialog(QDialog):
    def __init__(self, parent=None):
        super(ManuscriptPreviewDialog, self).__init__(parent)
        vbox(self, 0, 0)
        self.printView = QPrintPreviewWidget()
        self.printView.setZoomFactor(1.3)

        self.layout().addWidget(self.printView)

    def display(self, novel: Novel):
        if not novel:
            return
        textedit = format_manuscript(novel)
        self.printView.paintRequested.connect(partial(self._print, textedit))
        self.setWindowState(Qt.WindowMaximized)
        self.exec()

    def _print(self, textedit: QTextEdit, device: QPrinter):
        device.setPageSize(QPageSize(QPageSize.A4))
        device.setPageMargins(0, 0, 0, 0, QPrinter.Inch)
        textedit.print_(device)
