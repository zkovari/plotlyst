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
from abc import abstractmethod
from functools import partial
from typing import List

from PyQt6.QtCore import pyqtSignal, Qt, QSize, QObject, QEvent
from PyQt6.QtGui import QIcon, QColor, QPainter, QPaintEvent, QBrush, QResizeEvent
from PyQt6.QtWidgets import QWidget, QSizePolicy, \
    QLineEdit, QToolButton
from overrides import overrides
from qthandy import vbox, hbox, sp, vspacer, clear_layout, spacer, ask_confirmation, incr_font, bold, \
    margins
from qthandy.filter import VisibilityToggleEventFilter

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR, NEUTRAL_EMOTION_COLOR, \
    EMOTION_COLORS
from src.main.python.plotlyst.core.domain import BackstoryEvent
from src.main.python.plotlyst.view.common import tool_btn, frame
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.input import RemovalButton, AutoAdjustableTextEdit


class BackstoryCard(QWidget):
    edited = pyqtSignal()
    deleteRequested = pyqtSignal(object)
    relationChanged = pyqtSignal()

    def __init__(self, backstory: BackstoryEvent, parent=None):
        super().__init__(parent)
        self.backstory = backstory

        vbox(self)
        margins(self, top=18)

        self.cardFrame = frame()
        vbox(self.cardFrame)

        self.btnType = tool_btn(QIcon(), parent=self)
        self.btnType.setIconSize(QSize(24, 24))

        # self.menu = BackstoryEditorMenu(self.btnType)
        # self.menu.emotionChanged.connect(self._emotionChanged)
        # self.menu.iconSelected.connect(self._iconChanged)

        self.btnRemove = RemovalButton()
        self.btnRemove.setVisible(False)
        self.btnRemove.clicked.connect(self._remove)

        self.lineKeyPhrase = QLineEdit()
        self.lineKeyPhrase.setPlaceholderText('Keyphrase')
        self.lineKeyPhrase.setProperty('transparent', True)
        self.lineKeyPhrase.textEdited.connect(self._keyphraseEdited)
        incr_font(self.lineKeyPhrase)
        bold(self.lineKeyPhrase)

        self.textSummary = AutoAdjustableTextEdit(height=40)
        self.textSummary.setPlaceholderText("Summarize this event")
        self.textSummary.setProperty('transparent', True)
        self.textSummary.setProperty('rounded', True)
        self.textSummary.textChanged.connect(self._synopsisChanged)

        wdgTop = QWidget()
        hbox(wdgTop, 0, 0)
        wdgTop.layout().addWidget(self.lineKeyPhrase)
        wdgTop.layout().addWidget(self.btnRemove, alignment=Qt.AlignmentFlag.AlignTop)
        self.cardFrame.layout().addWidget(wdgTop)
        self.cardFrame.setObjectName('cardFrame')
        self.cardFrame.layout().addWidget(self.textSummary)
        self.layout().addWidget(self.cardFrame)

        self.cardFrame.installEventFilter(VisibilityToggleEventFilter(self.btnRemove, self.cardFrame))

        self.btnType.raise_()

        self.setMinimumWidth(60)
        sp(self).v_max()
        self.refresh()

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.btnType.setGeometry(self.width() // 2 - 18, 2, 36, 36)

    def refresh(self):
        self._refreshStyle()
        self.lineKeyPhrase.setText(self.backstory.keyphrase)
        self.textSummary.setPlainText(self.backstory.synopsis)
        # self.menu.setEmotion(self.backstory.emotion)

    def _refreshStyle(self):
        bg_color = EMOTION_COLORS.get(self.backstory.emotion, NEUTRAL_EMOTION_COLOR)
        self.cardFrame.setStyleSheet(f'''
                            #cardFrame {{
                                border-top: 8px solid {bg_color};
                                border-bottom-left-radius: 12px;
                                border-bottom-right-radius: 12px;
                                background-color: #ffe8d6;
                                }}
                            ''')
        self.btnType.setStyleSheet(
            f'''
                    QToolButton {{
                            background-color: {RELAXED_WHITE_COLOR}; border: 3px solid {bg_color};
                            border-radius: 18px;
                            padding: 4px;
                        }}
                    QToolButton:hover {{
                        padding: 2px;
                    }}
                    ''')

        self.btnType.setIcon(IconRegistry.from_name(self.backstory.type_icon, bg_color))

    def _synopsisChanged(self):
        self.backstory.synopsis = self.textSummary.toPlainText()
        self.edited.emit()

    def _keyphraseEdited(self):
        self.backstory.keyphrase = self.lineKeyPhrase.text()
        self.edited.emit()

    def _emotionChanged(self, value: int):
        self.backstory.emotion = value
        self._refreshStyle()
        self.edited.emit()

    def _iconChanged(self, icon: str):
        self.backstory.type_icon = icon
        self.btnType.setIcon(IconRegistry.from_name(self.backstory.type_icon, EMOTION_COLORS[self.backstory.emotion]))
        self.edited.emit()

    def _remove(self):
        if self.backstory.synopsis and not ask_confirmation(f'Remove event "{self.backstory.keyphrase}"?'):
            return
        self.deleteRequested.emit(self)


class BackstoryCardPlaceholder(QWidget):
    def __init__(self, card: BackstoryCard, alignment: int = Qt.AlignmentFlag.AlignRight, parent=None):
        super().__init__(parent)
        self.alignment = alignment
        self.card = card

        self._layout = hbox(self, 0, 3)
        self.spacer = spacer()
        self.spacer.setFixedWidth(self.width() // 2 + 3)
        if self.alignment == Qt.AlignmentFlag.AlignRight:
            self.layout().addWidget(self.spacer)
            self._layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignLeft)
        elif self.alignment == Qt.AlignmentFlag.AlignLeft:
            self._layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignRight)
            self.layout().addWidget(self.spacer)
        else:
            self.layout().addWidget(self.card)

    def toggleAlignment(self):
        if self.alignment == Qt.AlignmentFlag.AlignLeft:
            self.alignment = Qt.AlignmentFlag.AlignRight
            self._layout.takeAt(0)
            self._layout.addWidget(self.spacer)
            self._layout.setAlignment(self.card, Qt.AlignmentFlag.AlignRight)
        else:
            self.alignment = Qt.AlignmentFlag.AlignLeft
            self._layout.takeAt(1)
            self._layout.insertWidget(0, self.spacer)
            self._layout.setAlignment(self.card, Qt.AlignmentFlag.AlignLeft)


