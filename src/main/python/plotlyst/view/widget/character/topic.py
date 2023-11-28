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
from typing import Optional, Dict

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QWidget
from qthandy import vbox, vspacer
from qtmenu import MenuWidget, ActionTooltipDisplayMode

from src.main.python.plotlyst.core.domain import Character, Topic, TemplateValue, TopicType
from src.main.python.plotlyst.view.common import push_btn, scrolled, action
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.topic import TopicsEditor, topic_ids


# default_topics: List[Topic] = [
#     Topic('Family', uuid.UUID('2ce9c3b4-1dd9-4f88-a16e-b8dc507633b7'), 'mdi6.human-male-female-child', '#457b9d'),
#     Topic('Job', uuid.UUID('19d9bfe9-5432-42d8-a444-0bd849720b2d'), 'fa5s.briefcase', '#9c6644'),
#     Topic('Education', uuid.UUID('01e9ef93-7a71-4b2d-af88-53b30d3947cb'), 'fa5s.graduation-cap'),
#     Topic('Hometown', uuid.UUID('1ac1eec9-7953-419c-a265-88a0723a64ea'), 'ei.home-alt', '#4c334d'),
#     Topic('Physical appearance', uuid.UUID('3c1a00d2-5085-47f0-8fe5-6d253e708999'), 'ri.body-scan-fill', ''),
#     Topic('Scars, injuries', uuid.UUID('088ae5e0-99f8-4308-9d77-3daa624ca7a3'), 'mdi.bandage', ''),
#     Topic('Clothing', uuid.UUID('4572a00f-9039-43a1-8eb9-8abd39fbec32'), 'fa5s.tshirt', ''),
#     Topic('Accessories', uuid.UUID('eaab9129-576a-4042-9dfc-eedce3f6f3ab'), 'fa5s.glasses', ''),
#     Topic('Health', uuid.UUID('ec218ea4-d8f9-4eb7-9850-1ce0e7eff5e6'), 'mdi.hospital-box', ''),
#     Topic('Handwriting', uuid.UUID('65a43dc8-ee8d-4a4a-adb9-ee8a0e246e33'), 'mdi.signature-freehand', ''),
#     Topic('Gait', uuid.UUID('26bdeb49-116a-470a-8427-2e5c061243a8'), 'mdi.motion-sensor', ''),
#
#     Topic('Friends', uuid.UUID('d6d78fc4-d9d4-497b-8b61-cca465d5e8e7'), 'fa5s.user-friends', '#457b9d'),
#     Topic('Relationships', uuid.UUID('62f5e2b6-ac35-4b6e-ae3b-bfd5b083b026'), 'ei.heart', '#e63946'),
#
#     Topic('Faith', uuid.UUID('c4df6cdb-c92d-421b-8a2e-77598fc475a3'), 'fa5s.hands', ''),
#     Topic('Spirituality', uuid.UUID('01f750eb-c6e1-4efb-b32c-76cb1d7a33f6'), 'mdi6.meditation', ''),
#
#     Topic('Sport', uuid.UUID('d1e898d3-f9cc-4f65-8cfa-cc1a0c8cd8a2'), 'fa5.futbol', '#0096c7'),
#     Topic('Fitness', uuid.UUID('0e3e6e19-b284-4f7d-85ef-ce2ba047743c'), 'mdi.dumbbell', ''),
#     Topic('Hobby', uuid.UUID('97c66076-e97d-4f11-a20d-1ae6ff6ba246'), 'fa5s.book-reader', ''),
#     Topic('Art', uuid.UUID('ed6749da-d1b0-49cd-becf-c7ddc67725d2'), 'ei.picture', ''),
# ]


class CharacterTopicGroupSelector(MenuWidget):
    topicGroupTriggered = pyqtSignal(TopicType)

    def __init__(self, character: Character, parent=None):
        super().__init__(parent)
        self._character = character
        self._actions: Dict[TopicType, QAction] = {}
        self.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)

        for topic_group in TopicType:
            action_ = action(topic_group.name, icon=IconRegistry.from_name(topic_group.icon()), tooltip=topic_group.description())
            self._actions[topic_group] = action_
            action_.triggered.connect(partial(self.topicGroupTriggered.emit, topic_group))
            self.addAction(action_)

    def updateTopic(self, topicType: TopicType, enabled: bool):
        self._actions[topicType].setEnabled(enabled)


class CharacterTopicsEditor(QWidget):
    def __init__(self, parent=None):
        super(CharacterTopicsEditor, self).__init__(parent)
        self._character: Optional[Character] = None
        self._menu: Optional[CharacterTopicGroupSelector] = None

        self.btnAdd = push_btn(IconRegistry.plus_icon('white'), 'Add category', properties=['base', 'positive'])

        self._wdgTopics = TopicsEditor(self)
        vbox(self, 0, 0)
        self.layout().addWidget(self.btnAdd, alignment=Qt.AlignmentFlag.AlignLeft)
        self._scrollarea, self._wdgCenter = scrolled(self, frameless=True)
        self._wdgCenter.setProperty('relaxed-white-bg', True)
        vbox(self._wdgCenter)
        self._wdgCenter.layout().addWidget(self._wdgTopics)
        self._wdgCenter.layout().addWidget(vspacer())
        self._wdgTopics.topicGroupRemoved.connect(self._topicGroupRemoved)
        self._wdgTopics.topicAdded.connect(self._topicAdded)
        self._wdgTopics.topicRemoved.connect(self._topicRemoved)

    def setCharacter(self, character: Character):
        self._character = character
        self._menu = CharacterTopicGroupSelector(self._character, self.btnAdd)
        self._menu.topicGroupTriggered.connect(self._addTopicGroup)

        for value in character.topics:
            topic = topic_ids.get(str(value.id))
            if topic:
                topicType = TopicType(topic.type)
                self._wdgTopics.addTopic(topic, topicType, value)
                self._menu.updateTopic(topicType, False)

    def _addTopicGroup(self, topicType: TopicType):
        if self._character is None:
            return
        self._wdgTopics.addTopicGroup(topicType)

        self._menu.updateTopic(topicType, False)

    def _topicGroupRemoved(self, topicType: TopicType):
        self._menu.updateTopic(topicType, True)

    def _topicAdded(self, topic: Topic, value: TemplateValue):
        self._character.topics.append(value)

    def _topicRemoved(self, topic: Topic, value: TemplateValue):
        self._character.topics.remove(value)
