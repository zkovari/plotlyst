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

from PyQt6.QtCore import Qt, QMarginsF
from PyQt6.QtGui import QPageSize, QTextDocument
from PyQt6.QtPrintSupport import QPrintPreviewWidget, QPrinter
from PyQt6.QtWidgets import QDialog
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
        document: QTextDocument = format_manuscript(novel)
        self.printView.paintRequested.connect(partial(self._print, document))
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.exec()

    def _print(self, document: QTextDocument, device: QPrinter):
        device.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        device.setPageMargins(QMarginsF(0, 0, 0, 0))
        document.print(device)
