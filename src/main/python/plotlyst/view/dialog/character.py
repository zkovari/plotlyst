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
from typing import Optional, Dict, Tuple

import emoji
import qtanim
from PyQt5.QtCore import Qt, QSize, QObject, QEvent
from PyQt5.QtWidgets import QDialog, QToolButton, QButtonGroup, QDialogButtonBox
from fbs_runtime import platform
from overrides import overrides

from src.main.python.plotlyst.core.domain import BackstoryEvent, NEUTRAL, VERY_HAPPY, VERY_UNHAPPY, UNHAPPY, HAPPY, \
    BackstoryEventType
from src.main.python.plotlyst.view.common import emoji_font, InstantTooltipStyle
from src.main.python.plotlyst.view.generated.backstory_editor_dialog_ui import Ui_BackstoryEditorDialog
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import FlowLayout


class _BackstoryEventTypeButton(QToolButton):
    def __init__(self, type: BackstoryEventType, parent=None):
        super(_BackstoryEventTypeButton, self).__init__(parent)
        self._icons: Dict[BackstoryEventType, Tuple[str, str]] = {
            BackstoryEventType.Event: ('ri.calendar-event-fill', 'darkBlue'),
            BackstoryEventType.Birthday: ('fa5s.birthday-cake', '#03543f'),
            BackstoryEventType.Education: ('fa5s.graduation-cap', 'black'),
            BackstoryEventType.Job: ('fa5s.briefcase', '#9c6644'),
            BackstoryEventType.Love: ('ei.heart', '#e63946'),
            BackstoryEventType.Friendship: ('fa5s.user-friends', '#457b9d'),
            BackstoryEventType.Death: ('fa5s.skull-crossbones', 'black'),
            BackstoryEventType.Violence: ('mdi.knife-military', '#6c757d'),
            BackstoryEventType.Accident: ('fa5s.car-crash', '#a0001c'),
            BackstoryEventType.Promotion: ('mdi.ladder', '#6f4518'),
            BackstoryEventType.Travel: ('fa5s.train', '#a0001c'),
            BackstoryEventType.Breakup: ('fa5s.heart-broken', '#a4133c'),
            BackstoryEventType.Farewell: ('mdi6.hand-wave', '#656d4a'),
            BackstoryEventType.Award: ('fa5s.award', '#40916c'),
            BackstoryEventType.Family: ('mdi6.human-male-female-child', '#34a0a4'),
            BackstoryEventType.Home: ('fa5s.home', '#4c334d'),
            BackstoryEventType.Game: ('mdi.gamepad-variant', '#277da1'),
            BackstoryEventType.Sport: ('fa5.futbol', '#0096c7'),
            BackstoryEventType.Crime: ('fa5s.gavel', '#a68a64'),
            BackstoryEventType.Gift: ('fa5s.gift', '#b298dc'),
            BackstoryEventType.Medical: ('fa5s.medkit', '#849669'),
            BackstoryEventType.Catastrophe: ('fa5s.meteor', '#f48c06'),
            BackstoryEventType.Fortune: ('ph.coin-fill', '#ffb703'),
            BackstoryEventType.Injury: ('fa5s.user-injured', '#c05299'),
            BackstoryEventType.Loss: ('mdi.trophy-broken', '#f9c74f'),
        }
        self.type = type
        self.color = 'black'

        self.color: str = self._icons[type][1]
        self.iconName: str = self._icons[type][0]
        self.setIcon(IconRegistry.from_name(self.iconName, self.color))

        self.setToolTip(f'<html><b>{type.name}</b></html>')
        self.setStyleSheet(f'QToolTip {{color: {self.color}}}')

        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(QSize(24, 24))

        self.setStyle(InstantTooltipStyle(self.style()))


class BackstoryEditorDialog(QDialog, Ui_BackstoryEditorDialog):
    def __init__(self, backstory: Optional[BackstoryEvent] = None, showRelationOption: bool = True, parent=None):
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

        self.btnSave = self.buttonBox.button(QDialogButtonBox.Ok)

        self.btnSave.installEventFilter(self)
        self.btnSave.setDisabled(True)

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
            self.cbRelated.setChecked(backstory.follow_up)

        if not showRelationOption:
            self.cbRelated.setChecked(False)
            self.cbRelated.setHidden(True)
            self.wdgRelation.setHidden(True)

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

        btn: _BackstoryEventTypeButton = self._btnTypeGroup.checkedButton()
        return BackstoryEvent(self.lineKeyphrase.text(), synopsis='', emotion=emotion,
                              type=btn.type, type_icon=btn.iconName, type_color=btn.color,
                              follow_up=self.cbRelated.isChecked())

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.MouseButtonRelease and not watched.isEnabled():
            qtanim.shake(self.lineKeyphrase)

        return super(BackstoryEditorDialog, self).eventFilter(watched, event)
