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
from functools import partial
from typing import List, Optional, Dict

import qtanim
from PyQt6.QtCore import Qt, QSize, QEvent, pyqtSignal, QObject
from PyQt6.QtGui import QEnterEvent, QIcon, QMouseEvent, QColor
from PyQt6.QtWidgets import QWidget, QTextEdit, QPushButton, QLabel, QFrame, QStackedWidget, QTabBar
from overrides import overrides
from qthandy import vbox, vspacer, transparent, sp, line, incr_font, hbox, pointy, vline, retain_when_hidden, margins, \
    spacer, underline, bold, gc, curved_flow, flow, clear_layout
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import raise_unrecognized_arg, CONFLICT_SELF_COLOR
from src.main.python.plotlyst.core.domain import Scene, Novel, ScenePurpose, advance_story_scene_purpose, \
    ScenePurposeType, reaction_story_scene_purpose, character_story_scene_purpose, setup_story_scene_purpose, \
    emotion_story_scene_purpose, exposition_story_scene_purpose, scene_purposes, Character, Plot, ScenePlotReference, \
    StoryElement, StoryElementType, SceneOutcome, SceneStructureAgenda, PlotType, Motivation
from src.main.python.plotlyst.event.core import EventListener, Event, emit_event
from src.main.python.plotlyst.event.handler import event_dispatchers
from src.main.python.plotlyst.events import SceneChangedEvent
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import DelayedSignalSlotConnector, action, wrap, label, scrolled, \
    ButtonPressResizeEventFilter, insert_after, tool_btn, shadow
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorButton
from src.main.python.plotlyst.view.widget.display import Icon
from src.main.python.plotlyst.view.widget.input import RemovalButton
from src.main.python.plotlyst.view.widget.scene.agency import SceneAgendaEmotionEditor, SceneAgendaMotivationEditor
from src.main.python.plotlyst.view.widget.scene.conflict import ConflictIntensityEditor, CharacterConflictSelector
from src.main.python.plotlyst.view.widget.scene.plot import ScenePlotSelectorButton, ScenePlotValueEditor, \
    PlotValuesDisplay
from src.main.python.plotlyst.view.widget.scenes import SceneOutcomeSelector


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
    reset = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene: Optional[Scene] = None
        pointy(self)
        self._opacityFilter = OpacityEventFilter(self, 0.8, 1.0, ignoreCheckedButton=True)
        self.installEventFilter(self._opacityFilter)

        self._menu = MenuWidget(self)
        self._menu.addAction(action('Select new purpose', slot=self.reset.emit))

        self.refresh()

    def setScene(self, scene: Scene):
        self._scene = scene
        self.refresh()

    def refresh(self):
        if self._scene is None or self._scene.purpose is None:
            return
        IconRegistry.action_scene_icon()
        if self._scene.purpose == ScenePurposeType.Other:
            self.setText('')
            self.setToolTip('Scene purpose not selected')
        else:
            purpose = scene_purposes.get(self._scene.purpose)
            tip = purpose.display_name.replace('\n', ' ')
            self.setText(tip)
            self.setToolTip(f'Scene purpose: {tip}')

        if self._scene.purpose == ScenePurposeType.Exposition:
            self.setIcon(IconRegistry.exposition_scene_icon())
        elif self._scene.purpose == ScenePurposeType.Setup:
            self.setIcon(IconRegistry.setup_scene_icon())
        elif self._scene.purpose == ScenePurposeType.Character:
            self.setIcon(IconRegistry.character_development_scene_icon())
        elif self._scene.purpose == ScenePurposeType.Emotion:
            self.setIcon(IconRegistry.emotion_scene_icon())

        bold(self, self._scene.purpose != ScenePurposeType.Other)

        if self._scene.purpose == ScenePurposeType.Story:
            bgColor = '#f4978e'
            borderColor = '#fb5607'
            resolution = self._scene.outcome == SceneOutcome.RESOLUTION
            trade_off = self._scene.outcome == SceneOutcome.TRADE_OFF

            self.setIcon(IconRegistry.action_scene_icon(resolution, trade_off))
            if resolution:
                bgColor = '#12BB86'
                borderColor = '#0b6e4f'
            elif trade_off:
                bgColor = '#E188C2'
                borderColor = '#832161'
        elif self._scene.purpose == ScenePurposeType.Reaction:
            bgColor = '#89c2d9'
            borderColor = '#1a759f'
            self.setIcon(IconRegistry.reaction_scene_icon())
        elif self._scene.purpose == ScenePurposeType.Other:
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
        self.setMaximumWidth(190)

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


