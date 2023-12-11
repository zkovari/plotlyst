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
import random
from enum import Enum, auto
from functools import partial
from typing import Optional, Dict

import qtanim
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QButtonGroup, QStackedWidget, QTextEdit
from overrides import overrides
from qthandy import vbox, hbox, spacer, sp, flow, vline, clear_layout, bold, margins, incr_font, italic
from qthandy.filter import OpacityEventFilter

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR
from src.main.python.plotlyst.core.domain import Novel, Scene, ReaderQuestion, SceneReaderQuestion
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import push_btn, link_buttons_to_pages, shadow, scroll_area, \
    insert_before_the_end, wrap, fade_out_and_gc
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.display import LazyWidget


class QuestionState(Enum):
    Raised_before = auto()
    Raised_now = auto()
    Resolved_before = auto()
    Resolved_now = auto()
    Detached = auto()


class ReaderQuestionWidget(QWidget):
    resolved = pyqtSignal()

    def __init__(self, question: ReaderQuestion, state: QuestionState, ref: Optional[SceneReaderQuestion] = None,
                 parent=None):
        super().__init__(parent)
        self.question = question
        self.scene_ref = ref
        self.state = state

        vbox(self)
        margins(self, top=self.question.top_margin, left=self.question.left_margin, right=self.question.right_margin,
                bottom=self.question.bottom_margin)
        self._label = push_btn(IconRegistry.from_name('ei.question-sign'), 'Question', transparent_=True)
        bold(self._label)
        self._label.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.textedit = QTextEdit(self)
        self.textedit.setProperty('white-bg', True)
        self.textedit.setProperty('rounded', True)
        self.textedit.setTabChangesFocus(True)
        if app_env.is_mac():
            incr_font(self.textedit)
        self.textedit.setMinimumSize(170, 100)
        self.textedit.setMaximumSize(question.max_width, question.max_height)
        self.textedit.verticalScrollBar().setVisible(False)
        shadow(self.textedit)
        self.textedit.textChanged.connect(self._questionChanged)

        self.layout().addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self.textedit)

        if self.state == QuestionState.Raised_now or self.state == QuestionState.Resolved_now:
            badge = push_btn(IconRegistry.from_name('ei.star-alt', color=PLOTLYST_SECONDARY_COLOR), 'New!',
                             icon_resize=False, pointy_=False)
            badge.setStyleSheet(f'border: 0px; color: {PLOTLYST_SECONDARY_COLOR}')
            italic(badge)
            self.layout().addWidget(badge, alignment=Qt.AlignmentFlag.AlignLeft)
        elif self.state == QuestionState.Raised_before:
            resolve = push_btn(
                IconRegistry.from_name('mdi.sticker-check-outline', color=PLOTLYST_SECONDARY_COLOR), 'Resolve')
            resolve.setStyleSheet(f'border:opx; color: {PLOTLYST_SECONDARY_COLOR};')
            resolve.installEventFilter(OpacityEventFilter(resolve, leaveOpacity=0.7))
            resolve.clicked.connect(self.resolved)
            self.layout().addWidget(resolve, alignment=Qt.AlignmentFlag.AlignCenter)

        sp(self).v_max()

    def _questionChanged(self):
        pass


