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
from enum import Enum
from functools import partial
from typing import List, Optional, Any

import qtanim
from PyQt6.QtCore import Qt, QSize, QEvent, pyqtSignal, QObject
from PyQt6.QtGui import QEnterEvent, QIcon, QMouseEvent, QColor
from PyQt6.QtWidgets import QWidget, QTextEdit, QPushButton, QLabel, QFrame, QStackedWidget
from overrides import overrides
from qthandy import vbox, vspacer, transparent, sp, line, incr_font, hbox, pointy, vline, retain_when_hidden, margins, \
    spacer, underline, bold, flow
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import raise_unrecognized_arg
from src.main.python.plotlyst.core.domain import Scene, Novel, ScenePurpose, advance_story_scene_purpose, \
    ScenePurposeType, reaction_story_scene_purpose, character_story_scene_purpose, setup_story_scene_purpose, \
    emotion_story_scene_purpose, exposition_story_scene_purpose, scene_purposes, Character
from src.main.python.plotlyst.event.core import EventListener, Event, emit_event
from src.main.python.plotlyst.event.handler import event_dispatchers
from src.main.python.plotlyst.events import SceneChangedEvent
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import DelayedSignalSlotConnector, action, wrap, label, scrolled, \
    ButtonPressResizeEventFilter
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorButton
from src.main.python.plotlyst.view.widget.display import Icon
from src.main.python.plotlyst.view.widget.input import RemovalButton


class SceneMiniEditor(QWidget, EventListener):

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._scenes: List[Scene] = []
        self._currentScene: Optional[Scene] = None

        self._lblScene = QLabel()
        incr_font(self._lblScene, 2)
        self._btnScenes = QPushButton()
        incr_font(self._btnScenes, 2)
        transparent(self._btnScenes)
        sp(self._btnScenes).h_exp()
        self._menuScenes = MenuWidget(self._btnScenes)

        self._textSynopsis = QTextEdit()
        self._textSynopsis.setProperty('white-bg', True)
        self._textSynopsis.setProperty('rounded', True)
        self._textSynopsis.setPlaceholderText('Write a short summary of this scene')
        self._textSynopsis.setMaximumHeight(200)

        self._layout = vbox(self)
        self._layout.addWidget(self._btnScenes, alignment=Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._lblScene, alignment=Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(line())
        self._layout.addWidget(QLabel('Synopsis:'), alignment=Qt.AlignmentFlag.AlignLeft)
        self._layout.addWidget(self._textSynopsis)
        self._layout.addWidget(vspacer())

        DelayedSignalSlotConnector(self._textSynopsis.textChanged, self._save, parent=self)

        self._repo = RepositoryPersistenceManager.instance()
        dispatcher = event_dispatchers.instance(self._novel)
        dispatcher.register(self, SceneChangedEvent)

    def setScene(self, scene: Scene):
        self.setScenes([scene])

    def setScenes(self, scenes: List[Scene]):
        self.reset()
        self._scenes.extend(scenes)

        if len(self._scenes) > 1:
            for scene in scenes:
                self._menuScenes.addAction(action(
                    scene.title_or_index(self._novel), slot=partial(self.selectScene, scene)
                ))

        self._lblScene.setVisible(len(self._scenes) == 1)
        self._btnScenes.setVisible(len(self._scenes) > 1)

        if self._scenes:
            self.selectScene(self._scenes[0])

    def selectScene(self, scene: Scene):
        self._save()
        self._currentScene = None
        if len(self._scenes) > 1:
            self._btnScenes.setText(scene.title_or_index(self._novel))
        else:
            self._lblScene.setText(scene.title_or_index(self._novel))
        self._textSynopsis.setText(scene.synopsis)
        self._currentScene = scene

    def reset(self):
        self._save()
        self._currentScene = None
        self._scenes.clear()
        self._btnScenes.setText('')
        self._menuScenes.clear()
        self._textSynopsis.clear()

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, SceneChangedEvent):
            if event.scene is self._currentScene:
                self.selectScene(self._currentScene)

    def _save(self):
        if self._currentScene and self._currentScene.synopsis != self._textSynopsis.toPlainText():
            self._currentScene.synopsis = self._textSynopsis.toPlainText()
            self._repo.update_scene(self._currentScene)
            emit_event(self._novel, SceneChangedEvent(self, self._currentScene))


