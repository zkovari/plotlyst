"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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
from typing import Any, Dict, List

from PyQt5.QtCore import QModelIndex, Qt, QVariant, QMimeData, QByteArray, pyqtSignal
from anytree import Node
from overrides import overrides

from plotlyst.core.client import client
from plotlyst.core.domain import Novel, Chapter, Scene
from plotlyst.model.tree_model import TreeItemModel


class ChapterNode(Node):
    def __init__(self, chapter: Chapter, parent):
        super().__init__(chapter.title, parent)
        self.chapter = chapter


class SceneNode(Node):
    def __init__(self, scene: Scene, parent):
        super(SceneNode, self).__init__(scene.title, parent)
        self.scene = scene


class SceneMimeData(QMimeData):
    def __init__(self, node: SceneNode):
        self.node = node
        super(SceneMimeData, self).__init__()


class ChaptersTreeModel(TreeItemModel):
    MimeType: str = 'application/scene'
    orderChanged = pyqtSignal()

    def __init__(self, novel: Novel, parent=None):
        super(ChaptersTreeModel, self).__init__(parent)
        self.novel = novel

        self.update()

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if index.column() > 0:
            return QVariant()
        if role == Qt.DecorationRole:
            node: Node = index.internalPointer()
            # if isinstance(node, SceneNode):
            #     return IconRegistry.scene_icon()
        return super().data(index, role)

    def update(self):
        del self.root.children
        chapters: Dict[str, ChapterNode] = {}
        for chapter in self.novel.chapters:
            chapters[chapter.title] = ChapterNode(chapter, self.root)
        for scene in self.novel.scenes:
            if scene.chapter:
                SceneNode(scene, chapters[scene.chapter.title])

        dummy_parent = None
        for scene in self.novel.scenes:
            if not scene.chapter:
                if not dummy_parent:
                    if self.root.children:
                        dummy_parent = Node('---', self.root)
                    else:
                        dummy_parent = self.root
                SceneNode(scene, dummy_parent)

    def newChapter(self) -> Chapter:
        index = len(self.novel.chapters)
        chapter = Chapter(title=str(index + 1), sequence=index)
        self.novel.chapters.append(chapter)

        self.update()
        self.modelReset.emit()

        return chapter

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        node = index.internalPointer()
        if isinstance(node, SceneNode):
            return flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        return flags | Qt.ItemIsDropEnabled

    @overrides
    def mimeData(self, indexes: List[QModelIndex]) -> QMimeData:
        node = indexes[0].internalPointer()
        mime_data = SceneMimeData(node)
        mime_data.setData(self.MimeType, QByteArray(pickle.dumps(node.scene)))
        return mime_data

    @overrides
    def mimeTypes(self) -> List[str]:
        return [self.MimeType]

    @overrides
    def canDropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int,
                        parent: QModelIndex) -> bool:
        if row >= 0:
            return False
        if not data.hasFormat(self.MimeType):
            return False
        if not isinstance(data, SceneMimeData):
            return False
        if not isinstance(parent.internalPointer(), ChapterNode):
            return False

        return True

    @overrides
    def dropMimeData(self, data: SceneMimeData, action: Qt.DropAction, row: int, column: int,
                     parent: QModelIndex) -> bool:
        parent_node = parent.internalPointer()

        node: SceneNode = data.node
        old_parent = node.parent
        old_parent.children = [x for x in old_parent.children if x is not node]
        node.parent = parent_node
        parent_node.children = sorted(parent_node.children, key=lambda x: x.scene.sequence)
        node.scene.chapter = parent_node.chapter
        self.modelReset.emit()

        old_index = self.novel.scenes.index(node.scene)
        new_index = [x for x in self.root.leaves if isinstance(x, SceneNode)].index(node)
        if old_index != new_index:
            self.novel.scenes.insert(new_index, self.novel.scenes.pop(old_index))
            self.orderChanged.emit()
        client.update_scene_chapter(node.scene)

        return True