class SceneElementWidget(QWidget):
    def __init__(self, type: StoryElementType, parent=None):
        super().__init__(parent)
        self._type = type
        self._scene: Optional[Scene] = None
        self._element: Optional[StoryElement] = None
        vbox(self, 0, 0)

        self._btnClose = RemovalButton()
        retain_when_hidden(self._btnClose)
        self._btnClose.clicked.connect(self._deactivate)
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

        self.reset()

    def element(self) -> Optional[StoryElement]:
        return self._element

    def setScene(self, scene: Scene):
        self._scene = scene
        self.reset()

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

    def setIcon(self, icon: str, colorActive: str = 'black'):
        self._colorActive = QColor(colorActive)
        self._iconActive.setIcon(IconRegistry.from_name(icon, colorActive))
        self._iconIdle.setIcon(IconRegistry.from_name(icon, 'lightgrey'))

    def setTitle(self, text: str, color: Optional[str] = None):
        self._titleActive.setText(text)
        self._titleIdle.setText(text)
        if color:
            self._titleActive.setStyleSheet(f'color: {color};')
        else:
            self._titleActive.setStyleSheet('')

    def setElement(self, element: StoryElement):
        self._element = element

        self._pageIdle.setDisabled(True)
        self._stackWidget.setCurrentWidget(self._pageEditor)

    def reset(self):
        self._btnClose.setHidden(True)
        self._pageIdle.setEnabled(True)
        self._stackWidget.setCurrentWidget(self._pageIdle)
        pointy(self._pageIdle)
        self._element = None

    def activate(self):
        element = StoryElement(self._type)
        self.setElement(element)
        self._btnClose.setVisible(True)

        qtanim.glow(self._iconActive, duration=150, color=self._colorActive)
        self._elementCreated(element)

    def _deactivate(self):
        self._elementRemoved(self._element)
        self.reset()

    def _storyElements(self) -> List[StoryElement]:
        return self._scene.story_elements

    def _elementCreated(self, element: StoryElement):
        self._storyElements().append(element)

    def _elementRemoved(self, element: StoryElement):
        self._storyElements().remove(element)


class TextBasedSceneElementWidget(SceneElementWidget):
    def __init__(self, type: StoryElementType, parent=None):
        super().__init__(type, parent)

        self._textEditor = QTextEdit()
        self._textEditor.setMinimumWidth(170)
        self._textEditor.setMaximumWidth(200)
        self._textEditor.setMaximumHeight(100)
        self._textEditor.setTabChangesFocus(True)
        self._textEditor.setAcceptRichText(False)
        self._textEditor.verticalScrollBar().setHidden(True)
        self._textEditor.setProperty('rounded', True)
        self._textEditor.setProperty('white-bg', True)
        self._textEditor.textChanged.connect(self._textChanged)

        self._pageEditor.layout().addWidget(self._textEditor)

    def setPlaceholderText(self, text: str):
        self._textEditor.setPlaceholderText(text)

    @overrides
    def setElement(self, element: StoryElement):
        super().setElement(element)
        self._textEditor.setText(element.text)

    def _textChanged(self):
        if self._element:
            self._element.text = self._textEditor.toPlainText()

    @overrides
    def activate(self):
        super().activate()
        anim = qtanim.fade_in(self._textEditor, duration=150)
        anim.finished.connect(self._activateFinished)

    def _activateFinished(self):
        qtanim.glow(self._textEditor, color=self._colorActive)


