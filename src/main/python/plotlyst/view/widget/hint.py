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
from abc import abstractmethod
from enum import Enum
from typing import Optional

import qtanim
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QFrame, QPushButton, QApplication, QLabel
from overrides import overrides
from qthandy import vbox, ask_confirmation, busy, bold, incr_font

from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import emit_info
from src.main.python.plotlyst.service.persistence import flush_or_fail
from src.main.python.plotlyst.settings import settings
from src.main.python.plotlyst.view.common import hmax
from src.main.python.plotlyst.view.generated.hint.scenes_view_hint_ui import Ui_ScenesViewHintWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.input import RemovalButton


class HintId(Enum):
    SCENES_VIEW = 'scenesViewHint'
    SCENES_VIEW_2 = 'scenesViewHint2'
    SCENES_VIEW_3 = 'scenesViewHint3'


@busy
def reset_hints():
    if ask_confirmation('Display all hint messages again? The application will shut down first.'):
        for id_ in HintId:
            settings.reset_hint_showed(id_.value)

        emit_info('Application is shutting down. Persist workspace...')
        flush_or_fail()
        QApplication.exit()


class HintWidget(QFrame):
    next = pyqtSignal()

    def __init__(self, parent=None, previous: Optional['HintWidget'] = None, has_next: bool = False):
        super(HintWidget, self).__init__(parent)
        self.previous = previous
        self.has_next = has_next

        if app_env.test_env() or settings.hint_showed(self.id().value):
            self.setHidden(True)
            return

        self.setLineWidth(1)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet('''
            HintWidget {
                border: 2px solid #7209b7;
                border-radius: 4px;
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                      stop: 0 #dec9e9);
            }
        ''')

        self.wdgHint = QWidget(self)
        self.setupUi(self.wdgHint)

        vbox(self)
        self.btnRemoval = RemovalButton()

        self.lblTitle = QLabel()
        bold(self.lblTitle)
        incr_font(self.lblTitle, 2)
        self.lblTitle.setText(self.title())

        top = group(self.lblTitle, self.btnRemoval, spacing=0)
        self.layout().addWidget(top)
        self.layout().addWidget(self.wdgHint)
        if self.has_next:
            self.btnAction = QPushButton()
            self.btnAction.setIcon(IconRegistry.arrow_right_thick_icon())
        else:
            self.btnAction = QPushButton()
            self.btnAction.setText('Okay, understood')
            self.btnAction.setIcon(IconRegistry.from_name('fa5s.thumbs-up', '#7209b7'))
        self.btnAction.setProperty('base', True)
        self.btnAction.setCursor(Qt.CursorShape.PointingHandCursor)
        hmax(self.btnAction)
        self.layout().addWidget(self.btnAction, alignment=Qt.AlignmentFlag.AlignRight)

        self.btnRemoval.clicked.connect(self._action)
        self.btnAction.clicked.connect(self._action)

        if self.previous and not settings.hint_showed(self.previous.id().value):
            self.setHidden(True)
            self.previous.next.connect(lambda: qtanim.fade_in(self, duration=150))

    @abstractmethod
    def id(self) -> HintId:
        pass

    def title(self) -> str:
        return 'Hint'

    def previous_id(self) -> str:
        return ''

    def next_id(self) -> str:
        return ''

    def _action(self):
        settings.set_hint_showed(self.id().value)
        qtanim.fade_out(self, duration=100)
        if self.has_next:
            self.next.emit()


class ScenesViewHintWidget(HintWidget, Ui_ScenesViewHintWidget):

    @overrides
    def title(self) -> str:
        return 'Scenes view 1/3'

    @overrides
    def id(self) -> HintId:
        return HintId.SCENES_VIEW


class ScenesViewHintWidget2(HintWidget, Ui_ScenesViewHintWidget):

    @overrides
    def title(self) -> str:
        return 'Scenes view 2/3'

    @overrides
    def id(self) -> HintId:
        return HintId.SCENES_VIEW_2


class ScenesViewHintWidget3(HintWidget, Ui_ScenesViewHintWidget):

    @overrides
    def title(self) -> str:
        return 'Scenes view 3/3'

    @overrides
    def id(self) -> HintId:
        return HintId.SCENES_VIEW_3
