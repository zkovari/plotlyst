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
from PyQt6.QtGui import QColor, QEnterEvent, QIcon
from PyQt6.QtWidgets import QWidget, QAbstractButton
from overrides import overrides
from qthandy import vbox, incr_icon, incr_font, flow, margins, vspacer, hbox, clear_layout, pointy, gc
from qthandy.filter import OpacityEventFilter, ObjectReferenceMimeData
from qtmenu import MenuWidget, ActionTooltipDisplayMode

from plotlyst.common import PLOTLYST_SECONDARY_COLOR, RED_COLOR
from plotlyst.core.domain import Scene, Novel, StoryElementType, Character, SceneFunction, Plot
from plotlyst.service.cache import characters_registry
from plotlyst.view.common import push_btn, tool_btn, action, shadow, label, fade_out_and_gc
from plotlyst.view.icons import IconRegistry
from plotlyst.view.style.base import apply_white_menu
from plotlyst.view.widget.characters import CharacterSelectorButton
from plotlyst.view.widget.display import Icon
from plotlyst.view.widget.input import TextEditBubbleWidget
from plotlyst.view.widget.list import ListView, ListItemWidget
from plotlyst.view.widget.scene.plot import SceneFunctionPlotSelectorMenu


class PrimarySceneFunctionWidget(TextEditBubbleWidget):
    def __init__(self, novel: Novel, scene: Scene, function: SceneFunction, parent=None):
        super().__init__(parent)
        self.novel = novel
        self.scene = scene
        self.function = function
        self._removalEnabled = True

        self._textedit.setMinimumSize(165, 100)
        self._textedit.setMaximumSize(190, 110)
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
        self._menu = MenuWidget(self._title)
        self._menu.addAction(
            action('Edit', IconRegistry.edit_icon(), slot=partial(self.storylineEditRequested.emit, plot)))
        self._menu.addSeparator()
        self._menu.addAction(
            action('Unlink storyline', IconRegistry.from_name('fa5s.unlink', RED_COLOR), slot=self._plotRemoved))

    def _resetPlotStyle(self):
        pass

    def _storylineParent(self) -> QAbstractButton:
        pass

    def _plotSelected(self, plot: Plot):
        self.function.ref = plot.id
        self._setPlotStyle(plot)
        qtanim.glow(self._storylineParent(), color=QColor(plot.icon_color))
        self.storylineSelected.emit(plot)

    def _plotRemoved(self):
        self.function.ref = None
        gc(self._menu)
        self._menu = SceneFunctionPlotSelectorMenu(self.novel, self._title)
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

        shadow(self._textedit)

    @overrides
    def _setPlotStyle(self, plot: Plot):
        super()._setPlotStyle(plot)
        self._title.setIcon(IconRegistry.from_name(plot.icon, plot.icon_color))
        self._title.setText(plot.text)

    @overrides
    def _resetPlotStyle(self):
        self._title.setText('Plot')
        self._title.setIcon(IconRegistry.storylines_icon())

    @overrides
    def _storylineParent(self):
        return self._title


class _AlternativeStorylineAssociatedFunctionWidget(_StorylineAssociatedFunctionWidget):
    def __init__(self, novel: Novel, scene: Scene, function: SceneFunction, parent=None):
        super().__init__(novel, scene, function, parent)

        self._btnStorylineLink = tool_btn(IconRegistry.storylines_icon(color='lightgrey'), transparent_=True,
                                          tooltip='Link storyline to this element',
                                          parent=self)
        self._btnStorylineLink.installEventFilter(OpacityEventFilter(self._btnStorylineLink, leaveOpacity=0.7))
        self._btnStorylineLink.setGeometry(5, 18, 20, 20)
        self._btnStorylineLink.clicked.connect(self._btnStorylineClicked)

        if self.function.ref:
            self._btnStorylineLink.setVisible(True)
            storyline = self._plot()
            if storyline is not None:
                self._setPlotStyle(storyline)
        else:
            self._btnStorylineLink.setVisible(False)

        shadow(self._textedit)

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        if self.function.ref:
            self._btnStorylineLink.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        if not self.function.ref:
            self._btnStorylineLink.setVisible(False)

    @overrides
    def _plotSelected(self, plot: Plot):
        self._btnStorylineLink.setVisible(True)
        super()._plotSelected(plot)

    @overrides
    def _storylineParent(self):
        return self._btnStorylineLink

    def _btnStorylineClicked(self):
        self._menu.exec()


