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
from functools import partial
from typing import Any

import qtanim
from PyQt6.QtCore import Qt, pyqtSignal, QAbstractListModel, QModelIndex
from PyQt6.QtGui import QFont, QMouseEvent, QResizeEvent
from PyQt6.QtWidgets import QWidget, QApplication
from overrides import overrides
from qthandy import incr_font, flow, margins, vbox, hbox, pointy
from qthandy.filter import OpacityEventFilter, VisibilityToggleEventFilter
from qtmenu import MenuWidget

from plotlyst.common import RELAXED_WHITE_COLOR, PLOTLYST_MAIN_COLOR, PLOTLYST_SECONDARY_COLOR
from plotlyst.core.domain import Document, PremiseBuilder, PremiseIdea, BoxParameters
from plotlyst.model.common import proxy
from plotlyst.view.common import link_buttons_to_pages, ButtonPressResizeEventFilter, frame, action, fade_out_and_gc
from plotlyst.view.generated.premise_builder_widget_ui import Ui_PremiseBuilderWidget
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.button import DotsMenuButton
from plotlyst.view.widget.input import AutoAdjustableTextEdit, TextAreaInputDialog


class IdeaWidget(QWidget):
    toggled = pyqtSignal()
    edit = pyqtSignal()
    remove = pyqtSignal()

    def __init__(self, idea: PremiseIdea, parent=None):
        super().__init__(parent)
        self._idea = idea

        self.frame = frame()
        self.frame.setObjectName('mainFrame')
        pointy(self.frame)

        self.textEdit = AutoAdjustableTextEdit()
        self.textEdit.setProperty('transparent', True)
        self.textEdit.setText(self._idea.text)
        self.textEdit.setReadOnly(True)
        pointy(self.textEdit)
        font: QFont = self.textEdit.font()
        font.setPointSize(16)
        self.textEdit.setFont(font)
        self.textEdit.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.btnMenu = DotsMenuButton(self.frame)
        self.btnMenu.setCursor(Qt.CursorShape.ArrowCursor)
        self.btnMenu.setHidden(True)

        self.menu = MenuWidget(self.btnMenu)
        self.menu.addAction(action('Edit', IconRegistry.edit_icon(), slot=self.edit))
        self.menu.addAction(action('Remove', IconRegistry.trash_can_icon(), slot=self.remove))

        vbox(self, 0, 0)
        margins(self, left=self._idea.params.lm, top=self._idea.params.tm, right=self._idea.params.rm,
                bottom=self._idea.params.bm)
        self.setMaximumWidth(self._idea.params.width)
        self.layout().addWidget(self.frame)

        hbox(self.frame, 5, 0).addWidget(self.textEdit)

        self.refresh()

        self.installEventFilter(OpacityEventFilter(self, enterOpacity=0.7, leaveOpacity=1.0))
        self.installEventFilter(VisibilityToggleEventFilter(self.btnMenu, self))
        self.btnMenu.raise_()

    def idea(self) -> PremiseIdea:
        return self._idea

    def text(self):
        return self.textEdit.toPlainText()

    def setText(self, text: str):
        self._idea.text = text
        self.textEdit.setText(text)

    def toggle(self):
        self._idea.selected = not self._idea.selected
        self.toggled.emit()
        self.refresh()

    def refresh(self):
        bg_color = PLOTLYST_SECONDARY_COLOR if self._idea.selected else '#ced4da'

        self.setStyleSheet(f'''
                #mainFrame {{
                    background: {bg_color};
                    border: 1px solid {bg_color};
                    border-radius: 18px;
                }}
                QTextEdit {{
                    color: {RELAXED_WHITE_COLOR};
                    border: 0px;
                    padding: 4px;
                    background-color: rgba(0, 0, 0, 0);
                }}
                ''')

    @overrides
    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        self.toggle()

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.btnMenu.setGeometry(self.frame.width() - 25, 10, 20, 20)