class OutcomeSceneElementEditor(TextBasedSceneElementWidget):
    outcomeChanged = pyqtSignal(SceneOutcome)

    def __init__(self, parent=None):
        super().__init__(StoryElementType.Outcome, parent)
        self._outcomeSelector = SceneOutcomeSelector(autoSelect=False)
        self.setPlaceholderText('Is there an imminent outcome in this scene?')

        self._pageEditor.layout().addWidget(self._outcomeSelector, alignment=Qt.AlignmentFlag.AlignCenter)
        self._outcomeSelector.selected.connect(self._outcomeSelected)

    @overrides
    def setElement(self, element: StoryElement):
        super().setElement(element)
        if self._scene.outcome:
            self._outcomeSelector.refresh(self._scene.outcome)
            self._updateOutcome()
        else:
            self._outcomeSelector.reset()
            self._resetTitle()

    @overrides
    def reset(self):
        super().reset()
        self._resetTitle()

    def refresh(self):
        self._outcomeSelector.refresh(self._scene.outcome)
        self._updateOutcome()

    def _resetTitle(self):
        self.setTitle('Outcome')
        self.setIcon('fa5s.bomb', 'grey')

    def _outcomeSelected(self, outcome: SceneOutcome):
        self._scene.outcome = outcome
        self._updateOutcome()
        self.outcomeChanged.emit(outcome)

    def _updateOutcome(self):
        if self._scene.outcome == SceneOutcome.DISASTER:
            color = '#f4442e'
            self.setIcon('fa5s.bomb', color)
        elif self._scene.outcome == SceneOutcome.RESOLUTION:
            color = '#0b6e4f'
            self.setIcon('mdi.bullseye-arrow', color)
        elif self._scene.outcome == SceneOutcome.TRADE_OFF:
            color = '#832161'
            self.setIcon('fa5s.balance-scale-left', color)
        else:
            return
        self.setTitle(f'{SceneOutcome.to_str(self._scene.outcome)} outcome', color)


class StorylineElementEditor(TextBasedSceneElementWidget):
    plotSelected = pyqtSignal()

    def __init__(self, novel: Novel, type: StoryElementType, parent=None):
        super().__init__(type, parent)
        self._novel = novel

        self._plotValueEditor: Optional[ScenePlotValueEditor] = None
        self._plotValueDisplay: Optional[PlotValuesDisplay] = None

        self._btnPlotSelector = ScenePlotSelectorButton(self._novel)
        self._btnPlotSelector.plotSelected.connect(self._plotSelected)
        self._btnPlotSelector.setFixedHeight(self._titleActive.sizeHint().height())
        self._titleActive.setHidden(True)
        insert_after(self._pageEditor, self._btnPlotSelector, reference=self._titleActive,
                     alignment=Qt.AlignmentFlag.AlignCenter)

        self._wdgValues = QWidget()
        self._wdgValues.setHidden(True)
        vbox(self._wdgValues)
        self._btnEditValues = QPushButton('Edit values')
        self._btnEditValues.installEventFilter(OpacityEventFilter(self._btnEditValues, enterOpacity=0.7))
        self._btnEditValues.installEventFilter(ButtonPressResizeEventFilter(self._btnEditValues))
        self._btnEditValues.setIcon(IconRegistry.from_name('fa5s.chevron-circle-down', 'grey'))
        self._plotValueMenu = MenuWidget(self._btnEditValues)
        self._btnEditValues.setProperty('no-menu', True)
        transparent(self._btnEditValues)
        self._wdgValues.layout().addWidget(self._btnEditValues)

        self._pageEditor.layout().addWidget(self._wdgValues)

    @overrides
    def setScene(self, scene: Scene):
        super().setScene(scene)
        self._btnPlotSelector.setScene(scene)
        self._plotRef = None

    @overrides
    def setElement(self, element: StoryElement):
        super().setElement(element)

        if element.ref:
            plot_ref = next((x for x in self._scene.plot_values if x.plot.id == element.ref), None)
            if plot_ref:
                self._setPlotRef(plot_ref)

    @overrides
    def _deactivate(self):
        super()._deactivate()
        if self._plotRef:
            self._scene.plot_values.remove(self._plotRef)

    @overrides
    def _activateFinished(self):
        if self._novel.plots:
            self._btnPlotSelector.menuWidget().exec()

    def _plotSelected(self, plot: Plot):
        plotRef = ScenePlotReference(plot)
        self._scene.plot_values.append(plotRef)
        self._element.ref = plotRef.plot.id

        self._setPlotRef(plotRef)

        self.plotSelected.emit()

    def _setPlotRef(self, plotRef: ScenePlotReference):
        self._plotRef = plotRef
        self.setIcon(self._plotRef.plot.icon, self._plotRef.plot.icon_color)
        font = self._btnPlotSelector.font()
        font.setPointSize(self._titleActive.font().pointSize())
        self._btnPlotSelector.setFont(font)
        self._btnPlotSelector.setPlot(plotRef.plot)

        self._wdgValues.setVisible(True)

        self._plotValueEditor = ScenePlotValueEditor(self._plotRef)
        self._plotValueMenu.clear()
        self._plotValueMenu.addWidget(self._plotValueEditor)

        self._plotValueDisplay = PlotValuesDisplay(self._plotRef)
        self._plotValueEditor.charged.connect(self._plotValueDisplay.updateValue)

        for value in plotRef.data.values:
            plot_value = value.plot_value(self._plotRef.plot)
            if plot_value:
                self._plotValueDisplay.updateValue(plot_value, value)

        self._wdgValues.layout().addWidget(self._plotValueDisplay)


