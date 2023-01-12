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
import pickle
from abc import abstractmethod
from enum import Enum
from typing import Optional, List

import qtanim
from PyQt6 import QtGui
from PyQt6.QtCore import pyqtSignal, QSize, Qt, QEvent, QPoint, QMimeData, QByteArray
from PyQt6.QtGui import QMouseEvent, QDrag, QDragEnterEvent, QDragMoveEvent, QDropEvent, QColor, QAction
from PyQt6.QtWidgets import QFrame, QApplication, QToolButton
from overrides import overrides
from qtframes import Frame
from qthandy import FlowLayout, clear_layout, retain_when_hidden, transparent, margins

from src.main.python.plotlyst.common import act_color
from src.main.python.plotlyst.core.domain import NovelDescriptor, Character, Scene, Document, Novel
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.generated.character_card_ui import Ui_CharacterCard
from src.main.python.plotlyst.view.generated.journal_card_ui import Ui_JournalCard
from src.main.python.plotlyst.view.generated.novel_card_ui import Ui_NovelCard
from src.main.python.plotlyst.view.generated.scene_card_ui import Ui_SceneCard
from src.main.python.plotlyst.view.icons import IconRegistry, set_avatar, avatars
from src.main.python.plotlyst.view.widget.labels import CharacterAvatarLabel


class CardMimeData(QMimeData):
    def __init__(self, card: 'Card'):
        super().__init__()
        self.card = card


class Card(QFrame):
    selected = pyqtSignal(object)
    doubleClicked = pyqtSignal(object)
    dropped = pyqtSignal(object, object)

    def __init__(self, parent):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.select)
        self.dragStartPosition: Optional[QPoint] = None
        self._dragEnabled: bool = True
        self._popup_actions: List[QAction] = []

    def isDragEnabled(self) -> bool:
        return self._dragEnabled

    def setDragEnabled(self, enabled: bool):
        self._dragEnabled = enabled

    @overrides
    def enterEvent(self, event: QEvent) -> None:
        qtanim.glow(self, color=QColor('#0096c7'))

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._dragEnabled and event.button() == Qt.MouseButton.LeftButton:
            self.dragStartPosition = event.pos()
        else:
            self.dragStartPosition = None
        super(Card, self).mousePressEvent(event)

    @overrides
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._dragEnabled:
            return
        if not event.buttons() & Qt.MouseButton.LeftButton:
            return
        if not self.dragStartPosition:
            return
        if (event.pos() - self.dragStartPosition).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mimeData = CardMimeData(self)
        mimeData.setData(self.mimeType(), QByteArray(pickle.dumps(self.objectName())))
        drag.setPixmap(self.grab())
        drag.setMimeData(mimeData)
        drag.exec(Qt.MoveAction)

    @overrides
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self.select()

    @overrides
    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        self.select()
        self.doubleClicked.emit(self)

    @overrides
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        event.acceptProposedAction()

    @overrides
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasFormat(self.mimeType()):
            event.acceptProposedAction()
        else:
            event.ignore()

    @overrides
    def dropEvent(self, event: QDropEvent) -> None:
        if isinstance(event.mimeData(), CardMimeData):
            if event.mimeData().card is self:
                event.ignore()
                return

            self.dropped.emit(event.mimeData().card, self)
            event.acceptProposedAction()
        else:
            event.ignore()

    def select(self):
        self._setStyleSheet(selected=True)
        self.selected.emit(self)

    def clearSelection(self):
        self._setStyleSheet()

    @abstractmethod
    def mimeType(self) -> str:
        pass

    def _setStyleSheet(self, selected: bool = False):
        border_color = self._borderColor(selected)
        border_size = self._borderSize(selected)
        background_color = self._bgColor(selected)
        self.setStyleSheet(f'''
           QFrame[mainFrame=true] {{
               border: {border_size}px solid {border_color};
               border-radius: 15px;
               background-color: {background_color};
           }}''')

    def _bgColor(self, selected: bool = False) -> str:
        return '#dec3c3' if selected else '#f9f4f4'

    def _borderSize(self, selected: bool = False) -> int:
        return 4 if selected else 2

    def _borderColor(self, selected: bool = False) -> str:
        return '#2a4d69' if selected else '#adcbe3'


