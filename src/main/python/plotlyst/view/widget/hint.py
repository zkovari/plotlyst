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

import qtanim
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QFrame, QPushButton
from overrides import overrides
from qthandy import vbox

from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.settings import settings
from src.main.python.plotlyst.view.common import hmax
from src.main.python.plotlyst.view.generated.hint.scenes_view_hint_ui import Ui_ScenesViewHintWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.input import RemovalButton


class HintWidget(QFrame):
    def __init__(self, parent=None):
        super(HintWidget, self).__init__(parent)

        if app_env.test_env() or settings.hint_showed(self.id()):
            # self._shownAlready = True
            self.setHidden(True)
            return

        self.setLineWidth(1)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet('''
            HintWidget {
                border: 2px solid #7209b7;
                border-radius: 4px;
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                      stop: 0 #4e4187);
            }
        ''')

        self.wdgHint = QWidget(self)
        self.setupUi(self.wdgHint)

        vbox(self)
        self.btnRemoval = RemovalButton()

        top = group(self.wdgHint, self.btnRemoval, margin=0, spacing=0)
        top.layout().setAlignment(self.btnRemoval, Qt.AlignTop)
        self.layout().addWidget(top)
        self.btnOkay = QPushButton()
        self.btnOkay.setProperty('base', True)
        self.btnOkay.setText('Okay, understood')
        self.btnOkay.setIcon(IconRegistry.from_name('fa5s.thumbs-up', '#7209b7'))
        self.btnOkay.setCursor(Qt.PointingHandCursor)
        hmax(self.btnOkay)
        self.layout().addWidget(self.btnOkay, alignment=Qt.AlignRight)

        self.btnRemoval.clicked.connect(self._hide)
        self.btnOkay.clicked.connect(self._hide)

    # @overrides
    # def showEvent(self, event: QtGui.QShowEvent) -> None:
    #     if not self._shownAlready:
    #         settings.set_hint_showed(self.id())

    @abstractmethod
    def id(self) -> str:
        pass

    def _hide(self):
        qtanim.fade_out(self, duration=100)


class ScenesViewHintWidget(HintWidget, Ui_ScenesViewHintWidget):

    @overrides
    def id(self) -> str:
        return 'scenesView'