def purpose_icon(purpose_type: ScenePurposeType) -> QIcon:
    if purpose_type == ScenePurposeType.Story:
        return IconRegistry.action_scene_icon()
    elif purpose_type == ScenePurposeType.Reaction:
        return IconRegistry.reaction_scene_icon()
    elif purpose_type == ScenePurposeType.Character:
        return IconRegistry.character_development_scene_icon()
    elif purpose_type == ScenePurposeType.Emotion:
        return IconRegistry.emotion_scene_icon()
    elif purpose_type == ScenePurposeType.Setup:
        return IconRegistry.setup_scene_icon()
    elif purpose_type == ScenePurposeType.Exposition:
        return IconRegistry.exposition_scene_icon()
    else:
        raise_unrecognized_arg(purpose_type)


class ScenePurposeTypeButton(QPushButton):
    selectionRequested = pyqtSignal()

    def __init__(self, type: ScenePurposeType, parent=None):
        super(ScenePurposeTypeButton, self).__init__(parent)
        self.type = type
        pointy(self)
        self._opacityFilter = OpacityEventFilter(self, 0.8, 1.0, ignoreCheckedButton=True)
        self.installEventFilter(self._opacityFilter)

        self._menu = MenuWidget(self)
        self._menu.addAction(action('Select new purpose', slot=self.selectionRequested.emit))

        self.refresh()

    def setPurposeType(self, type: ScenePurposeType):
        self.type = type
        self.refresh()

    def refresh(self):
        if self.type == ScenePurposeType.Other:
            self.setText('')
            self.setToolTip('Scene purpose not selected')
        else:
            purpose = scene_purposes.get(self.type)
            tip = purpose.display_name.replace('\n', ' ')
            self.setText(tip)
            self.setToolTip(f'Scene purpose: {tip}')

        if self.type == ScenePurposeType.Exposition:
            self.setIcon(IconRegistry.exposition_scene_icon())
        elif self.type == ScenePurposeType.Setup:
            self.setIcon(IconRegistry.setup_scene_icon())
        elif self.type == ScenePurposeType.Character:
            self.setIcon(IconRegistry.character_development_scene_icon())
        elif self.type == ScenePurposeType.Emotion:
            self.setIcon(IconRegistry.emotion_scene_icon())

        bold(self, self.type != ScenePurposeType.Other)

        if self.type == ScenePurposeType.Story:
            bgColor = '#f4978e'
            borderColor = '#fb5607'
            self.setIcon(IconRegistry.action_scene_icon())
        elif self.type == ScenePurposeType.Reaction:
            bgColor = '#89c2d9'
            borderColor = '#1a759f'
            self.setIcon(IconRegistry.reaction_scene_icon())
        elif self.type == ScenePurposeType.Other:
            bgColor = 'lightgrey'
            borderColor = 'grey'
        else:
            bgColor = 'darkGrey'
            borderColor = 'grey'

        self.setStyleSheet(f'''
            QPushButton {{
                background: {bgColor};
                border: 2px solid {borderColor};
                border-radius: 8px;
                padding: 2px;
            }}
            QPushButton::menu-indicator{{
                width:0px;
            }}
            ''')