class PlotSceneElementEditor(StorylineElementEditor):
    def __init__(self, novel: Novel, parent=None):
        self._plotRef: Optional[ScenePlotReference] = None
        super().__init__(novel, StoryElementType.Plot, parent)
        self.setTitle('Storyline')
        self.setIcon('fa5s.theater-masks')
        self.setPlaceholderText('Describe how this scene is related to the selected storyline')

        self._btnPlotSelector.menuWidget().filterAll(False)
        self._btnPlotSelector.menuWidget().filterPlotType(PlotType.Main, True)
        self._btnPlotSelector.menuWidget().filterPlotType(PlotType.Global, True)
        self._btnPlotSelector.menuWidget().filterPlotType(PlotType.Subplot, True)


class ArcSceneElementEditor(StorylineElementEditor):
    def __init__(self, novel: Novel, parent=None):
        self._plotRef: Optional[ScenePlotReference] = None
        super().__init__(novel, StoryElementType.Arc, parent)
        self._agenda: Optional[SceneStructureAgenda] = None
        self.setPlaceholderText('Describe how the character progresses in their character arc')

        self._btnPlotSelector.menuWidget().filterAll(False)
        self._btnPlotSelector.menuWidget().filterPlotType(PlotType.Internal, True)

    @overrides
    def setScene(self, scene: Scene):
        super().setScene(scene)
        self._agenda = scene.agendas[0]

    @overrides
    def reset(self):
        super().reset()
        self.setTitle('Character change')
        self.setIcon('mdi.mirror', CONFLICT_SELF_COLOR)

    @overrides
    def _storyElements(self) -> List[StoryElement]:
        return self._agenda.story_elements


class AgencyTextBasedElementEditor(TextBasedSceneElementWidget):
    def __init__(self, type: StoryElementType, parent=None):
        super().__init__(type, parent)
        self._agenda: Optional[SceneStructureAgenda] = None

    def setAgenda(self, agenda: SceneStructureAgenda):
        self._agenda = agenda
        self.reset()

    @overrides
    def _storyElements(self) -> List[StoryElement]:
        return self._agenda.story_elements


