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
from typing import List, Set, Dict, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon
from overrides import overrides
from qthandy import vspacer

from src.main.python.plotlyst.core.domain import NovelDescriptor
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode, ChildNode


class NovelNode(ChildNode):
    def __init__(self, novel: NovelDescriptor, parent=None):
        super(NovelNode, self).__init__(novel.title, parent=parent)
        self._novel = novel
        self.setPlusButtonEnabled(False)
        self._actionChangeIcon.setVisible(True)
        self.refresh()

    def novel(self) -> NovelDescriptor:
        return self._novel

    def refresh(self):
        self._lblTitle.setText(self._novel.title)
        if self._novel.icon:
            self._icon.setIcon(IconRegistry.from_name(self._novel.icon, self._novel.icon_color))
            self._icon.setVisible(True)
        else:
            self._icon.setHidden(True)

    @overrides
    def _iconChanged(self, iconName: str, iconColor: str):
        self._novel.icon = iconName
        self._novel.icon_color = iconColor


class ShelveNode(ContainerNode):
    def __init__(self, title: str, icon: Optional[QIcon] = None, parent=None):
        super(ShelveNode, self).__init__(title, icon, parent)
        self.setMenuEnabled(False)
        self.setPlusButtonEnabled(False)


class ShelvesTreeView(TreeView):
    novelSelected = pyqtSignal(NovelDescriptor)
    novelChanged = pyqtSignal(NovelDescriptor)
    novelsShelveSelected = pyqtSignal()

    def __init__(self, parent=None):
        super(ShelvesTreeView, self).__init__(parent)

        self._selectedNovels: Set[NovelDescriptor] = set()
        self._novels: Dict[NovelDescriptor, NovelNode] = {}

        self._wdgNovels = ShelveNode('Novels', IconRegistry.book_icon())
        self._wdgNovels.selectionChanged.connect(self._novelsShelveSelectionChanged)
        self._wdgShortStories = ShelveNode('Short stories', IconRegistry.from_name('ph.file-text'))
        self._wdgIdeas = ShelveNode('Ideas', IconRegistry.decision_icon())
        self._wdgNotes = ShelveNode('Notes', IconRegistry.document_edition_icon())

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
            node.iconChanged.connect(partial(self.novelChanged.emit, novel))

    def updateNovel(self, novel: NovelDescriptor):
        self._novels[novel].refresh()

    def clearSelection(self):
        for novel in self._selectedNovels:
            self._novels[novel].deselect()
        self._selectedNovels.clear()

    def _novelSelectionChanged(self, novelNode: NovelNode, selected: bool):
        if selected:
            self.clearSelection()
            self._wdgNovels.deselect()
            self._selectedNovels.add(novelNode.novel())
            self.novelSelected.emit(novelNode.novel())

    def _novelsShelveSelectionChanged(self, selected: bool):
        if selected:
            self.clearSelection()
            self.novelsShelveSelected.emit()