class ReaderCuriosityEditor(LazyWidget):
    LABEL_RAISED_QUESTIONS = 'Raised questions'
    LABEL_RESOLVED_QUESTIONS = 'Resolved questions'
    LABEL_FUTURE_QUESTIONS = 'Future questions'

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._scene: Optional[Scene] = None

        vbox(self, 10, 8)
        self.wdgHeader = QWidget()
        hbox(self.wdgHeader)

        self.btnUnresolved = push_btn(
            IconRegistry.from_name('ei.question-sign', 'lightgrey', color_on=PLOTLYST_SECONDARY_COLOR),
            text=self.LABEL_RAISED_QUESTIONS,
            properties=['secondary-selector', 'transparent-magnolia-rounded-bg-on-hover',
                        'transparent-rounded-bg-on-hover'],
            checkable=True)
        self.btnResolved = push_btn(
            IconRegistry.from_name('mdi.sticker-check', 'lightgrey', color_on=PLOTLYST_SECONDARY_COLOR),
            text=self.LABEL_RESOLVED_QUESTIONS,
            properties=['secondary-selector', 'transparent-magnolia-rounded-bg-on-hover',
                        'transparent-rounded-bg-on-hover'],
            checkable=True)
        self.btnOther = push_btn(
            IconRegistry.from_name('ph.link-simple-break-bold', 'lightgrey', color_on=PLOTLYST_SECONDARY_COLOR),
            text=self.LABEL_FUTURE_QUESTIONS,
            properties=['secondary-selector', 'transparent-magnolia-rounded-bg-on-hover',
                        'transparent-rounded-bg-on-hover'],
            checkable=True)

        self.btnGroup = QButtonGroup()
        self.btnGroup.setExclusive(True)
        self.btnGroup.addButton(self.btnUnresolved)
        self.btnGroup.addButton(self.btnResolved)
        self.btnGroup.addButton(self.btnOther)

        self.btnUnresolved.setChecked(True)

        self.wdgHeader.layout().addWidget(self.btnUnresolved)
        self.wdgHeader.layout().addWidget(self.btnResolved)
        self.wdgHeader.layout().addWidget(vline())
        self.wdgHeader.layout().addWidget(self.btnOther)
        self.wdgHeader.layout().addWidget(spacer())

        self.btnAddNew = push_btn(IconRegistry.plus_icon('grey'), 'Raise new question', transparent_=True)
        self.btnAddNew.installEventFilter(OpacityEventFilter(self.btnAddNew, 0.8, 0.5))
        self.btnAddNew.clicked.connect(self._addNew)

        self.wdgEditor = QStackedWidget()
        sp(self.wdgEditor).v_exp()

        self.pageQuestions = scroll_area(h_on=False, frameless=True)
        self.pageQuestionsEditor = QWidget()
        self.pageQuestionsEditor.setProperty('relaxed-white-bg', True)
        self.pageQuestions.setWidget(self.pageQuestionsEditor)
        flow(self.pageQuestionsEditor, 5, 7)
        self.wdgEditor.addWidget(self.pageQuestions)

        self.pageResolvedQuestions = scroll_area(h_on=False, frameless=True)
        self.pageResolvedQuestionsEditor = QWidget()
        self.pageResolvedQuestionsEditor.setProperty('relaxed-white-bg', True)
        self.pageResolvedQuestions.setWidget(self.pageResolvedQuestionsEditor)
        flow(self.pageResolvedQuestionsEditor, 5, 8)
        self.wdgEditor.addWidget(self.pageResolvedQuestions)

        self.pageDetachedQuestions = scroll_area(h_on=False, frameless=True)
        self.pageDetachedQuestionsEditor = QWidget()
        self.pageDetachedQuestionsEditor.setProperty('relaxed-white-bg', True)
        self.pageDetachedQuestions.setWidget(self.pageDetachedQuestionsEditor)
        flow(self.pageDetachedQuestionsEditor, 5, 8)
        self.wdgEditor.addWidget(self.pageDetachedQuestions)

        self.wdgEditor.setCurrentWidget(self.pageQuestions)

        self.layout().addWidget(self.wdgHeader)
        self.layout().addWidget(self.wdgEditor)

        link_buttons_to_pages(self.wdgEditor, [
            (self.btnUnresolved, self.pageQuestions), (self.btnResolved, self.pageResolvedQuestions),
            (self.btnOther, self.pageDetachedQuestions)
        ])

        self.repo = RepositoryPersistenceManager.instance()

    def setScene(self, scene: Scene):
        self._scene = scene
        self._initialized = False
        if self.isVisible():
            self.refresh()

    @overrides
    def refresh(self):
        if not self._scene:
            return

        clear_layout(self.pageQuestionsEditor)
        clear_layout(self.pageResolvedQuestionsEditor)
        clear_layout(self.pageDetachedQuestionsEditor)

        found_questions: Dict[ReaderQuestion, Optional[bool]] = {}
        for scene in self._novel.scenes:
            for question_ref in scene.questions:
                question = self._novel.questions[question_ref.sid()]
                found_questions[question] = question_ref.resolved

            if scene is self._scene:
                break

        for question_ref in self._scene.questions:
            question = self._novel.questions[question_ref.sid()]
            found_questions[question] = None
            self._addQuestion(question,
                              QuestionState.Resolved_now if question_ref.resolved else QuestionState.Raised_now)

        for k, v in found_questions.items():
            if v is None:
                continue
            self._addQuestion(k, QuestionState.Resolved_before if v else QuestionState.Raised_before)

        for question in self._novel.questions.values():
            if question not in found_questions.keys():
                self._addQuestion(question, QuestionState.Detached)

        self.pageQuestionsEditor.layout().addWidget(wrap(self.btnAddNew, margin_top=80))

        self._updateLabels()

        super().refresh()

    def _updateLabels(self):
        self.btnUnresolved.setText(f'{self.LABEL_RAISED_QUESTIONS} ({self.pageQuestionsEditor.layout().count() - 1})')
        self.btnResolved.setText(
            f'{self.LABEL_RESOLVED_QUESTIONS} ({self.pageResolvedQuestionsEditor.layout().count()})')
        self.btnOther.setText(f'{self.LABEL_FUTURE_QUESTIONS} ({self.pageDetachedQuestionsEditor.layout().count()})')

        self.btnOther.setVisible(self.pageDetachedQuestionsEditor.layout().count() > 0)
        if not self.btnOther.isVisible() and self.btnOther.isChecked():
            self.btnUnresolved.setChecked(True)

    def _addQuestion(self, question: ReaderQuestion, state: QuestionState, ref: Optional[SceneReaderQuestion] = None):
        wdg = self.__initQuestionWidget(question, state, ref)

        if state == QuestionState.Raised_before or state == QuestionState.Raised_now:
            self.pageQuestionsEditor.layout().addWidget(wdg)
        elif state == QuestionState.Resolved_before or state == QuestionState.Resolved_now:
            self.pageResolvedQuestionsEditor.layout().addWidget(wdg)
        else:
            self.pageDetachedQuestionsEditor.layout().addWidget(wdg)

    def _addNew(self):
        question = ReaderQuestion()
        question.top_margin = random.randint(5, 15)
        question.left_margin = random.randint(5, 15)
        question.right_margin = random.randint(5, 15)
        question.bottom_margin = random.randint(5, 15)
        question.max_width = random.randint(180, 190)
        question.max_height = random.randint(110, 120)

        self._novel.questions[question.sid()] = question
        ref = SceneReaderQuestion(question.id)
        self._scene.questions.append(ref)
        self.repo.update_novel(self._novel)

        wdg = self.__initQuestionWidget(question, QuestionState.Raised_now, ref)
        insert_before_the_end(self.pageQuestionsEditor, wdg)
        qtanim.fade_in(wdg, teardown=lambda: wdg.setGraphicsEffect(None))
        wdg.textedit.setFocus()

        self._updateLabels()

    def _resolve(self, wdg: ReaderQuestionWidget):
        def finish():
            self._addQuestion(question, QuestionState.Resolved_now, ref)
            qtanim.glow(self.btnResolved, color=QColor(PLOTLYST_SECONDARY_COLOR), loop=3)
            self._updateLabels()

        question = wdg.question
        ref = SceneReaderQuestion(question.id, resolved=True)
        fade_out_and_gc(self.pageQuestionsEditor, wdg, teardown=finish)
        self._scene.questions.append(ref)

    def __initQuestionWidget(self, question: ReaderQuestion,
                             state: QuestionState, ref: Optional[SceneReaderQuestion] = None) -> ReaderQuestionWidget:
        wdg = ReaderQuestionWidget(question, state, ref)
        wdg.resolved.connect(partial(self._resolve, wdg))

        return wdg