class ConflictElementEditor(AgencyTextBasedElementEditor):
    def __init__(self, parent=None):
        super().__init__(StoryElementType.Conflict, parent)
        self._novel: Optional[Novel] = None

        self.setTitle('Conflict')
        self.setIcon('mdi.sword-cross', '#f3a712')
        self.setPlaceholderText("What kind of conflict does the character have to face?")

        self._sliderIntensity = ConflictIntensityEditor()
        self._sliderIntensity.intensityChanged.connect(self._intensityChanged)

        self._wdgConflicts = QWidget()
        flow(self._wdgConflicts)

        self._wdgTracking = QWidget()
        vbox(self._wdgTracking, spacing=0)
        self._wdgTracking.layout().addWidget(label('Intensity'), alignment=Qt.AlignmentFlag.AlignLeft)
        self._wdgTracking.layout().addWidget(self._sliderIntensity)
        self._wdgTracking.layout().addWidget(line())
        self._wdgTracking.layout().addWidget(self._wdgConflicts)

        self._pageEditor.layout().addWidget(self._wdgTracking)

    @overrides
    def setScene(self, scene: Scene, novel: Novel):
        super().setScene(scene)
        self._novel = novel
        clear_layout(self._wdgConflicts)

    @overrides
    def setAgenda(self, agenda: SceneStructureAgenda):
        super().setAgenda(agenda)
        for ref in agenda.conflict_references:
            conflictSelector = CharacterConflictSelector(self._novel, self._scene)
            conflictSelector.setConflict(ref.conflict(self._novel), ref)
            self._wdgConflicts.layout().addWidget(conflictSelector)

        conflictSelector = CharacterConflictSelector(self._novel, self._scene,
                                                     simplified=len(agenda.conflict_references) > 0)
        conflictSelector.conflictSelected.connect(self._conflictSelected)
        self._wdgConflicts.layout().addWidget(conflictSelector)

    @overrides
    def setElement(self, element: StoryElement):
        super().setElement(element)
        self._sliderIntensity.setValue(element.intensity)

    def _intensityChanged(self, value: int):
        self._element.intensity = value
        shadow(self._iconActive, offset=0, radius=value * 2, color=QColor('#f3a712'))
        shadow(self._titleActive, offset=0, radius=value, color=QColor('#f3a712'))
        shadow(self._textEditor, offset=0, radius=value * 2, color=QColor('#f3a712'))

    def _conflictSelected(self):
        conflictSelector = CharacterConflictSelector(self._novel, self._scene, simplified=True)
        conflictSelector.conflictSelected.connect(self._conflictSelected)
        self._wdgConflicts.layout().addWidget(conflictSelector)


class AbstractSceneElementsEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene: Optional[Scene] = None
        self._storylineElements: List[PlotSceneElementEditor] = []

        hbox(self)
        sp(self).h_exp()
        self._scrollarea, self._wdgElementsParent = scrolled(self, frameless=True)
        self._wdgElementsParent.setProperty('relaxed-white-bg', True)
        vbox(self._wdgElementsParent)

        self._wdgHeader = QWidget()
        hbox(self._wdgHeader)
        self._wdgElementsTopRow = QWidget()
        curved_flow(self._wdgElementsTopRow, spacing=8)
        self._wdgElementsBottomRow = QWidget()
        curved_flow(self._wdgElementsBottomRow, spacing=8)

        self._lblBottom = label('', underline=True)
        self._wdgElementsParent.layout().addWidget(self._wdgHeader)
        self._wdgElementsParent.layout().addWidget(self._wdgElementsTopRow)
        self._wdgElementsParent.layout().addWidget(self._lblBottom)
        self._wdgElementsParent.layout().addWidget(self._wdgElementsBottomRow)

    def setScene(self, scene: Scene):
        self._scene = scene

        for wdg in self._storylineElements:
            self._wdgElementsTopRow.layout().removeWidget(wdg)
            gc(wdg)
        self._storylineElements.clear()

    def _newLine(self) -> QFrame:
        line = vline()
        line.setMinimumHeight(200)

        return line