class SelectedIdeasListModel(QAbstractListModel):
    SelectionRole = Qt.ItemDataRole.UserRole + 1

    def __init__(self, premise: PremiseBuilder, parent=None):
        super().__init__(parent)
        self._premise = premise

    @overrides
    def rowCount(self, parent: QModelIndex = ...) -> int:
        # return len([x for x in self._premise.ideas if x.selected])
        return len(self._premise.ideas)

    @overrides
    def data(self, index: QModelIndex, role: int) -> Any:
        if role == self.SelectionRole:
            return str(self._premise.ideas[index.row()].selected)
        elif role == Qt.ItemDataRole.DisplayRole:
            idea = self._premise.ideas[index.row()]
            return idea.text
        elif role == Qt.ItemDataRole.DecorationRole:
            return IconRegistry.from_name('mdi.seed', 'grey')
        elif role == Qt.ItemDataRole.FontRole:
            font = QApplication.font()
            font.setPointSize(15)
            return font


class ConceptWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)


class PremiseBuilderWidget(QWidget, Ui_PremiseBuilderWidget):
    changed = pyqtSignal()

    IDEA_EDIT_DESC: str = "An idea about character, plot, event, situation, setting, theme, genre, etc."
    IDEA_EDIT_PLACEHOLDER: str = "An idea..."

    def __init__(self, doc: Document, premise: PremiseBuilder, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._doc = doc
        self._premise = premise

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
        self.btnNextToConcept.setIcon(IconRegistry.from_name('fa5s.arrow-alt-circle-right', RELAXED_WHITE_COLOR))
        self.btnNextToConcept.installEventFilter(ButtonPressResizeEventFilter(self.btnNextToConcept))
        self.btnNextToPremise.setIcon(IconRegistry.from_name('fa5s.arrow-alt-circle-right', RELAXED_WHITE_COLOR))
        self.btnNextToPremise.installEventFilter(ButtonPressResizeEventFilter(self.btnNextToPremise))

        self.ideasModel = SelectedIdeasListModel(self._premise)
        self._proxy = proxy(self.ideasModel)
        self._proxy.setFilterRole(SelectedIdeasListModel.SelectionRole)
        self.listSelectedIdeas.setFont(QApplication.font())
        self.listSelectedIdeas.setModel(self._proxy)
        self.listSelectedIdeas.setSpacing(20)
        self._proxy.setFilterFixedString('True')

        link_buttons_to_pages(self.stackedWidget, [(self.btnSeed, self.pageSeed), (self.btnConcept, self.pageConcept),
                                                   (self.btnPremise, self.pagePremise)])
        self.btnSeed.setChecked(True)

        flow(self.wdgIdeasEditor)
        margins(self.wdgIdeasEditor, left=20, right=20, top=20)

        for idea in self._premise.ideas:
            self.__initIdeaWidget(idea)

    def _addNewIdea(self):
        text = TextAreaInputDialog.edit('Add a new idea', self.IDEA_EDIT_PLACEHOLDER, self.IDEA_EDIT_DESC)
        if text:
            idea = PremiseIdea(text)
            idea.params = BoxParameters()
            idea.params.lm = self.__randomMargin()
            idea.params.tm = self.__randomMargin()
            idea.params.rm = self.__randomMargin()
            idea.params.bm = self.__randomMargin()
            idea.params.width = random.randint(170, 210)

            self._premise.ideas.append(idea)
            wdg = self.__initIdeaWidget(idea)
            qtanim.fade_in(wdg)
            self.changed.emit()
            self._proxy.invalidate()

    def _editIdea(self, wdg: IdeaWidget):
        text = TextAreaInputDialog.edit('Edit idea', self.IDEA_EDIT_PLACEHOLDER, self.IDEA_EDIT_DESC, wdg.text())
        if text:
            wdg.setText(text)
            self.changed.emit()
            self._proxy.invalidate()

    def _removeIdea(self, wdg: IdeaWidget):
        idea = wdg.idea()
        self._premise.ideas.remove(idea)
        fade_out_and_gc(self.wdgIdeasEditor, wdg)
        self.changed.emit()
        self._proxy.invalidate()

    def _ideaToggled(self):
        self._proxy.invalidate()
        self.changed.emit()

    def __initIdeaWidget(self, idea: PremiseIdea) -> IdeaWidget:
        wdg = IdeaWidget(idea)
        wdg.edit.connect(partial(self._editIdea, wdg))
        wdg.remove.connect(partial(self._removeIdea, wdg))
        wdg.toggled.connect(self._ideaToggled)
        self.wdgIdeasEditor.layout().addWidget(wdg)

        return wdg

    def __randomMargin(self) -> int:
        return random.randint(3, 15)