class MysteryPrimarySceneFunctionWidget(_AlternativeStorylineAssociatedFunctionWidget):
    def __init__(self, novel: Novel, scene: Scene, function: SceneFunction, parent=None):
        super().__init__(novel, scene, function, parent)
        self._title.setIcon(IconRegistry.from_name('ei.question-sign', PLOTLYST_SECONDARY_COLOR))
        self._title.setText('Mystery')
        self._textedit.setPlaceholderText("What mystery is introduced or deepened")

    @overrides
    def _setPlotStyle(self, plot: Plot):
        super()._setPlotStyle(plot)
        self._btnStorylineLink.setIcon(IconRegistry.from_name(plot.icon, plot.icon_color))
        self._title.setIcon(IconRegistry.from_name('ei.question-sign', plot.icon_color))

    @overrides
    def _resetPlotStyle(self):
        self._btnStorylineLink.setVisible(False)
        self._btnStorylineLink.setIcon(IconRegistry.storylines_icon(color='lightgrey'))
        self._title.setIcon(IconRegistry.from_name('ei.question-sign', PLOTLYST_SECONDARY_COLOR))


class RevelationPrimarySceneFunctionWidget(_AlternativeStorylineAssociatedFunctionWidget):
    def __init__(self, novel: Novel, scene: Scene, function: SceneFunction, parent=None):
        super().__init__(novel, scene, function, parent)
        self._title.setIcon(IconRegistry.from_name('fa5s.binoculars', PLOTLYST_SECONDARY_COLOR))
        self._title.setText('Revelation')
        self._textedit.setPlaceholderText("What key information is revealed or discovered")

    @overrides
    def _setPlotStyle(self, plot: Plot):
        super()._setPlotStyle(plot)
        self._btnStorylineLink.setIcon(IconRegistry.from_name(plot.icon, plot.icon_color))
        self._title.setIcon(IconRegistry.from_name('fa5s.binoculars', plot.icon_color))

    @overrides
    def _resetPlotStyle(self):
        self._btnStorylineLink.setVisible(False)
        self._btnStorylineLink.setIcon(IconRegistry.storylines_icon(color='lightgrey'))
        self._title.setIcon(IconRegistry.from_name('fa5s.binoculars', PLOTLYST_SECONDARY_COLOR))


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
        shadow(self._textedit)

        if self.function.character_id:
            character = characters_registry.character(str(self.function.character_id))
            if character:
                self._charSelector.setCharacter(character)

    def _characterSelected(self, character: Character):
        self.function.character_id = character.id


class ResonancePrimarySceneFunctionWidget(PrimarySceneFunctionWidget):
    def __init__(self, novel: Novel, scene: Scene, function: SceneFunction, parent=None):
        super().__init__(novel, scene, function, parent)

        self._title.setIcon(IconRegistry.theme_icon())
        self._title.setText('Resonance')
        self._textedit.setPlaceholderText("What emotional or thematic impact does this scene have")


class SecondaryFunctionListItemWidget(ListItemWidget):
    def __init__(self, function: SceneFunction, parent=None):
        super().__init__(function, parent)
        self._function = function
        self._icon = Icon()

        if function.type == StoryElementType.Mystery:
            icon = IconRegistry.from_name('ei.question-sign', PLOTLYST_SECONDARY_COLOR)
            placeholder = "Introduce or deepen a mystery"
        elif function.type == StoryElementType.Setup:
            icon = IconRegistry.setup_scene_icon(color=PLOTLYST_SECONDARY_COLOR)
            placeholder = "Sets up a story element for a later payoff"
        elif function.type == StoryElementType.Information:
            icon = IconRegistry.general_info_icon('lightgrey')
            placeholder = "What new information is conveyed"
        elif function.type == StoryElementType.Resonance:
            icon = IconRegistry.theme_icon()
            placeholder = "What emotional or thematic impact does this scene have"
        elif function.type == StoryElementType.Character:
            icon = IconRegistry.character_icon(color=PLOTLYST_SECONDARY_COLOR)
            placeholder = 'What do we learn about a character'
        else:
            icon = QIcon()
            placeholder = 'Fill out this secondary function'

        tip = f'{function.type.name}: {placeholder}'

        self._icon.setIcon(icon)
        self._icon.setToolTip(tip)
        self._lineEdit.setPlaceholderText(placeholder)
        self._lineEdit.setToolTip(tip)

        self.layout().insertWidget(1, self._icon)
        self._lineEdit.setText(self._function.text)

    @overrides
    def _textChanged(self, text: str):
        super()._textChanged(text)
        self._function.text = text


