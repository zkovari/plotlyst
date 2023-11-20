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
import uuid
from functools import partial
from typing import Dict, List

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QWidget, QTextEdit, QGridLayout
from qthandy import vbox, bold, line, margins, spacer, grid, hbox, italic
from qthandy.filter import VisibilityToggleEventFilter, OpacityEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.core.domain import TemplateValue, Topic, TopicType
from src.main.python.plotlyst.view.common import tool_btn, push_btn, action, fade_out_and_gc
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.button import CollapseButton
from src.main.python.plotlyst.view.widget.input import AutoAdjustableTextEdit, RemovalButton

topics: Dict[TopicType, List[Topic]] = {
    TopicType.Physical: [
        Topic('Clothing', TopicType.Physical, uuid.UUID('4572a00f-9039-43a1-8eb9-8abd39fbec32'), 'fa5s.tshirt', ''),
        Topic('Marks of scars', TopicType.Physical, uuid.UUID('088ae5e0-99f8-4308-9d77-3daa624ca7a3'),
              'mdi.bandage',
              '')],
    TopicType.Habits: [
        Topic('Exercise and fitness', TopicType.Habits, uuid.UUID('0e3e6e19-b284-4f7d-85ef-ce2ba047743c'),
              'mdi.dumbbell', ''),
    ],
    TopicType.Skills: [],
    TopicType.Fears: [],
    TopicType.Background: [],
    TopicType.Hobbies: [],
    TopicType.Communication: [],
    TopicType.Beliefs: [],
}


class TopicGroupWidget(QWidget):
    removed = pyqtSignal()

    def __init__(self, topicType: TopicType, parent=None):
        super().__init__(parent)
        self._type = topicType
        vbox(self)

        self.btnHeader = CollapseButton(Qt.Edge.BottomEdge, Qt.Edge.RightEdge)
        self.btnHeader.setIconSize(QSize(16, 16))
        self.btnHeader.setText(self._type.name)
        self.btnHeader.setToolTip(self._type.description())
        bold(self.btnHeader)
        self.btnEdit = tool_btn(IconRegistry.edit_icon(), transparent_=True)
        self.btnEdit.installEventFilter(OpacityEventFilter(self.btnEdit))
        self.menuTopics = MenuWidget(self.btnEdit)
        self._topicActions: Dict[Topic, QAction] = {}
        self._topicWidgets: Dict[Topic, TopicWidget] = {}
        for topic in topics[self._type]:
            action_ = action(topic.text, icon=IconRegistry.from_name(topic.icon), tooltip=topic.description,
                             slot=partial(self.addTopic, topic))
            self._topicActions[topic] = action_
            self.menuTopics.addAction(action_)

        self.btnRemoval = RemovalButton()
        self.btnRemoval.clicked.connect(self._removed)

        self.wdgHeader = QWidget()
        hbox(self.wdgHeader)
        self.wdgHeader.layout().addWidget(self.btnHeader)
        self.wdgHeader.layout().addWidget(self.btnEdit)
        self.wdgHeader.layout().addWidget(spacer())
        self.wdgHeader.layout().addWidget(self.btnRemoval)
        self.wdgTopics = QWidget()
        self.btnAddTopic = push_btn(IconRegistry.plus_icon('grey'), 'Add topic', transparent_=True)
        italic(self.btnAddTopic)
        self.btnAddTopic.installEventFilter(OpacityEventFilter(self.btnAddTopic))
        self.btnAddTopic.clicked.connect(lambda: self.menuTopics.exec())

        vbox(self.wdgTopics)
        self.wdgTopics.layout().addWidget(self.btnAddTopic)
        self.btnHeader.toggled.connect(self.wdgTopics.setHidden)

        self.installEventFilter(VisibilityToggleEventFilter(self.btnEdit, self.wdgHeader))
        self.installEventFilter(VisibilityToggleEventFilter(self.btnRemoval, self.wdgHeader))

        self.layout().addWidget(self.wdgHeader)
        self.layout().addWidget(line())
        self.layout().addWidget(self.wdgTopics)

    def addTopic(self, topic: Topic):
        wdg = TopicWidget(topic, TemplateValue(topic.id, ''))
        wdg.removalRequested.connect(partial(self._removeTopic, topic))
        self._topicWidgets[topic] = wdg
        self.btnAddTopic.setHidden(True)
        self.wdgTopics.layout().addWidget(wdg)

        self._topicActions[topic].setDisabled(True)

    def _removed(self):
        self.removed.emit()
        pass

    def _removeTopic(self, topic: Topic):
        wdg = self._topicWidgets.pop(topic)
        fade_out_and_gc(self.wdgTopics, wdg)
        self._topicActions[topic].setEnabled(True)


class TopicWidget(QWidget):
    removalRequested = pyqtSignal()

    def __init__(self, topic: Topic, value: TemplateValue, parent=None):
        super(TopicWidget, self).__init__(parent)

        self._topic = topic
        self._value = value

        self.btnHeader = push_btn(IconRegistry.from_name(topic.icon, topic.icon_color), topic.text,
                                  tooltip=topic.description, transparent_=True)

        self.textEdit = AutoAdjustableTextEdit(height=40)
        self.textEdit.setProperty('rounded', True)
        self.textEdit.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
        self.textEdit.setTabChangesFocus(True)
        self.textEdit.setMarkdown(value.value)

        self.textEdit.textChanged.connect(self._textChanged)

        self._btnRemoval = RemovalButton()
        self._btnRemoval.clicked.connect(self.removalRequested.emit)

        self._top = group(self.btnHeader, spacer(), self._btnRemoval, margin=0, spacing=1)
        margins(self._top, left=20)
        layout_ = vbox(self)
        layout_.addWidget(self._top)
        self._top.installEventFilter(VisibilityToggleEventFilter(self._btnRemoval, self._top))

        bottom = group(self.textEdit, vertical=False, margin=0, spacing=0)
        margins(bottom, left=20)
        layout_.addWidget(bottom, alignment=Qt.AlignmentFlag.AlignTop)

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
    topicGroupRemoved = pyqtSignal(TopicType)

    def __init__(self, parent=None):
        super(TopicsEditor, self).__init__(parent)
        self._gridLayout: QGridLayout = grid(self)

        self._topicGroups: Dict[TopicType, TopicGroupWidget] = {}

    def addTopicGroup(self, topicType: TopicType):
        wdg = TopicGroupWidget(topicType)
        wdg.removed.connect(partial(self.removeTopicGroup, topicType))
        self._topicGroups[topicType] = wdg

        self._gridLayout.addWidget(wdg, topicType.value, 0)

    def removeTopicGroup(self, topicType: TopicType):
        wdg = self._topicGroups.pop(topicType)
        fade_out_and_gc(self, wdg)
        self.topicGroupRemoved.emit(topicType)
    # def addTopic(self, topic: Topic, value: TemplateValue):
    #     wdg = TopicWidget(topic, value, self)
    #     self._topics[topic] = wdg
    #     insert_before_the_end(self, wdg)
    #     if self.isVisible():
    #         anim = qtanim.fade_in(wdg, duration=200)
    #         anim.finished.connect(wdg.activate)
    #     else:
    #         wdg.activate()
    #
    #     wdg.removalRequested.connect(partial(self._removeTopic, topic))
    #
    # def _removeTopic(self, topic: Topic):
    #     wdg = self._topics[topic]
    #
    #     if not wdg.plainText() or ask_confirmation(f'Remove topic "{topic.text}"?'):
    #         self._topics.pop(topic)
    #         value = wdg.value()
    #         fade_out_and_gc(self, wdg)
    #         self.topicRemoved.emit(topic, value)
