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
from typing import Dict

import qtanim
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget
from qthandy import incr_font, vbox, retain_when_hidden, gc

from src.main.python.plotlyst.core.domain import MiceQuotient, Document, MiceThread, MiceType
from src.main.python.plotlyst.view.common import VisibilityToggleEventFilter
from src.main.python.plotlyst.view.generated.mice_doc_ui import Ui_MiceQuotientDoc
from src.main.python.plotlyst.view.generated.mice_thread_ui import Ui_MiceThread
from src.main.python.plotlyst.view.icons import IconRegistry

mice_colors: Dict[MiceType, str] = {MiceType.MILIEU: '#2d6a4f',
                                    MiceType.INQUIRY: '#7b2cbf',
                                    MiceType.CHARACTER: 'darkBlue',
                                    MiceType.EVENT: '#d90429'}


class MiceThreadWidget(QWidget, Ui_MiceThread):
    removed = pyqtSignal(QWidget)

    def __init__(self, thread: MiceThread, parent=None):
        super(MiceThreadWidget, self).__init__(parent)
        self.setupUi(self)
        self.thread = thread
        if thread.type == MiceType.MILIEU:
            self.icon.setIcon(IconRegistry.from_name('fa5s.map-marked-alt', mice_colors[MiceType.MILIEU]))
        elif thread.type == MiceType.INQUIRY:
            self.icon.setIcon(IconRegistry.from_name('ei.question', mice_colors[MiceType.INQUIRY]))
        elif thread.type == MiceType.CHARACTER:
            self.icon.setIcon(IconRegistry.from_name('fa5s.user', mice_colors[MiceType.CHARACTER]))
        else:
            self.icon.setIcon(IconRegistry.from_name('fa5s.meteor', mice_colors[MiceType.EVENT]))

        self.lineText.setStyleSheet(f'border: 1px solid {mice_colors[thread.type]}')
        self.lineText.setText(thread.text)

        retain_when_hidden(self.btnRemoval)
        self.installEventFilter(VisibilityToggleEventFilter(target=self.btnRemoval, parent=self))

        self.btnRemoval.clicked.connect(lambda: self.removed.emit(self))


class MiceQuotientDoc(QWidget, Ui_MiceQuotientDoc):
    def __init__(self, doc: Document, mice: MiceQuotient, parent=None):
        super(MiceQuotientDoc, self).__init__(parent)
        self.setupUi(self)
        self.doc = doc
        self.mice = mice

        color = mice_colors[MiceType.MILIEU]
        self.btnMilieu.initStyleSheet(color, color=color)
        color = mice_colors[MiceType.INQUIRY]
        self.btnInquiry.initStyleSheet(color, color=color)
        color = mice_colors[MiceType.CHARACTER]
        self.btnCharacter.initStyleSheet(color, color=color)
        color = mice_colors[MiceType.EVENT]
        self.btnEvent.initStyleSheet(color, color=color)

        incr_font(self.btnTitle, 15)

        self.btnTitle.setText(self.doc.title)
        self.btnTitle.setIcon(IconRegistry.from_name(self.doc.icon, self.doc.icon_color))

        self.btnMilieu.clicked.connect(lambda: self._addThread(MiceType.MILIEU))
        self.btnInquiry.clicked.connect(lambda: self._addThread(MiceType.INQUIRY))
        self.btnCharacter.clicked.connect(lambda: self._addThread(MiceType.CHARACTER))
        self.btnEvent.clicked.connect(lambda: self._addThread(MiceType.EVENT))

        vbox(self.wdgThreads)

    def _addThread(self, type: MiceType):
        thread = MiceThread(type)
        self.mice.threads.append(thread)
        widget = MiceThreadWidget(thread, self.wdgThreads)
        widget.removed.connect(self._removeThreadWidget)

        self.wdgThreads.layout().addWidget(widget)
        anim = qtanim.glow(widget, color=QColor(mice_colors[type]))
        anim.finished.connect(lambda: widget.setGraphicsEffect(None))

    def _removeThreadWidget(self, widget: MiceThreadWidget):
        self.mice.threads.remove(widget.thread)
        self.wdgThreads.layout().removeWidget(widget)
        gc(widget)
