"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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
import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableView

from plotlyst.service.log import LogHandler
from plotlyst.view.common import stretch_col, push_btn
from plotlyst.view.widget.display import PopupDialog


class LogsPopup(PopupDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tblView = QTableView()
        self.tblView.setWordWrap(True)
        self.tblView.setMinimumSize(700, 400)

        logger = logging.getLogger()
        for handler in logger.handlers:
            if isinstance(handler, LogHandler):
                self.tblView.setModel(handler.model)
                break

        stretch_col(self.tblView, 1)
        self.tblView.setColumnWidth(0, 30)
        self.tblView.setColumnWidth(2, 200)

        self.btnClose = push_btn(text='Close', properties=['confirm', 'cancel'])
        self.btnClose.clicked.connect(self.accept)

        self.frame.layout().addWidget(self.btnReset, alignment=Qt.AlignmentFlag.AlignRight)
        self.frame.layout().addWidget(self.tblView)
        self.frame.layout().addWidget(self.btnClose, alignment=Qt.AlignmentFlag.AlignRight)

    def display(self):
        self.exec()
