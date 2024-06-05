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
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget
from qthandy import vbox, incr_icon, incr_font, flow, margins, vspacer
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget, ActionTooltipDisplayMode

from plotlyst.core.domain import Scene, Novel, StoryElementType
from plotlyst.view.common import push_btn, tool_btn, action, shadow
from plotlyst.view.icons import IconRegistry
from plotlyst.view.layout import group
from plotlyst.view.widget.input import TextEditBubbleWidget


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
    def __init__(self, novel: Novel, scene: Scene, elementType: StoryElementType, parent=None):
        super().__init__(parent)
        self.novel = novel
        self.scene = scene
        self.elementType = elementType

        if self.elementType == StoryElementType.Plot:
            self._title.setIcon(IconRegistry.storylines_icon())
            self._title.setText('Plot')
            self._textedit.setPlaceholderText("How does the story move forward")
        elif self.elementType == StoryElementType.Character:
            self._title.setIcon(IconRegistry.character_icon())
            self._title.setText('Character insight')
            self._textedit.setPlaceholderText("What do we learn about a character")
        elif self.elementType == StoryElementType.Mystery:
            self._title.setIcon(IconRegistry.from_name('ei.question-sign'))
            self._title.setText('Mystery')
            self._textedit.setPlaceholderText("What mystery is introduced or deepened")

        shadow(self._textedit)


class SceneFunctionsWidget(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._scene: Optional[Scene] = None

        vbox(self)
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
        self.btnPrimary.clicked.connect(self.btnPrimaryPlus.click)

        self.btnSecondary = push_btn(IconRegistry.from_name('fa5s.list', 'grey'), 'Secondary',
                                     transparent_=True)
        self.btnSecondary.installEventFilter(OpacityEventFilter(self.btnSecondary, leaveOpacity=0.7))
        incr_icon(self.btnSecondary, 1)
        incr_font(self.btnSecondary, 1)

        self.wdgPrimary = QWidget()
        flow(self.wdgPrimary)
        margins(self.wdgPrimary, left=20)

        self.layout().addWidget(group(self.btnPrimary, self.btnPrimaryPlus), alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(self.wdgPrimary)
        self.layout().addWidget(self.btnSecondary, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(vspacer())

    def setScene(self, scene: Scene):
        self._scene = scene

    def _addPrimary(self, type_: StoryElementType):
        wdg = PrimarySceneFunctionWidget(self._novel, self._scene, type_)
        self.wdgPrimary.layout().addWidget(wdg)
        qtanim.fade_in(wdg)
