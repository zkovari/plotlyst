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
from functools import partial
from typing import Optional

import qtanim
from PyQt6.QtCore import Qt, QEvent, pyqtSignal
from PyQt6.QtGui import QColor, QEnterEvent
from PyQt6.QtWidgets import QWidget, QAbstractButton
from overrides import overrides
from qthandy import vbox, incr_icon, incr_font, flow, margins, vspacer, hbox, clear_layout, pointy, gc
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget, ActionTooltipDisplayMode

from plotlyst.common import PLOTLYST_SECONDARY_COLOR
from plotlyst.core.domain import Scene, Novel, StoryElementType, Character, SceneFunction, Plot
from plotlyst.service.cache import characters_registry
from plotlyst.view.common import push_btn, tool_btn, action, shadow, label, fade_out_and_gc
from plotlyst.view.icons import IconRegistry
from plotlyst.view.style.base import apply_white_menu
from plotlyst.view.widget.characters import CharacterSelectorButton
from plotlyst.view.widget.input import TextEditBubbleWidget
from plotlyst.view.widget.scene.plot import SceneFunctionPlotSelectorMenu


# class ScenePrimaryFunctionWidget(OutlineItemWidget):
#     SceneFunctionMimeType: str = 'application/scene-function'
#     functionEdited = pyqtSignal()
#
#     def __init__(self, item: OutlineItem, parent=None):
#         super().__init__(item, parent)
#
#     @overrides
#     def mimeType(self):
#         return self.SceneFunctionMimeType
#
#     def _valueChanged(self):
#         pass


# class EventCauseFunctionWidget(OutlineTimelineWidget):
#     def __init__(self, parent=None):
#         super().__init__(parent, paintTimeline=True, framed=False, layout=LayoutType.HORIZONTAL)
#         margins(self, 0, 0, 0, 0)
#         self.layout().setSpacing(0)
#
#     @overrides
#     def _newBeatWidget(self, item: OutlineItem) -> OutlineItemWidget:
#         wdg = ScenePrimaryFunctionWidget(item)
#         wdg.removed.connect(self._beatRemoved)
#         return wdg
#
#     @overrides
#     def _newPlaceholderWidget(self, displayText: bool = False) -> QWidget:
#         wdg = super()._newPlaceholderWidget(displayText)
#         margins(wdg, top=2)
#         if displayText:
#             wdg.btn.setText('Insert element')
#         wdg.btn.setToolTip('Insert new element')
#         return wdg
#
#     @overrides
#     def _placeholderClicked(self, placeholder: QWidget):
#         self._currentPlaceholder = placeholder
#         item = OutlineItem()
#         widget = self._newBeatWidget(item)
#         self._insertWidget(item, widget)


# class EventCauseFunctionGroupWidget(QWidget):
#     remove = pyqtSignal()
#
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.frame = frame()
#         self.frame.setObjectName('frame')
#         vbox(self.frame, 0, 0)
#
#         self.setStyleSheet(f'''
#                                 #frame {{
#                                     border: 0px;
#                                     border-top: 2px solid {PLOTLYST_SECONDARY_COLOR};
#                                     border-radius: 15px;
#                                 }}''')
#
#         vbox(self)
#         self._wdgPrinciples = EventCauseFunctionWidget()
#         self._wdgPrinciples.setStructure([])
#
#         self._title = IconText()
#         self._title.setText('Cause and effect')
#         incr_icon(self._title, 4)
#         bold(self._title)
#
#         self.btnRemove = RemovalButton()
#         retain_when_hidden(self.btnRemove)
#         self.installEventFilter(VisibilityToggleEventFilter(self.btnRemove, self))
#         self.btnRemove.clicked.connect(self.remove)
#
#         self.frame.layout().addWidget(self._wdgPrinciples)
#         self.layout().addWidget(group(spacer(), self._title, spacer(), self.btnRemove))
#         self.layout().addWidget(self.frame)


class PrimarySceneFunctionWidget(TextEditBubbleWidget):
    def __init__(self, novel: Novel, scene: Scene, function: SceneFunction, parent=None):
        super().__init__(parent)
        self.novel = novel
        self.scene = scene
        self.function = function
        self._removalEnabled = True

        self._textedit.setMinimumSize(165, 100)
        self._textedit.setMaximumSize(180, 110)
        self._textedit.setText(self.function.text)

        margins(self, top=16)

    @overrides
    def _textChanged(self):
        self.function.text = self._textedit.toPlainText()


