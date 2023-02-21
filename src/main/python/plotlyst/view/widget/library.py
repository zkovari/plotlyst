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
from typing import List, Set, Dict

from PyQt6.QtCore import pyqtSignal
from qthandy import vspacer

from src.main.python.plotlyst.core.domain import NovelDescriptor
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode, ChildNode


class NovelNode(ChildNode):
    def __init__(self, novel: NovelDescriptor, parent=None):
        super(NovelNode, self).__init__(novel.title, parent=parent)
        self._novel = novel

    def novel(self) -> NovelDescriptor:
        return self._novel


class ShelvesTreeView(TreeView):
    novelSelected = pyqtSignal(NovelDescriptor)

    def __init__(self, parent=None):
        super(ShelvesTreeView, self).__init__(parent)

        self._selectedNovels: Set[NovelDescriptor] = set()
        self._novels: Dict[NovelDescriptor, NovelNode] = {}

        self._wdgNovels = ContainerNode('Novels', IconRegistry.book_icon())
        self._wdgNovels.setMenuEnabled(False)
        self._wdgShortStories = ContainerNode('Short stories', IconRegistry.from_name('ph.file-text'))
        self._wdgShortStories.setMenuEnabled(False)
        self._wdgIdeas = ContainerNode('Ideas', IconRegistry.decision_icon())
        self._wdgIdeas.setMenuEnabled(False)
        self._wdgNotes = ContainerNode('Notes', IconRegistry.document_edition_icon())
        self._wdgNotes.setMenuEnabled(False)

        self._wdgShortStories.setDisabled(True)
        self._wdgIdeas.setDisabled(True)
        self._wdgNotes.setDisabled(True)

        self._centralWidget.layout().addWidget(self._wdgNovels)
        self._centralWidget.layout().addWidget(self._wdgShortStories)
        self._centralWidget.layout().addWidget(self._wdgIdeas)
        self._centralWidget.layout().addWidget(self._wdgNotes)
        self._centralWidget.layout().addWidget(vspacer())

    def novels(self) -> List[NovelDescriptor]:
        return list(self._novels.keys())

    def setNovels(self, novels: List[NovelDescriptor]):
        self.clearSelection()
        self._novels.clear()

        self._wdgNovels.clearChildren()
        for novel in novels:
            node = NovelNode(novel)
            self._wdgNovels.addChild(node)
            self._novels[novel] = node
            node.selectionChanged.connect(partial(self._novelSelectionChanged, node))

    def clearSelection(self):
        for novel in self._selectedNovels:
            self._novels[novel].deselect()
        self._selectedNovels.clear()

    def _novelSelectionChanged(self, novelNode: NovelNode, selected: bool):
        if selected:
            self.clearSelection()
            self._selectedNovels.add(novelNode.novel())
            self.novelSelected.emit(novelNode.novel())