class _ControlButtons(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        vbox(self)

        self.btnPlaceholderCircle = QToolButton(self)
        self.btnPlus = tool_btn(IconRegistry.plus_icon('white'), tooltip='Add new event')

        self.layout().addWidget(self.btnPlaceholderCircle)
        self.layout().addWidget(self.btnPlus)

        self.btnPlus.setHidden(True)

        bg_color = '#1d3557'
        for btn in [self.btnPlaceholderCircle, self.btnPlus]:
            btn.setStyleSheet(f'''
                QToolButton {{ background-color: {bg_color}; border: 1px;
                        border-radius: 13px; padding: 2px;}}
                QToolButton:pressed {{background-color: grey;}}
            ''')

        self.installEventFilter(self)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            self.btnPlaceholderCircle.setHidden(True)
            self.btnPlus.setVisible(True)
        elif event.type() == QEvent.Type.Leave:
            self.btnPlaceholderCircle.setVisible(True)
            self.btnPlus.setHidden(True)

        return super().eventFilter(watched, event)


class TimelineWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent=None):
        self._spacers: List[QWidget] = []
        super().__init__(parent)
        self._layout = vbox(self, spacing=0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        for sp in self._spacers:
            sp.setFixedWidth(self.width() // 2 + 3)

    @abstractmethod
    def events(self) -> List[BackstoryEvent]:
        pass

    def refresh(self):
        self._spacers.clear()
        clear_layout(self.layout())

        prev_alignment = None
        for i, backstory in enumerate(self.events()):
            if prev_alignment is None:
                alignment = Qt.AlignmentFlag.AlignRight
            elif backstory.follow_up and prev_alignment:
                alignment = prev_alignment
            elif prev_alignment == Qt.AlignmentFlag.AlignLeft:
                alignment = Qt.AlignmentFlag.AlignRight
            else:
                alignment = Qt.AlignmentFlag.AlignLeft
            prev_alignment = alignment
            event = BackstoryCardPlaceholder(BackstoryCard(backstory), alignment, parent=self)
            event.card.deleteRequested.connect(self._remove)

            self._spacers.append(event.spacer)
            event.spacer.setFixedWidth(self.width() // 2 + 3)

            self._addControlButtons(i)
            self._layout.addWidget(event)

            event.card.edited.connect(self.changed.emit)
            event.card.relationChanged.connect(self.changed.emit)
            event.card.relationChanged.connect(self.refresh)

        self._addControlButtons(-1)
        spacer_ = vspacer()
        spacer_.setMinimumHeight(200)
        self.layout().addWidget(spacer_)

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor('#1d3557')))
        painter.drawRect(int(self.width() / 2) - 3, 64, 6, self.height() - 64)

        painter.end()

    def add(self, pos: int = -1):
        backstory = BackstoryEvent('', '', type_color=NEUTRAL_EMOTION_COLOR)
        if pos >= 0:
            self.events().insert(pos, backstory)
        else:
            self.events().append(backstory)
        self.refresh()
        self.changed.emit()

    def _remove(self, card: BackstoryCard):
        if card.backstory in self.character.backstory:
            self.character.backstory.remove(card.backstory)

        self.refresh()
        self.changed.emit()

    def _addControlButtons(self, pos: int):
        control = _ControlButtons(self)
        control.btnPlus.clicked.connect(partial(self.add, pos))
        self._layout.addWidget(control, alignment=Qt.AlignmentFlag.AlignHCenter)