class _StorylineAssociatedFunctionWidget(PrimarySceneFunctionWidget):
    storylineSelected = pyqtSignal(Plot)
    storylineEditRequested = pyqtSignal(Plot)

    def __init__(self, novel: Novel, scene: Scene, function: SceneFunction, parent=None):
        super().__init__(novel, scene, function, parent)
        pointy(self._title)
        self._menu = SceneFunctionPlotSelectorMenu(novel, self._title)
        self._menu.plotSelected.connect(self._plotSelected)
        self._menu.setScene(scene)

    def _plot(self) -> Optional[Plot]:
        return next((x for x in self.novel.plots if x.id == self.function.ref), None)

    def _setPlotStyle(self, plot: Plot):
        gc(self._menu)
        self._menu = MenuWidget(self._menuParent())
        self._menu.addAction(
            action('Edit', IconRegistry.edit_icon(), slot=partial(self.storylineEditRequested.emit, plot)))
        self._menu.addSeparator()
        self._menu.addAction(action('Remove', IconRegistry.trash_can_icon(), slot=self._plotRemoved))

    def _resetPlotStyle(self):
        pass

    def _menuParent(self) -> QAbstractButton:
        pass

    def _plotSelected(self, plot: Plot):
        self.function.ref = plot.id
        self._setPlotStyle(plot)

    def _plotRemoved(self):
        self.function.ref = None
        # self._btnStorylineLink.setIcon(IconRegistry.storylines_icon(color='lightgrey'))

        # self._btnStorylineLink.clicked.disconnect()
        gc(self._menu)
        self._menu = SceneFunctionPlotSelectorMenu(self.novel, self._menuParent())
        self._menu.plotSelected.connect(self._plotSelected)
        self._menu.setScene(self.scene)
        self._resetPlotStyle()


class PlotPrimarySceneFunctionWidget(_StorylineAssociatedFunctionWidget):
    def __init__(self, novel: Novel, scene: Scene, function: SceneFunction, parent=None):
        super().__init__(novel, scene, function, parent)
        self._textedit.setPlaceholderText("How does the story move forward")
        if self.function.ref:
            storyline = self._plot()
            if storyline is not None:
                self._setPlotStyle(storyline)
        else:
            self._resetPlotStyle()

    @overrides
    def _setPlotStyle(self, plot: Plot):
        super()._setPlotStyle(plot)
        self._title.setIcon(IconRegistry.from_name(plot.icon, plot.icon_color))
        self._title.setText(plot.text)
        shadow(self._textedit, color=QColor(plot.icon_color))

    @overrides
    def _resetPlotStyle(self):
        self._title.setText('Plot')
        self._title.setIcon(IconRegistry.storylines_icon())
        shadow(self._textedit)

    @overrides
    def _menuParent(self):
        return self._title


class MysteryPrimarySceneFunctionWidget(_StorylineAssociatedFunctionWidget):
    def __init__(self, novel: Novel, scene: Scene, function: SceneFunction, parent=None):
        super().__init__(novel, scene, function, parent)
        self._title.setIcon(IconRegistry.from_name('ei.question-sign', PLOTLYST_SECONDARY_COLOR))
        self._title.setText('Mystery')
        self._textedit.setPlaceholderText("What mystery is introduced or deepened")

        self._btnStorylineLink = tool_btn(IconRegistry.storylines_icon(color='lightgrey'), transparent_=True,
                                          tooltip='Link storyline to this element',
                                          parent=self)
        self._btnStorylineLink.installEventFilter(OpacityEventFilter(self._btnStorylineLink, leaveOpacity=0.7))
        self._btnStorylineLink.setGeometry(0, 20, 20, 20)
        self._btnStorylineLink.setDisabled(True)

        if self.function.ref:
            self._btnStorylineLink.setVisible(True)
            storyline = self._plot()
            if storyline is not None:
                self._setPlotStyle(storyline)
        else:
            self._btnStorylineLink.setVisible(False)

        shadow(self._textedit, color=QColor(PLOTLYST_SECONDARY_COLOR))

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        if self.function.ref:
            self._btnStorylineLink.setEnabled(True)
            self._btnStorylineLink.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self._btnStorylineLink.setDisabled(True)
        if not self.function.ref:
            self._btnStorylineLink.setVisible(False)

    @overrides
    def _setPlotStyle(self, plot: Plot):
        super()._setPlotStyle(plot)
        self._btnStorylineLink.setIcon(IconRegistry.from_name(plot.icon, plot.icon_color))

    @overrides
    def _resetPlotStyle(self):
        self._btnStorylineLink.setIcon(IconRegistry.storylines_icon(color='lightgrey'))
        self._btnStorylineLink.setVisible(False)

    @overrides
    def _menuParent(self):
        return self._title