class SceneStorylineEditor(AbstractSceneElementsEditor):
    outcomeChanged = pyqtSignal(SceneOutcome)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel

        self.__newPlotElementEditor()

        self._btnAddNewPlot = tool_btn(IconRegistry.plus_circle_icon('grey'), 'Add new storyline', transparent_=True,
                                       parent=self._wdgElementsTopRow)
        self._btnAddNewPlot.installEventFilter(OpacityEventFilter(self._btnAddNewPlot))
        self._btnAddNewPlot.clicked.connect(self._addNewPlot)

        self._wdgAddNewPlotParent = QWidget()
        vbox(self._wdgAddNewPlotParent)
        margins(self._wdgAddNewPlotParent, top=self._storylineElements[0].sizeHint().height() // 2, left=5, right=5)
        icon = Icon()
        icon.setIcon(IconRegistry.from_name('fa5s.theater-masks', 'lightgrey'))
        self._wdgAddNewPlotParent.layout().addWidget(icon)
        self._wdgAddNewPlotParent.layout().addWidget(self._btnAddNewPlot)
        self._wdgAddNewPlotParent.setHidden(True)

        # self._themeElement = TextBasedSceneElementWidget()
        # self._themeElement.setText('Theme')
        # self._themeElement.setIcon('mdi.butterfly-outline', '#9d4edd')

        self._outcomeElement = OutcomeSceneElementEditor()
        self._outcomeElement.outcomeChanged.connect(self.outcomeChanged.emit)

        self._consequencesElement = TextBasedSceneElementWidget(StoryElementType.Consequences)
        self._consequencesElement.setTitle('Consequences')
        self._consequencesElement.setIcon('mdi.ray-start-arrow')
        self._consequencesElement.setPlaceholderText("Are there any imminent or later consequences of this scene?")

        self._wdgElementsTopRow.layout().addWidget(self._outcomeElement)
        self._wdgElementsTopRow.layout().addWidget(self._newLine())
        self._wdgElementsTopRow.layout().addWidget(self._storylineElements[0])

        self._wdgElementsTopRow.layout().addWidget(self._newLine())
        self._wdgElementsTopRow.layout().addWidget(self._consequencesElement)

    @overrides
    def setScene(self, scene: Scene):
        super().setScene(scene)
        self._outcomeElement.setScene(scene)
        self._consequencesElement.setScene(scene)

        for element in scene.story_elements:
            if element.type == StoryElementType.Outcome:
                self._outcomeElement.setElement(element)
            elif element.type == StoryElementType.Consequences:
                self._consequencesElement.setElement(element)
            elif element.type == StoryElementType.Plot:
                wdg = self.__newPlotElementEditor()
                wdg.setElement(element)

        if not self._storylineElements:
            self.__newPlotElementEditor()

        for i, wdg in enumerate(self._storylineElements):
            self._wdgElementsTopRow.layout().insertWidget(i + 2, wdg)

        last_plot_element = self._storylineElements[-1].element()
        if last_plot_element and last_plot_element.ref:
            insert_after(self._wdgElementsTopRow, self._wdgAddNewPlotParent, reference=self._storylineElements[-1])
            self._wdgAddNewPlotParent.setVisible(True)

    def refresh(self):
        self._outcomeElement.refresh()

    def _plotSelected(self, plotElement: PlotSceneElementEditor):
        insert_after(self._wdgElementsTopRow, self._wdgAddNewPlotParent, reference=plotElement)
        self._wdgAddNewPlotParent.setVisible(True)

    def _addNewPlot(self):
        elementEditor = self.__newPlotElementEditor()
        insert_after(self._wdgElementsTopRow, elementEditor, reference=self._wdgAddNewPlotParent)
        self._wdgAddNewPlotParent.setHidden(True)
        self._wdgElementsTopRow.layout().removeWidget(self._wdgAddNewPlotParent)

        elementEditor.activate()

    def __newPlotElementEditor(self) -> PlotSceneElementEditor:
        elementEditor = PlotSceneElementEditor(self._novel)
        elementEditor.plotSelected.connect(partial(self._plotSelected, elementEditor))

        if self._scene:
            elementEditor.setScene(self._scene)

        self._storylineElements.append(elementEditor)

        return elementEditor


class CharacterTabBar(QTabBar):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._character: Optional[Character] = None
        sp(self).h_max()
        self.setShape(QTabBar.Shape.RoundedWest)

        self._btnCharacterSelector = CharacterSelectorButton(self._novel, parent=self)
        self.addTab('')

        self._btnCharacterSelector.characterSelected.connect(self._characterSelected)

    @overrides
    def tabSizeHint(self, index: int) -> QSize:
        return QSize(self._btnCharacterSelector.sizeHint().width(), 80)

    def _characterSelected(self, character: Character):
        self._character = character


class SceneAgendaEditor(AbstractSceneElementsEditor):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel

        self._lblBottom.setText('Character relations')

        self._characterTabbar = CharacterTabBar(self._novel)
        self.layout().insertWidget(0, self._characterTabbar, alignment=Qt.AlignmentFlag.AlignTop)

        self._emotionEditor = SceneAgendaEmotionEditor()
        self._emotionEditor.emotionChanged.connect(self._emotionChanged)
        self._emotionEditor.emotionReset.connect(self._emotionReset)
        self._motivationEditor = SceneAgendaMotivationEditor()
        self._motivationEditor.motivationChanged.connect(self._motivationChanged)
        self._motivationEditor.motivationReset.connect(self._motivationReset)

        margins(self._wdgHeader, left=25)
        self._wdgHeader.layout().setSpacing(10)
        self._wdgHeader.layout().addWidget(self._emotionEditor)
        self._wdgHeader.layout().addWidget(vline())
        self._wdgHeader.layout().addWidget(self._motivationEditor)
        self._wdgHeader.layout().addWidget(spacer())
        self._wdgElementsParent.layout().insertWidget(1, line())

        self._arcElement = ArcSceneElementEditor(self._novel)

        self._goalElement = AgencyTextBasedElementEditor(StoryElementType.Goal)
        self._goalElement.setTitle('Goal')
        self._goalElement.setIcon('mdi.target', 'darkBlue')
        self._goalElement.setPlaceholderText("What's the character's goal in this scene?")

        self._conflictElement = ConflictElementEditor()

        self._decisionElement = AgencyTextBasedElementEditor(StoryElementType.Decision)
        self._decisionElement.setTitle('Decision')
        self._decisionElement.setIcon('fa5s.map-signs', '#ba6f4d')

        self._wdgElementsTopRow.layout().addWidget(self._goalElement)
        self._wdgElementsTopRow.layout().addWidget(self._conflictElement)
        self._wdgElementsTopRow.layout().addWidget(self._newLine())
        self._wdgElementsTopRow.layout().addWidget(self._decisionElement)
        self._wdgElementsTopRow.layout().addWidget(self._newLine())
        self._wdgElementsTopRow.layout().addWidget(self._arcElement)

    @overrides
    def setScene(self, scene: Scene):
        super().setScene(scene)
        agenda = scene.agendas[0]
        self._arcElement.setScene(scene)
        if agenda.emotion is None:
            self._emotionEditor.reset()
        else:
            self._emotionEditor.setValue(agenda.emotion)
        if agenda.motivations:
            print('has moti')
            values: Dict[Motivation, int] = {}
            for k, v in agenda.motivations.items():
                motivation = Motivation(k)
                values[motivation] = v

            self._motivationEditor.setValues(values)
        else:
            print('no moti')
            self._motivationEditor.reset()

        self._goalElement.setAgenda(agenda)
        self._conflictElement.setScene(scene, self._novel)
        self._conflictElement.setAgenda(agenda)
        self._decisionElement.setAgenda(agenda)

        for element in scene.agendas[0].story_elements:
            if element.type == StoryElementType.Goal:
                self._goalElement.setElement(element)
            elif element.type == StoryElementType.Conflict:
                self._conflictElement.setElement(element)
            elif element.type == StoryElementType.Decision:
                self._decisionElement.setElement(element)
            elif element.type == StoryElementType.Arc:
                self._arcElement.setElement(element)
            #     wdg = self.__newPlotElementEditor()
            #     wdg.setElement(element)

    def updateAvailableCharacters(self, characters: List[Character]):
        pass

    def _emotionChanged(self, emotion: int):
        self._scene.agendas[0].emotion = emotion

    def _emotionReset(self):
        self._scene.agendas[0].emotion = None

    def _motivationChanged(self, motivation: Motivation, value: int):
        self._scene.agendas[0].motivations[motivation.value] = value

    def _motivationReset(self):
        self._scene.agendas[0].motivations.clear()
