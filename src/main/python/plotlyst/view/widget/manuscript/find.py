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
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QStackedWidget, QWidget
from overrides import overrides
from qthandy import incr_font, vbox, sp, incr_icon

from plotlyst.common import RELAXED_WHITE_COLOR
from plotlyst.core.domain import Novel
from plotlyst.view.common import push_btn, link_editor_to_btn
from plotlyst.view.icons import IconRegistry
from plotlyst.view.layout import group
from plotlyst.view.widget.display import PopupDialog, Icon
from plotlyst.view.widget.input import SearchField


class ManuscriptFindPopup(PopupDialog):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel

        self.search = SearchField()
        incr_font(self.search.lineSearch)

        incr_icon(self.btnReset, 4)

        self.btnFind = push_btn(IconRegistry.from_name('fa5s.search', RELAXED_WHITE_COLOR),
                                text='Search', tooltip='Search for text', properties=['confirm', 'positive'])

        link_editor_to_btn(self.search.lineSearch, self.btnFind)
        self.btnFind.setDisabled(True)
        self.btnFind.clicked.connect(self._search)

        self.stack = QStackedWidget()
        sp(self.stack).v_exp().h_exp()
        self.pageEmpty = QWidget()
        vbox(self.pageEmpty)
        icon = Icon()
        icon.setIcon(IconRegistry.from_name('fa5s.search', 'lightgrey', hflip=True))
        icon.setIconSize(QSize(128, 128))
        self.pageEmpty.layout().addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack.addWidget(self.pageEmpty)

        self.btnCancel = push_btn(text='Close', properties=['confirm', 'cancel'])
        self.btnCancel.clicked.connect(self.reject)

        # self.frame.layout().addWidget(label('Search', h5=True), alignment=Qt.AlignmentFlag.AlignCenter)
        self.frame.layout().addWidget(self.btnReset, alignment=Qt.AlignmentFlag.AlignRight)
        self.frame.layout().addWidget(group(self.search, self.btnFind, spacing=20),
                                      alignment=Qt.AlignmentFlag.AlignLeft)

        self.frame.layout().addWidget(self.stack)

        self.frame.layout().addWidget(self.btnCancel, alignment=Qt.AlignmentFlag.AlignRight)

    @overrides
    def sizeHint(self) -> QSize:
        return self._adjustedSize(0.8, 0.8, 600, 500)

    def display(self):
        self.search.lineSearch.setFocus()
        self.exec()
    
    def _search(self):
        term = self.search.lineSearch.text()
