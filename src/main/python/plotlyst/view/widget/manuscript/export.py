"""
Plotlyst
Copyright (C) 2021-2025  Zsolt Kovari

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

from PyQt6.QtCore import Qt, QMarginsF, QSize
from PyQt6.QtGui import QTextDocument, QPageSize
from PyQt6.QtPrintSupport import QPrintPreviewWidget, QPrinter
from PyQt6.QtWidgets import QButtonGroup, QWidget, QApplication
from overrides import overrides
from qthandy import vbox

from plotlyst.common import RELAXED_WHITE_COLOR
from plotlyst.core.domain import Novel
from plotlyst.service.manuscript import export_manuscript_to_docx, format_manuscript
from plotlyst.view.common import push_btn, label
from plotlyst.view.icons import IconRegistry
from plotlyst.view.layout import group
from plotlyst.view.widget.display import PopupDialog


class ManuscriptExportWidget(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel

        vbox(self, spacing=15)
        # self.layout().addWidget(label('Export manuscript', h5=True), alignment=Qt.AlignmentFlag.AlignCenter)
        # self.layout().addWidget(line())

        self._btnDocx = push_btn(IconRegistry.docx_icon(), 'Word (.docx)', checkable=True,
                                 properties=['transparent-rounded-bg-on-hover', 'secondary-selector'])
        self._btnDocx.setChecked(True)
        self._btnPdf = push_btn(IconRegistry.from_name('fa5.file-pdf'), 'PDF', checkable=True,
                                tooltip='PDF export not available yet',
                                properties=['transparent-rounded-bg-on-hover', 'secondary-selector'])

        self._btnGroup = QButtonGroup()
        self._btnGroup.setExclusive(True)
        self._btnGroup.addButton(self._btnDocx)
        self._btnGroup.addButton(self._btnPdf)
        self._btnPdf.setDisabled(True)
        self.layout().addWidget(self._btnDocx, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._btnPdf, alignment=Qt.AlignmentFlag.AlignCenter)

        self._btnExport = push_btn(IconRegistry.from_name('mdi.file-export-outline', RELAXED_WHITE_COLOR), 'Export',
                                   tooltip='Export manuscript',
                                   properties=['base', 'positive'])
        self.layout().addWidget(self._btnExport)

        self._btnExport.clicked.connect(self._export)

    def _export(self):
        if self._btnDocx.isChecked():
            export_manuscript_to_docx(self._novel)


class ManuscriptExportPopup(PopupDialog):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel

        self.printView = QPrintPreviewWidget()
        # self.printView.setZoomMode(QPrintPreviewWidget.ZoomMode.FitToWidth)

        self.layout().addWidget(self.printView)

        self._btnExport = push_btn(IconRegistry.from_name('mdi.file-export-outline', RELAXED_WHITE_COLOR), 'Export',
                                   tooltip='Export manuscript',
                                   properties=['base', 'positive'])
        self.btnCancel = push_btn(text='Close', properties=['confirm', 'cancel'])
        self.btnCancel.clicked.connect(self.reject)

        self.frame.layout().addWidget(label('Export manuscript', h5=True), alignment=Qt.AlignmentFlag.AlignCenter)
        self.frame.layout().addWidget(self.printView)
        self.frame.layout().addWidget(group(self.btnCancel, self._btnExport), alignment=Qt.AlignmentFlag.AlignRight)

    @overrides
    def sizeHint(self) -> QSize:
        return self._adjustedSize()

    def _adjustedSize(self) -> QSize:
        window = QApplication.activeWindow()
        if window:
            size = QSize(int(window.size().width() * 0.75), int(window.size().height() * 0.8))
        else:
            return QSize(800, 600)

        size.setWidth(max(size.width(), 800))
        size.setHeight(max(size.height(), 600))

        return size

    def display(self):
        document: QTextDocument = format_manuscript(self.novel)
        self.printView.paintRequested.connect(partial(self._print, document))
        self.printView.fitToWidth()
        self.exec()

    def _print(self, document: QTextDocument, device: QPrinter):
        device.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        device.setPageMargins(QMarginsF(0, 0, 0, 0))
        document.print(device)
