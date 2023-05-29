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
from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon
from qthandy import vspacer, retain_when_hidden

from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.tour.core import Tutorial
from src.main.python.plotlyst.view.widget.tree import TreeView, TreeSettings, ContainerNode


class TutorialNode(ContainerNode):

    def __init__(self, title: str, icon: Optional[QIcon] = None, tutorial: Tutorial = Tutorial.ContainerIntroduction,
                 parent=None,
                 settings: Optional[TreeSettings] = None):
        super(TutorialNode, self).__init__(title, icon, parent, settings=settings)
        self.setMenuEnabled(False)
        self.setPlusButtonEnabled(False)
        retain_when_hidden(self._icon)
        self._tutorial = tutorial

    def tutorial(self) -> Tutorial:
        return self._tutorial


class TutorialsTreeView(TreeView):
    tutorialSelected = pyqtSignal(Tutorial)

    def __init__(self, parent=None, settings: Optional[TreeSettings] = None):
        super(TutorialsTreeView, self).__init__(parent)
        self._settings = settings
        self._centralWidget.setProperty('bg', True)

        self._selected: Optional[TutorialNode] = None

        self._wdgBasic = self.__initNode('Introduction', Tutorial.ContainerIntroduction, IconRegistry.tutorial_icon())
        self._wdgBasic.addChild(self.__initNode('Create novel', Tutorial.FirstNovel, IconRegistry.book_icon()))
        self._wdgBasic.addChild(
            self.__initNode('Create protagonist', Tutorial.FirstProtagonist, IconRegistry.character_icon()))
        self._wdgBasic.addChild(self.__initNode('Create scenes', Tutorial.FirstScene, IconRegistry.scene_icon()))

        self._centralWidget.layout().addWidget(self._wdgBasic)
        self._centralWidget.layout().addWidget(vspacer())

    def clearSelection(self):
        if self._selected is not None:
            self._selected.deselect()
        self._selected = None

    def _selectionChanged(self, node: TutorialNode, selected: bool):
        self.clearSelection()
        if selected:
            self._selected = node
            self.tutorialSelected.emit(node.tutorial())

    def __initNode(self, title: str, tutorial: Tutorial, icon: Optional[QIcon] = None):
        node = TutorialNode(title, icon, tutorial=tutorial, settings=self._settings)
        node.selectionChanged.connect(partial(self._selectionChanged, node))
        return node
