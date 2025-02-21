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
from PyQt6.QtGui import QTextDocument, QPageSize, QColor
from PyQt6.QtPrintSupport import QPrintPreviewWidget, QPrinter
from PyQt6.QtWidgets import QButtonGroup, QWidget, QApplication, QDialog, QGraphicsView, QSplitter, QPushButton
from overrides import overrides
from qthandy import vbox, vspacer, sp, incr_icon, incr_font

from plotlyst.common import RELAXED_WHITE_COLOR, PLOTLYST_SECONDARY_COLOR
from plotlyst.core.domain import Novel
from plotlyst.service.manuscript import export_manuscript_to_docx, format_manuscript
from plotlyst.view.common import push_btn, label, exclusive_buttons
from plotlyst.view.icons import IconRegistry
from plotlyst.view.layout import group
from plotlyst.view.style.theme import BG_MUTED_COLOR
from plotlyst.view.widget.display import PopupDialog
from plotlyst.view.widget.settings import Forms


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
        item = self.printView.layout().itemAt(0)
        if isinstance(item.widget(), QGraphicsView):
            item.widget().setBackgroundBrush(QColor(BG_MUTED_COLOR))
        sp(self.printView).h_exp()

        self.layout().addWidget(self.printView)

        self._btnDocx = self.__selectorButton('mdi.file-word-outline', 'Word (.docx)')
        self._btnPdf = self.__selectorButton('fa5.file-pdf', 'PDF')

        self.wdgEditor = QWidget()
        # formLayout = QFormLayout(self.wdgEditor)
        vbox(self.wdgEditor, 10, 6)
        self.wdgCentral = QSplitter()
        self.wdgCentral.setChildrenCollapsible(False)
        self.wdgCentral.addWidget(self.printView)
        self.wdgCentral.addWidget(self.wdgEditor)
        self.wdgCentral.setSizes([550, 150])

        self._btnGroup = QButtonGroup()
        self._btnGroup.setExclusive(True)
        self._btnGroup.addButton(self._btnDocx)
        self._btnGroup.addButton(self._btnPdf)

        chapterForms = Forms('Chapter titles')
        self.wdgEditor.layout().addWidget(chapterForms)
        self.chapterSceneTitle = chapterForms.addSetting("First scene's title")
        self.chapterScenePov = chapterForms.addSetting("First POV's name")
        exclusive_buttons(self.wdgEditor, self.chapterSceneTitle, self.chapterScenePov, optional=True)

        self.wdgEditor.layout().addWidget(vspacer())

        self.btnExport = push_btn(IconRegistry.from_name('mdi.file-export-outline', RELAXED_WHITE_COLOR),
                                  'Export to docx',
                                  tooltip='Export manuscript',
                                  properties=['base', 'positive'])
        self.btnExport.clicked.connect(self.accept)
        self.btnCancel = push_btn(text='Close', properties=['confirm', 'cancel'])
        self.btnCancel.clicked.connect(self.reject)

        self._btnGroup.buttonToggled.connect(self._formatChanged)
        self._btnDocx.setChecked(True)

        self.frame.layout().addWidget(
            group(label('Export manuscript to: ', h5=True), self._btnDocx, self._btnPdf, margin=10, spacing=5),
            alignment=Qt.AlignmentFlag.AlignCenter)
        self.frame.layout().addWidget(self.wdgCentral)
        self.frame.layout().addWidget(group(self.btnCancel, self.btnExport), alignment=Qt.AlignmentFlag.AlignRight)

    @overrides
    def sizeHint(self) -> QSize:
        return self._adjustedSize()

    def _adjustedSize(self) -> QSize:
        window = QApplication.activeWindow()
        if window:
            size = QSize(int(window.size().width() * 0.9), int(window.size().height() * 0.8))
        else:
            return QSize(800, 600)

        size.setWidth(max(size.width(), 800))
        size.setHeight(max(size.height(), 600))

        return size

    def display(self):
        document: QTextDocument = format_manuscript(self.novel)
        self.printView.paintRequested.connect(partial(self._print, document))
        self.printView.fitToWidth()
        result = self.exec()
        if result == QDialog.DialogCode.Accepted:
            if self._btnDocx.isChecked():
                export_manuscript_to_docx(self.novel)
            elif self._btnPdf.isChecked():
                print('pdf')

    def _print(self, document: QTextDocument, device: QPrinter):
        device.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))
        device.setPageMargins(QMarginsF(0, 0, 0, 0))
        document.print(device)

    def _formatChanged(self):
        if self._btnDocx.isChecked():
            self.btnExport.setText('Export to docx')
        elif self._btnPdf.isChecked():
            self.btnExport.setText('Export to PDF')

    def __selectorButton(self, icon: str, text: str) -> QPushButton:
        btn = push_btn(IconRegistry.from_name(icon, color_on=PLOTLYST_SECONDARY_COLOR), text, checkable=True,
                       properties=['transparent-rounded-bg-on-hover', 'secondary-selector'])
        incr_icon(btn, 4)
        incr_font(btn, 2)

        return btn