class SecondaryFunctionsList(ListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene: Optional[Scene] = None
        margins(self, left=20)
        self._btnAdd.setHidden(True)

    def setScene(self, scene: Scene):
        self._scene = scene

        for function in self._scene.functions.secondary:
            self.addItem(function)

    @overrides
    def _addNewItem(self):
        function = SceneFunction(StoryElementType.Mystery)
        self._scene.functions.secondary.append(function)
        self.addItem(function)

    @overrides
    def _listItemWidgetClass(self):
        return SecondaryFunctionListItemWidget

    @overrides
    def _deleteItemWidget(self, widget: ListItemWidget):
        super()._deleteItemWidget(widget)
        self._scene.functions.secondary.remove(widget.item())

    @overrides
    def _dropped(self, mimeData: ObjectReferenceMimeData):
        super()._dropped(mimeData)
        items = []
        for wdg in self.widgets():
            items.append(wdg.item())
        self._scene.functions.secondary[:] = items


class SceneFunctionsWidget(QWidget):
    storylineLinked = pyqtSignal(Plot)
    storylineEditRequested = pyqtSignal(Plot)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._scene: Optional[Scene] = None

        vbox(self)
        margins(self, left=15)
        self.btnPrimary = push_btn(IconRegistry.from_name('mdi6.note-text-outline', 'grey'), 'Primary',
                                   transparent_=True)
        incr_icon(self.btnPrimary, 1)
        incr_font(self.btnPrimary, 1)
        self.btnPrimary.installEventFilter(OpacityEventFilter(self.btnPrimary, leaveOpacity=0.7))
        self.btnPrimaryPlus = tool_btn(IconRegistry.plus_icon('grey'), transparent_=True)
        self.btnPrimaryPlus.installEventFilter(OpacityEventFilter(self.btnPrimaryPlus, leaveOpacity=0.7))
        self.menuPrimary = MenuWidget(self.btnPrimaryPlus)
        self.menuPrimary.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
        self.menuPrimary.addSection('Select a primary function that this scene fulfils')
        self.menuPrimary.addSeparator()
        self.menuPrimary.addAction(action('Advance plot', IconRegistry.storylines_icon(),
                                          slot=partial(self._addPrimary, StoryElementType.Plot),
                                          tooltip="This scene primarily advances or complicates the story by affecting the plot, character arc, or relationships"))
        self.menuPrimary.addAction(
            action('Character insight', IconRegistry.character_icon(),
                   slot=partial(self._addPrimary, StoryElementType.Character),
                   tooltip="This scene primarily provides new information, layers, or development about a character"))
        self.menuPrimary.addAction(action('Mystery', IconRegistry.from_name('ei.question-sign'),
                                          slot=partial(self._addPrimary, StoryElementType.Mystery),
                                          tooltip="This scene primarily introduces or deepens a mystery that drives the narrative forward"))
        self.menuPrimary.addAction(action('Revelation', IconRegistry.from_name('fa5s.binoculars'),
                                          slot=partial(self._addPrimary, StoryElementType.Revelation),
                                          tooltip="This scene primarily reveals a key information"))
        self.menuPrimary.addAction(action('Resonance', IconRegistry.theme_icon('black'),
                                          slot=partial(self._addPrimary, StoryElementType.Resonance),
                                          tooltip="This scene primarily establishes an emotional or thematic impact"))
        apply_white_menu(self.menuPrimary)
        self.btnPrimary.clicked.connect(self.btnPrimaryPlus.click)

        self.btnSecondary = push_btn(IconRegistry.from_name('fa5s.list', 'grey'), 'Secondary',
                                     transparent_=True)
        self.btnSecondary.installEventFilter(OpacityEventFilter(self.btnSecondary, leaveOpacity=0.7))
        incr_icon(self.btnSecondary, 1)
        incr_font(self.btnSecondary, 1)
        self.btnSecondaryPlus = tool_btn(IconRegistry.plus_icon('grey'), transparent_=True)
        self.btnSecondaryPlus.installEventFilter(OpacityEventFilter(self.btnPrimaryPlus, leaveOpacity=0.7))
        self.menuSecondary = MenuWidget(self.btnSecondaryPlus)
        self.menuSecondary.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
        self.menuSecondary.addSection('Select a secondary function that this scene also fulfils')
        self.menuSecondary.addSeparator()
        self.menuSecondary.addAction(
            action('Setup', IconRegistry.setup_scene_icon('black'),
                   slot=partial(self._addSecondary, StoryElementType.Setup),
                   tooltip="Sets up a story element for a later payoff"))
        self.menuSecondary.addAction(
            action('Information', IconRegistry.general_info_icon('black'),
                   slot=partial(self._addSecondary, StoryElementType.Information),
                   tooltip="New information to be conveyed"))
        self.menuSecondary.addAction(
            action('Character insight', IconRegistry.character_icon(),
                   slot=partial(self._addSecondary, StoryElementType.Character),
                   tooltip="New information about a character"))
        self.menuSecondary.addAction(
            action('Mystery', IconRegistry.from_name('ei.question-sign'),
                   slot=partial(self._addSecondary, StoryElementType.Mystery),
                   tooltip="A smaller mystery to be introduced or deepened"))
        self.menuSecondary.addAction(
            action('Resonance', IconRegistry.theme_icon('black'),
                   slot=partial(self._addSecondary, StoryElementType.Resonance),
                   tooltip="Emotional or thematic impact"))

        apply_white_menu(self.menuSecondary)
        self.btnSecondary.clicked.connect(self.btnSecondaryPlus.click)

        self.wdgPrimary = QWidget()
        flow(self.wdgPrimary, spacing=13)
        margins(self.wdgPrimary, left=20, top=0)

        self.listSecondary = SecondaryFunctionsList()

        wdgPrimaryHeader = QWidget()
        hbox(wdgPrimaryHeader, 0, 0)
        wdgPrimaryHeader.layout().addWidget(self.btnPrimary)
        wdgPrimaryHeader.layout().addWidget(self.btnPrimaryPlus, alignment=Qt.AlignmentFlag.AlignBottom)
        self.layout().addWidget(wdgPrimaryHeader, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(self.wdgPrimary)

        wdgSecondaryHeader = QWidget()
        hbox(wdgSecondaryHeader, 0, 0)
        wdgSecondaryHeader.layout().addWidget(self.btnSecondary)
        wdgSecondaryHeader.layout().addWidget(self.btnSecondaryPlus, alignment=Qt.AlignmentFlag.AlignBottom)
        self.layout().addWidget(wdgSecondaryHeader, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(self.listSecondary)
        self.layout().addWidget(vspacer())

    def setScene(self, scene: Scene):
        self._scene = scene
        clear_layout(self.wdgPrimary)
        self.listSecondary.clear()
        for function in self._scene.functions.primary:
            self.__initPrimaryWidget(function)

        self.listSecondary.setScene(self._scene)

    def _addPrimary(self, type_: StoryElementType):
        function = SceneFunction(type_)
        self._scene.functions.primary.append(function)

        wdg = self.__initPrimaryWidget(function)
        qtanim.fade_in(wdg, teardown=lambda: wdg.setGraphicsEffect(None))

    def _addSecondary(self, type_: StoryElementType):
        function = SceneFunction(type_)
        self._scene.functions.secondary.append(function)
        self.listSecondary.addItem(function)

    def _removePrimary(self, wdg: PrimarySceneFunctionWidget):
        self._scene.functions.primary.remove(wdg.function)
        fade_out_and_gc(self.wdgPrimary, wdg)

    def __initPrimaryWidget(self, function: SceneFunction):
        if function.type == StoryElementType.Character:
            wdg = CharacterPrimarySceneFunctionWidget(self._novel, self._scene, function)
        elif function.type == StoryElementType.Mystery:
            wdg = MysteryPrimarySceneFunctionWidget(self._novel, self._scene, function)
        elif function.type == StoryElementType.Revelation:
            wdg = RevelationPrimarySceneFunctionWidget(self._novel, self._scene, function)
        elif function.type == StoryElementType.Resonance:
            wdg = ResonancePrimarySceneFunctionWidget(self._novel, self._scene, function)
        else:
            wdg = PlotPrimarySceneFunctionWidget(self._novel, self._scene, function)

        wdg.removed.connect(partial(self._removePrimary, wdg))
        if isinstance(wdg, _StorylineAssociatedFunctionWidget):
            wdg.storylineSelected.connect(self.storylineLinked)
            wdg.storylineEditRequested.connect(self.storylineEditRequested)
        self.wdgPrimary.layout().addWidget(wdg)
        return wdg