class ScenePurposeWidget(QFrame):
    clicked = pyqtSignal()

    def __init__(self, purpose: ScenePurpose, parent=None):
        super().__init__(parent)
        self._purpose = purpose
        self.setMinimumWidth(150)
        self.setMaximumWidth(170)

        self._icon = Icon()
        self._icon.setIcon(purpose_icon(self._purpose.type))
        self._icon.setIconSize(QSize(64, 64))
        self._icon.setDisabled(True)
        self._icon.installEventFilter(self)
        self._title = QLabel(self._purpose.display_name)
        self._title.setProperty('h4', True)
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._wdgInfo = QWidget(self)
        vbox(self._wdgInfo)
        if self._purpose.type == ScenePurposeType.Story or self._purpose.type == ScenePurposeType.Character:
            margins(self._wdgInfo, top=20)
        else:
            margins(self._wdgInfo, top=40)

        if self._purpose.keywords:
            self._wdgInfo.layout().addWidget(label('Keywords:', underline=True))
            keywords = ', '.join(self._purpose.keywords)
            lbl = label(keywords, description=True, wordWrap=True)
            self._wdgInfo.layout().addWidget(wrap(lbl, margin_left=5))
        if self._purpose.pacing:
            lbl = label('Pacing:', underline=True)
            self._wdgInfo.layout().addWidget(wrap(lbl, margin_top=10))
            lbl = label(self._purpose.pacing, description=True)
            self._wdgInfo.layout().addWidget(wrap(lbl, margin_left=5))
        if self._purpose.include:
            lbl = label('May include:', underline=True)
            icons = QWidget()
            icons.setToolTip(self._purpose.help_include)
            hbox(icons, 0, 3)
            margins(icons, left=5)
            for type in self._purpose.include:
                icon = Icon()
                icon.setIcon(purpose_icon(type))
                icon.setDisabled(True)
                icon.setToolTip(scene_purposes[type].display_name)
                icons.layout().addWidget(icon)
            icons.layout().addWidget(spacer())
            self._wdgInfo.layout().addWidget(wrap(lbl, margin_top=10))
            self._wdgInfo.layout().addWidget(icons)

        self._wdgInfo.setHidden(True)
        retain_when_hidden(self._wdgInfo)

        pointy(self)
        vbox(self)
        self.layout().addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._wdgInfo)
        self.layout().addWidget(vspacer())

        self.installEventFilter(OpacityEventFilter(self))

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            self.mousePressEvent(event)
            return False
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.mouseReleaseEvent(event)
            return False
        return super().eventFilter(watched, event)

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._setBgColor(0.1)
        event.accept()

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._setBgColor()
        event.accept()
        self.clicked.emit()

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        self._icon.setEnabled(True)
        self._setBgColor()
        self._wdgInfo.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        self._icon.setDisabled(True)
        self._wdgInfo.setHidden(True)
        self.setStyleSheet('')

    def _setBgColor(self, opacity: float = 0.04):
        if self._purpose.type == ScenePurposeType.Story:
            self._bgRgb = '254, 74, 73'
        elif self._purpose.type == ScenePurposeType.Reaction:
            self._bgRgb = '75, 134, 180'
        else:
            self._bgRgb = '144, 151, 156'
        self.setStyleSheet(f'ScenePurposeWidget {{background-color: rgba({self._bgRgb}, {opacity});}}')


class ScenePurposeSelectorWidget(QWidget):
    skipped = pyqtSignal()
    selected = pyqtSignal(ScenePurpose)

    def __init__(self, parent=None):
        super().__init__(parent)

        vbox(self)
        self._btnSkip = QPushButton('Ignore')
        self._btnSkip.setIcon(IconRegistry.from_name('ri.share-forward-fill'))
        underline(self._btnSkip)
        transparent(self._btnSkip)
        pointy(self._btnSkip)
        self._btnSkip.installEventFilter(OpacityEventFilter(self._btnSkip))
        self._btnSkip.installEventFilter(ButtonPressResizeEventFilter(self._btnSkip))
        self._btnSkip.clicked.connect(self.skipped.emit)
        self.layout().addWidget(self._btnSkip, alignment=Qt.AlignmentFlag.AlignRight)
        self.layout().addWidget(label("Select the scene's main purpose:", bold=True),
                                alignment=Qt.AlignmentFlag.AlignCenter)

        self._scrollarea, self._wdgPurposes = scrolled(self, frameless=True)
        self._wdgPurposes.setProperty('relaxed-white-bg', True)
        sp(self._scrollarea).h_exp().v_exp()
        sp(self._wdgPurposes).h_exp().v_exp()
        hbox(self._wdgPurposes, 0, 0)
        margins(self._wdgPurposes, top=10)

        self._wdgPurposes.layout().addWidget(spacer())
        for purpose in [advance_story_scene_purpose, reaction_story_scene_purpose, character_story_scene_purpose,
                        setup_story_scene_purpose, emotion_story_scene_purpose, exposition_story_scene_purpose]:
            wdg = ScenePurposeWidget(purpose)
            wdg.clicked.connect(partial(self.selected.emit, purpose))
            self._wdgPurposes.layout().addWidget(wdg)
        self._wdgPurposes.layout().insertWidget(3, vline())
        self._wdgPurposes.layout().addWidget(spacer())