class CharacterPrimarySceneFunctionWidget(PrimarySceneFunctionWidget):
    def __init__(self, novel: Novel, scene: Scene, function: SceneFunction, parent=None):
        super().__init__(novel, scene, function, parent)

        self._title.setIcon(IconRegistry.character_icon())
        self._title.setText('Character insight')
        self._textedit.setPlaceholderText("What do we learn about a character")

        self._title.setHidden(True)
        self._charSelector = CharacterSelectorButton(self.novel, iconSize=32)
        self._charSelector.characterSelected.connect(self._characterSelected)
        wdgHeader = QWidget()
        hbox(wdgHeader, 0, 0)
        wdgHeader.layout().addWidget(self._charSelector)
        wdgHeader.layout().addWidget(label('Character insight', bold=True), alignment=Qt.AlignmentFlag.AlignBottom)
        self.layout().insertWidget(0, wdgHeader, alignment=Qt.AlignmentFlag.AlignCenter)
        margins(self, top=1)
        shadow(self._textedit, color=QColor('#219ebc'))

        if self.function.character_id:
            character = characters_registry.character(str(self.function.character_id))
            if character:
                self._charSelector.setCharacter(character)

    def _characterSelected(self, character: Character):
        self.function.character_id = character.id


class SceneFunctionsWidget(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._scene: Optional[Scene] = None

        vbox(self)
        margins(self, left=15)
        self.btnPrimary = push_btn(IconRegistry.from_name('mdi6.note-text-outline', 'grey'), 'Primary',
                                   transparent_=True)
        incr_icon(self.btnPrimary, 2)
        incr_font(self.btnPrimary, 2)
        self.btnPrimary.installEventFilter(OpacityEventFilter(self.btnPrimary, leaveOpacity=0.7))
        self.btnPrimaryPlus = tool_btn(IconRegistry.plus_icon('grey'), transparent_=True)
        self.btnPrimaryPlus.installEventFilter(OpacityEventFilter(self.btnPrimaryPlus, leaveOpacity=0.7))
        self.menuPrimary = MenuWidget(self.btnPrimaryPlus)
        self.menuPrimary.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
        self.menuPrimary.addSection('Select a primary function that this scene fulfils')
        self.menuPrimary.addSeparator()
        self.menuPrimary.addAction(action('Advance plot', IconRegistry.storylines_icon(),
                                          slot=partial(self._addPrimary, StoryElementType.Plot),
                                          tooltip="This scene primarily advances the story, often through progression or setback"))
        self.menuPrimary.addAction(
            action('Character insight', IconRegistry.character_icon(),
                   slot=partial(self._addPrimary, StoryElementType.Character),
                   tooltip="This scene primarily provides new information, layer, or development about a character"))
        self.menuPrimary.addAction(action('Mystery', IconRegistry.from_name('ei.question-sign'),
                                          slot=partial(self._addPrimary, StoryElementType.Mystery),
                                          tooltip="This scene primarily introduces or deepens a mystery that drives the narrative forward"))
        apply_white_menu(self.menuPrimary)
        self.btnPrimary.clicked.connect(self.btnPrimaryPlus.click)

        self.btnSecondary = push_btn(IconRegistry.from_name('fa5s.list', 'grey'), 'Secondary',
                                     transparent_=True)
        self.btnSecondary.installEventFilter(OpacityEventFilter(self.btnSecondary, leaveOpacity=0.7))
        incr_icon(self.btnSecondary, 1)
        incr_font(self.btnSecondary, 1)

        self.wdgPrimary = QWidget()
        flow(self.wdgPrimary, spacing=10)
        margins(self.wdgPrimary, left=20, top=0)

        wdgPrimaryHeader = QWidget()
        hbox(wdgPrimaryHeader, 0, 0)
        wdgPrimaryHeader.layout().addWidget(self.btnPrimary)
        wdgPrimaryHeader.layout().addWidget(self.btnPrimaryPlus, alignment=Qt.AlignmentFlag.AlignBottom)
        self.layout().addWidget(wdgPrimaryHeader, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(self.wdgPrimary)
        self.layout().addWidget(self.btnSecondary, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(vspacer())

    def setScene(self, scene: Scene):
        self._scene = scene
        clear_layout(self.wdgPrimary)
        for function in self._scene.functions.primary:
            self.__initPrimaryWidget(function)

    def _addPrimary(self, type_: StoryElementType):
        function = SceneFunction(type_)
        self._scene.functions.primary.append(function)

        wdg = self.__initPrimaryWidget(function)
        qtanim.fade_in(wdg, teardown=lambda: wdg.setGraphicsEffect(None))

    def _removePrimary(self, wdg: PrimarySceneFunctionWidget):
        self._scene.functions.primary.remove(wdg.function)
        fade_out_and_gc(self.wdgPrimary, wdg)

    def __initPrimaryWidget(self, function: SceneFunction):
        if function.type == StoryElementType.Character:
            wdg = CharacterPrimarySceneFunctionWidget(self._novel, self._scene, function)
        elif function.type == StoryElementType.Mystery:
            wdg = MysteryPrimarySceneFunctionWidget(self._novel, self._scene, function)
        else:
            wdg = PlotPrimarySceneFunctionWidget(self._novel, self._scene, function)

        wdg.removed.connect(partial(self._removePrimary, wdg))
        self.wdgPrimary.layout().addWidget(wdg)
        return wdg