class NovelCard(Ui_NovelCard, Card):

    def __init__(self, novel: NovelDescriptor, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self._setStyleSheet()
        self.refresh()

    def refresh(self):
        self.textName.setText(self.novel.title)
        self.textName.setAlignment(Qt.AlignmentFlag.AlignCenter)

    @overrides
    def mimeType(self) -> str:
        return 'application/novel-card'


class CharacterCard(Ui_CharacterCard, Card):

    def __init__(self, character: Character, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.character = character
        self.textName.setContentsMargins(0, 0, 0, 0)
        self.textName.document().setDocumentMargin(0)
        self.textName.setText(self.character.name)
        self.textName.setAlignment(Qt.AlignmentFlag.AlignCenter)
        set_avatar(self.lblPic, self.character, size=118)

        transparent(self.btnEnneagram)
        enneagram = self.character.enneagram()
        if enneagram:
            self.btnEnneagram.setIcon(IconRegistry.from_name(enneagram.icon, enneagram.icon_color))
        mbti = self.character.mbti()
        if mbti:
            self.btnMbti.setStyleSheet(f'color: {mbti.icon_color};border:0px;')
            self.btnMbti.setText(mbti.text)
            self.btnMbti.setIcon(IconRegistry.from_name(mbti.icon, mbti.icon_color))

        retain_when_hidden(self.iconRole)
        self.iconRole.setHidden(self.character.prefs.avatar.use_role)
        if self.character.role and not self.character.prefs.avatar.use_role:
            self.iconRole.setRole(self.character.role)
            self.iconRole.setToolTip(self.character.role.text)
        self._setStyleSheet()

    @overrides
    def mimeType(self) -> str:
        return 'application/character-card'


class JournalCard(Card, Ui_JournalCard):

    def __init__(self, journal: Document, parent=None):
        super(JournalCard, self).__init__(parent)
        self.setupUi(self)
        self.journal = journal

        self.refresh()
        self.textTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._setStyleSheet()
        self.setDragEnabled(False)

    @overrides
    def mimeType(self) -> str:
        return 'application/journal-card'

    def refresh(self):
        self.textTitle.setText(self.journal.title)


class SceneCard(Ui_SceneCard, Card):
    cursorEntered = pyqtSignal()

    def __init__(self, scene: Scene, novel: Novel, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.scene = scene
        self.novel = novel

        self.wdgCharacters.layout().setSpacing(1)

        self.textTitle.setFontPointSize(QApplication.font().pointSize() + 1)
        self.textTitle.setText(self.scene.title_or_index(self.novel))
        self.textTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.textSynopsis.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.textSynopsis.setText(scene.synopsis)

        self.btnPov.clicked.connect(self.select)
        self.btnStage.clicked.connect(self.select)

        if scene.pov:
            self.btnPov.setIcon(avatars.avatar(scene.pov))
        for char in scene.characters:
            self.wdgCharacters.addLabel(CharacterAvatarLabel(char, 20))

        self._beatFrame = Frame(self)
        self.btnBeat = QToolButton()
        transparent(self.btnBeat)
        self.btnBeat.setIconSize(QSize(24, 24))
        self._beatFrame.setWidget(self.btnBeat)
        self._beatFrame.setGeometry(self.width() - 30, 0, self._beatFrame.width(), self._beatFrame.height())

        beat = self.scene.beat(self.novel)
        if beat and beat.icon:
            self.btnBeat.setIcon(IconRegistry.from_name(beat.icon, beat.icon_color))
            self._beatFrame.setFrameColor(QColor(act_color(beat.act)))
            self._beatFrame.setBackgroundColor(Qt.GlobalColor.white)
            margins(self._beatFrame, 0, 0, 0, 0)
        else:
            self._beatFrame.setHidden(True)

        # if any([x.major for x in scene.comments]):
        #     self.btnComments.setIcon(IconRegistry.from_name('fa5s.comment', color='#fb8b24'))
        # else:
        #     self.btnComments.setHidden(True)

        icon = IconRegistry.scene_type_icon(self.scene)
        if icon:
            self.lblType.setPixmap(icon.pixmap(QSize(24, 24)))
        else:
            self.lblType.clear()

        self.btnStage.setScene(self.scene)

        self._setStyleSheet()

        self.repo = RepositoryPersistenceManager.instance()

    @overrides
    def mimeType(self) -> str:
        return 'application/scene-card'

    @overrides
    def enterEvent(self, event: QEvent) -> None:
        super(SceneCard, self).enterEvent(event)
        self.wdgCharacters.setEnabled(True)
        if not self.btnStage.stageOk():
            self.btnStage.setVisible(True)
        self.cursorEntered.emit()

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        self.wdgCharacters.setEnabled(False)
        if not self.btnStage.stageOk() and not self.btnStage.menu().isVisible():
            self.btnStage.setHidden(True)

    @overrides
    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self.btnStage.setVisible(self.btnStage.stageOk())

    @overrides
    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        w = event.size().width()
        self._adjustToWidth(w)

    @overrides
    def setFixedSize(self, w: int, h: int) -> None:
        super(SceneCard, self).setFixedSize(w, h)
        self._adjustToWidth(w)

    def _adjustToWidth(self, w):
        self.textSynopsis.setVisible(w > 170)
        self.lineAfterTitle.setVisible(w > 170)
        self.lineAfterTitle.setFixedWidth(w - 30)

        self._beatFrame.setGeometry(w - 40, 0, 40, 50)


class CardSizeRatio(Enum):
    RATIO_2_3 = 0
    RATIO_3_4 = 1


class CardsView(QFrame):
    swapped = pyqtSignal(object, object)
    selectionCleared = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = FlowLayout(9, 15)
        self._cards: List[Card] = []
        self.setLayout(self._layout)
        self.setAcceptDrops(True)
        self._selected: Optional[Card] = None
        self._cardsWidth: int = 135
        self._cardsRatio = CardSizeRatio.RATIO_3_4

    @overrides
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        event.acceptProposedAction()
        super(CardsView, self).dragEnterEvent(event)

    @overrides
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        event.acceptProposedAction()

    @overrides
    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        if self._selected:
            self._selected.clearSelection()
            self._selected = None
            self.selectionCleared.emit()

    def clear(self):
        self._selected = None
        self._cards.clear()
        clear_layout(self._layout)

    def addCard(self, card: Card):
        card.setAcceptDrops(True)
        card.selected.connect(self._cardSelected)
        card.dropped.connect(self.swapped.emit)

        self._layout.addWidget(card)
        self._cards.append(card)
        self._resizeCard(card)

    def cardAt(self, pos: int) -> Optional[Card]:
        item = self._layout.itemAt(pos)
        if item and item.widget():
            return item.widget()

    def setCardsWidth(self, value: int):
        self._cardsWidth = value
        self._resizeAllCards()

    def setCardsSizeRatio(self, ratio: CardSizeRatio):
        self._cardsRatio = ratio
        self._resizeAllCards()

    def _resizeAllCards(self):
        for card in self._cards:
            self._resizeCard(card)

    def _resizeCard(self, card: Card):
        if self._cardsRatio == CardSizeRatio.RATIO_3_4:
            height = self._cardsWidth * 1.3
        else:
            height = self._cardsWidth / 2 * 3
        card.setFixedSize(self._cardsWidth, int(height))

    def _cardSelected(self, card: Card):
        self._selected = card