class SceneElementIconDisplayMode(Enum):
    Center = 0
    Left = 1


class SceneElementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        vbox(self, 0, 0)

        self._btnClose = RemovalButton()
        retain_when_hidden(self._btnClose)
        self._btnClose.clicked.connect(self.deactivate)
        self.layout().addWidget(self._btnClose, alignment=Qt.AlignmentFlag.AlignRight)

        self._stackWidget = QStackedWidget(self)
        self.layout().addWidget(self._stackWidget)

        self._pageIdle = QWidget()
        self._pageIdle.installEventFilter(OpacityEventFilter(self._pageIdle))
        self._pageIdle.installEventFilter(self)
        self._pageEditor = QWidget()
        self._stackWidget.addWidget(self._pageIdle)
        self._stackWidget.addWidget(self._pageEditor)

        self._colorActive: Optional[QColor] = None
        self._iconActive = Icon()
        self._iconActive.setIconSize(QSize(48, 48))
        self._iconIdle = Icon()
        self._iconIdle.setIconSize(QSize(48, 48))
        self._iconIdle.clicked.connect(self.activate)
        self._titleActive = label('', h4=True)
        self._titleIdle = label('', description=True, italic=True, h4=True)

        vbox(self._pageIdle)
        vbox(self._pageEditor)

        self._pageEditor.layout().addWidget(self._iconActive, alignment=Qt.AlignmentFlag.AlignCenter)
        self._pageEditor.layout().addWidget(self._titleActive, alignment=Qt.AlignmentFlag.AlignCenter)

        self._pageIdle.layout().addWidget(self._iconIdle, alignment=Qt.AlignmentFlag.AlignCenter)
        self._pageIdle.layout().addWidget(self._titleIdle, alignment=Qt.AlignmentFlag.AlignCenter)

        self._lblClick = label('Click to add', underline=True, description=True)
        retain_when_hidden(self._lblClick)
        self._lblClick.setHidden(True)
        self._pageIdle.layout().addWidget(self._lblClick, alignment=Qt.AlignmentFlag.AlignCenter)
        self._pageIdle.layout().addWidget(vspacer())

        self.deactivate()

    @overrides
    def eventFilter(self, watched: 'QObject', event: 'QEvent') -> bool:
        if event.type() == QEvent.Type.MouseButtonRelease:
            self.activate()

        return super().eventFilter(watched, event)

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        if self._stackWidget.currentWidget() == self._pageIdle:
            self._lblClick.setVisible(True)
        else:
            self._btnClose.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        if self._stackWidget.currentWidget() == self._pageIdle:
            self._lblClick.setVisible(False)
        else:
            self._btnClose.setVisible(False)

    def setIcon(self, icon: str, colorActive: str):
        self._colorActive = QColor(colorActive)
        self._iconActive.setIcon(IconRegistry.from_name(icon, colorActive))
        self._iconIdle.setIcon(IconRegistry.from_name(icon, 'lightgrey'))

    def setText(self, text: str):
        self._titleActive.setText(text)
        self._titleIdle.setText(text)

    def setValue(self, value: Any):
        self._stackWidget.setCurrentWidget(self._pageEditor)
        self._updateValue(value)

    def activate(self):
        self._pageIdle.setDisabled(True)
        self._stackWidget.setCurrentWidget(self._pageEditor)
        qtanim.glow(self._iconActive, color=self._colorActive)

    def deactivate(self):
        self._btnClose.setHidden(True)
        self._pageIdle.setEnabled(True)
        self._stackWidget.setCurrentWidget(self._pageIdle)
        pointy(self._pageIdle)

    @abstractmethod
    def _updateValue(self, value: Any):
        pass


