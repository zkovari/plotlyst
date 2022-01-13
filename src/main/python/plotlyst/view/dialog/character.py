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
from typing import Optional, Dict

import emoji
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QToolButton, QButtonGroup
from fbs_runtime import platform

from src.main.python.plotlyst.core.domain import BackstoryEvent, NEUTRAL, VERY_HAPPY, VERY_UNHAPPY, UNHAPPY, HAPPY, \
    BackstoryEventType
from src.main.python.plotlyst.view.common import emoji_font, InstantTooltipStyle
from src.main.python.plotlyst.view.generated.backstory_editor_dialog_ui import Ui_BackstoryEditorDialog
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import FlowLayout


class _BackstoryEventTypeButton(QToolButton):
    def __init__(self, type: BackstoryEventType, parent=None):
        super(_BackstoryEventTypeButton, self).__init__(parent)
        self.type = type
        if type == BackstoryEventType.Event:
            self._color = 'darkBlue'
            self.setIcon(IconRegistry.from_name('ri.calendar-event-fill', self._color))
        self.setToolTip(f'<html><b>{type.name}</b></html>')
        self.setStyleSheet(f'QToolTip {{color: {self._color}}}')

        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)

        self.setStyle(InstantTooltipStyle(self.style()))


class BackstoryEditorDialog(QDialog, Ui_BackstoryEditorDialog):
    def __init__(self, backstory: Optional[BackstoryEvent] = None, parent=None):
        super(BackstoryEditorDialog, self).__init__(parent)
        self.setupUi(self)

        if platform.is_windows():
            self._emoji_font = emoji_font(14)
        else:
            self._emoji_font = emoji_font(20)

        self.btnVeryUnhappy.setFont(self._emoji_font)
        self.btnVeryUnhappy.setText(emoji.emojize(':fearful_face:'))
        self.btnUnHappy.setFont(self._emoji_font)
        self.btnUnHappy.setText(emoji.emojize(':worried_face:'))
        self.btnNeutral.setFont(self._emoji_font)
        self.btnNeutral.setText(emoji.emojize(':neutral_face:'))
        self.btnHappy.setFont(self._emoji_font)
        self.btnHappy.setText(emoji.emojize(':slightly_smiling_face:'))
        self.btnVeryHappy.setFont(self._emoji_font)
        self.btnVeryHappy.setText(emoji.emojize(':smiling_face_with_smiling_eyes:'))

        self.wdgTypes.setLayout(FlowLayout(2, 3))
        self._btnTypeGroup = QButtonGroup(self)
        self._btnTypeGroup.setExclusive(True)

        self._typeButtons: Dict[BackstoryEventType, QToolButton] = {}
        for event in BackstoryEventType:
            btn = _BackstoryEventTypeButton(event)
            self._typeButtons[event] = btn
            self._btnTypeGroup.addButton(btn)
            self.wdgTypes.layout().addWidget(btn)

        self.lineKeyphrase.textChanged.connect(lambda x: self.btnSave.setEnabled(len(x) > 0))

        self.btnSave.setDisabled(True)
        self.btnSave.clicked.connect(self.accept)
        self.btnClose.clicked.connect(self.reject)

        self._typeButtons[BackstoryEventType.Event].setChecked(True)

        if backstory:
            self.lineKeyphrase.setText(backstory.keyphrase)

            if backstory.emotion == VERY_UNHAPPY:
                self.btnVeryUnhappy.setChecked(True)
            if backstory.emotion == UNHAPPY:
                self.btnUnHappy.setChecked(True)
            if backstory.emotion == NEUTRAL:
                self.btnNeutral.setChecked(True)
            if backstory.emotion == HAPPY:
                self.btnHappy.setChecked(True)
            if backstory.emotion == VERY_HAPPY:
                self.btnVeryHappy.setChecked(True)

            self._typeButtons[backstory.type].setChecked(True)

    def display(self) -> Optional[BackstoryEvent]:
        result = self.exec()
        if result == QDialog.Rejected:
            return None

        emotion = NEUTRAL
        if self.btnVeryUnhappy.isChecked():
            emotion = VERY_UNHAPPY
        elif self.btnUnHappy.isChecked():
            emotion = UNHAPPY
        elif self.btnHappy.isChecked():
            emotion = HAPPY
        elif self.btnVeryHappy.isChecked():
            emotion = VERY_HAPPY

        return BackstoryEvent(self.lineKeyphrase.text(), synopsis='', emotion=emotion)
