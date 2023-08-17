"""
Plotlyst
Copyright (C) 2021-2023  Zsolt Kovari

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
from typing import Dict

import qtanim
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import QWidget, QPushButton, QTextEdit
from qthandy import vbox, bold, line, transparent, margins, vspacer, spacer, ask_confirmation
from qthandy.filter import VisibilityToggleEventFilter

from src.main.python.plotlyst.core.domain import TemplateValue, Topic
from src.main.python.plotlyst.view.common import pointy, insert_before_the_end, fade_out_and_gc
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.button import CollapseButton
from src.main.python.plotlyst.view.widget.input import AutoAdjustableTextEdit, RemovalButton


class TopicWidget(QWidget):
    removalRequested = pyqtSignal()

    def __init__(self, topic: Topic, value: TemplateValue, parent=None):
        super(TopicWidget, self).__init__(parent)

        self._topic = topic
        self._value = value

        self.btnHeader = QPushButton()
        self.btnHeader.setText(topic.text)
        self.btnHeader.setToolTip(topic.description)
        if topic.icon:
            self.btnHeader.setIcon(IconRegistry.from_name(topic.icon, topic.icon_color))

        self.btnCollapse = CollapseButton(Qt.Edge.BottomEdge, Qt.Edge.RightEdge)
        self.btnCollapse.setIconSize(QSize(16, 16))

        pointy(self.btnHeader)
        transparent(self.btnHeader)
        bold(self.btnHeader)

        self.textEdit = AutoAdjustableTextEdit(height=80)
        self.textEdit.setProperty('rounded', True)
        self.textEdit.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
        self.textEdit.setTabChangesFocus(True)
        self.textEdit.setMarkdown(value.value)

        self.textEdit.textChanged.connect(self._textChanged)

        self._btnRemoval = RemovalButton()
        self._btnRemoval.clicked.connect(self.removalRequested.emit)

        self._top = group(self.btnCollapse, self.btnHeader, spacer(), self._btnRemoval, margin=0, spacing=1)
        layout_ = vbox(self)
        layout_.addWidget(self._top)
        self._top.installEventFilter(VisibilityToggleEventFilter(self._btnRemoval, self._top))

        line_ = line(color=topic.icon_color)
        middle = group(line_, margin=0, spacing=0)
        margins(middle, left=20)
        layout_.addWidget(middle)

        bottom = group(self.textEdit, vertical=False, margin=0, spacing=0)
        margins(bottom, left=20)
        layout_.addWidget(bottom, alignment=Qt.AlignmentFlag.AlignTop)

        self.btnHeader.clicked.connect(self.btnCollapse.toggle)
        self.btnCollapse.toggled.connect(self.textEdit.setHidden)

    def activate(self):
        self.textEdit.setFocus()
        self.textEdit.setPlaceholderText(f'Write about {self._topic.text.lower()}')

    def value(self):
        return self._value

    def plainText(self) -> str:
        return self.textEdit.toPlainText()

    def _textChanged(self):
        self._value.value = self.textEdit.toMarkdown()


class TopicsEditor(QWidget):
    topicRemoved = pyqtSignal(Topic, TemplateValue)

    def __init__(self, parent=None):
        super(TopicsEditor, self).__init__(parent)
        vbox(self)

        self._topics: Dict[Topic, TopicWidget] = {}
        self.layout().addWidget(vspacer())

    def addTopic(self, topic: Topic, value: TemplateValue):
        wdg = TopicWidget(topic, value, self)
        self._topics[topic] = wdg
        insert_before_the_end(self, wdg)
        if self.isVisible():
            anim = qtanim.fade_in(wdg, duration=200)
            anim.finished.connect(wdg.activate)
        else:
            wdg.activate()

        wdg.removalRequested.connect(partial(self._removeTopic, topic))

    def _removeTopic(self, topic: Topic):
        wdg = self._topics[topic]

        if not wdg.plainText() or ask_confirmation(f'Remove topic "{topic.text}"?'):
            self._topics.pop(topic)
            value = wdg.value()
            fade_out_and_gc(self, wdg)
            self.topicRemoved.emit(topic, value)