class TextBasedSceneElementWidget(SceneElementWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._textEditor = QTextEdit()
        self._textEditor.setMinimumWidth(170)
        self._textEditor.setMaximumWidth(200)
        self._textEditor.setMaximumHeight(100)
        self._textEditor.setTabChangesFocus(True)
        self._textEditor.setAcceptRichText(False)
        self._textEditor.verticalScrollBar().setHidden(True)
        self._textEditor.setProperty('rounded', True)
        self._textEditor.setProperty('white-bg', True)

        self._pageEditor.layout().addWidget(self._textEditor)

    def setPlaceholderText(self, text: str):
        self._textEditor.setPlaceholderText(text)

    @overrides
    def activate(self):
        def glowText():
            qtanim.glow(self._textEditor, color=self._colorActive)

        super().activate()
        anim = qtanim.fade_in(self._textEditor, duration=150)
        anim.finished.connect(glowText)

    @overrides
    def _updateValue(self, value: Any):
        pass


class PlotSceneElementEditor(TextBasedSceneElementWidget):
    def __init__(self, parent=None):
        super().__init__(parent)


class AbstractSceneElementsEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        vbox(self)
        sp(self).h_exp()
        self._scrollarea, self._wdgElementsParent = scrolled(self, frameless=True)
        self._wdgElementsParent.setProperty('relaxed-white-bg', True)
        vbox(self._wdgElementsParent)

        self._wdgElementsTopRow = QWidget()
        flow(self._wdgElementsTopRow)
        self._wdgElementsBottomRow = QWidget()
        flow(self._wdgElementsBottomRow)

        self._lblBottom = label('', underline=True)
        self._wdgElementsParent.layout().addWidget(self._wdgElementsTopRow)
        self._wdgElementsParent.layout().addWidget(self._lblBottom)
        self._wdgElementsParent.layout().addWidget(self._wdgElementsBottomRow)


class SceneStorylineEditor(AbstractSceneElementsEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lblBottom.setText('Character relations')

        self._plotElement = PlotSceneElementEditor()
        self._plotElement.setText('Plot')
        self._plotElement.setIcon('fa5s.theater-masks', 'grey')
        self._plotElement.setPlaceholderText('Describe how this scene is related to the selected plot')

        self._themeElement = TextBasedSceneElementWidget()
        self._themeElement.setText('Theme')
        self._themeElement.setIcon('mdi.butterfly-outline', '#9d4edd')

        self._outcomeElement = TextBasedSceneElementWidget()
        self._outcomeElement.setText('Outcome')
        self._outcomeElement.setIcon('fa5s.bomb', '#f4442e')

        self._consequencesElement = TextBasedSceneElementWidget()
        self._consequencesElement.setText('Consequences')
        self._consequencesElement.setIcon('mdi.ray-start-arrow', 'black')

        self._wdgElementsTopRow.layout().addWidget(self._plotElement)
        self._wdgElementsTopRow.layout().addWidget(self._themeElement)
        self._wdgElementsTopRow.layout().addWidget(self._outcomeElement)
        self._wdgElementsTopRow.layout().addWidget(self._consequencesElement)


class SceneAgendaEditor(AbstractSceneElementsEditor):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel

        self._lblBottom.setText('Character changes')

        self._btnCharacterSelector = CharacterSelectorButton(self._novel)
        self.layout().insertWidget(0, self._btnCharacterSelector)

    def updateAvailableCharacters(self, characters: List[Character]):
        pass
