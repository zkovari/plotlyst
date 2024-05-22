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
import random

import qtanim
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget
from qthandy import incr_font, flow, margins, vbox, hbox, pointy
from qthandy.filter import OpacityEventFilter

from plotlyst.common import RELAXED_WHITE_COLOR, PLOTLYST_MAIN_COLOR, PLOTLYST_SECONDARY_COLOR
from plotlyst.core.domain import Document
from plotlyst.view.common import link_buttons_to_pages, ButtonPressResizeEventFilter, frame
from plotlyst.view.generated.premise_builder_widget_ui import Ui_PremiseBuilderWidget
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.input import AutoAdjustableTextEdit, TextAreaInputDialog


class IdeaWidget(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)

        self.frame = frame()
        self.frame.setObjectName('mainFrame')
        pointy(self.frame)

        self.textEdit = AutoAdjustableTextEdit()
        self.textEdit.setProperty('transparent', True)
        self.textEdit.setText(text)
        self.textEdit.setReadOnly(True)
        pointy(self.textEdit)
        font: QFont = self.textEdit.font()
        font.setPointSize(16)
        self.textEdit.setFont(font)

        vbox(self, 0, 0)
        lm = self.__randomMargin()
        tm = self.__randomMargin()
        rm = self.__randomMargin()
        bm = self.__randomMargin()
        margins(self, left=lm, top=tm, right=rm, bottom=bm)
        self.setMaximumWidth(random.randint(170, 210))
        self.layout().addWidget(self.frame)

        hbox(self.frame, 5, 0).addWidget(self.textEdit)

        self.setStyleSheet(f'''
            #mainFrame {{
                background: {PLOTLYST_SECONDARY_COLOR};
                border: 1px solid {PLOTLYST_SECONDARY_COLOR};
                border-radius: 18px;
            }}
            QTextEdit {{
                color: {RELAXED_WHITE_COLOR};
                border: 0px;
                padding: 4px;
                background-color: rgba(0, 0, 0, 0);
            }}
        ''')

        self.installEventFilter(OpacityEventFilter(self, enterOpacity=0.7, leaveOpacity=1.0))
    # @overrides
    # def paintEvent(self, event: QPaintEvent) -> None:
    #     pass

    def __randomMargin(self) -> int:
        return random.randint(3, 15)


class PremiseBuilderWidget(QWidget, Ui_PremiseBuilderWidget):
    def __init__(self, doc: Document, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._doc = doc

        self.btnSeed.setIcon(IconRegistry.from_name('fa5s.seedling', color_on=PLOTLYST_MAIN_COLOR))
        self.btnConcept.setIcon(IconRegistry.from_name('fa5s.question-circle', color_on=PLOTLYST_MAIN_COLOR))
        self.btnPremise.setIcon(IconRegistry.from_name('fa5s.scroll', color_on=PLOTLYST_MAIN_COLOR))

        incr_font(self.btnSeed, 2)
        incr_font(self.btnConcept, 2)
        incr_font(self.btnPremise, 2)

        self.btnNewIdea.setIcon(IconRegistry.plus_icon(RELAXED_WHITE_COLOR))
        self.btnNewIdea.installEventFilter(ButtonPressResizeEventFilter(self.btnNewIdea))
        self.btnNewIdea.clicked.connect(self._addNewIdea)
        self.btnNewConcept.setIcon(IconRegistry.plus_icon(RELAXED_WHITE_COLOR))
        self.btnNewConcept.installEventFilter(ButtonPressResizeEventFilter(self.btnNewConcept))

        link_buttons_to_pages(self.stackedWidget, [(self.btnSeed, self.pageSeed), (self.btnConcept, self.pageConcept),
                                                   (self.btnPremise, self.pagePremise)])
        self.btnSeed.setChecked(True)

        flow(self.wdgIdeasEditor)
        margins(self.wdgIdeasEditor, left=20, right=20, top=20)

    def _addNewIdea(self):
        text = TextAreaInputDialog.edit('Add a new idea', 'An idea...',
                                        "An idea about character, plot, event, situation, setting, theme, genre, etc.")
        if text:
            wdg = IdeaWidget(text)
            self.wdgIdeasEditor.layout().addWidget(wdg)
            qtanim.fade_in(wdg)
