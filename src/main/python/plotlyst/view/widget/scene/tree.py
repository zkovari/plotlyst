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
from typing import Dict, Optional, Set, Union
from typing import List

from PyQt6.QtCore import QMimeData, QPointF
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QMenu
from overrides import overrides
from qthandy import gc, retain_when_hidden, translucent, clear_layout, vbox, margins
from qthandy import vspacer
from qthandy.filter import DragEventFilter, DropEventFilter

from src.main.python.plotlyst.core.domain import Scene, Novel, SceneType, \
    Chapter
from src.main.python.plotlyst.event.core import emit_event, Event, EventListener
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import SceneDeletedEvent, \
    SceneChangedEvent
from src.main.python.plotlyst.events import SceneOrderChangedEvent, ChapterChangedEvent
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager, delete_scene
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.widget.display import Icon
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode


class SceneWidget(ContainerNode):

    def __init__(self, scene: Scene, novel: Novel, parent=None):
        super(SceneWidget, self).__init__(scene.title_or_index(novel), parent=parent)
        self._scene = scene
        self._novel = novel

        self._scenePovIcon = Icon(self)
        retain_when_hidden(self._scenePovIcon)
        self.setPlusButtonEnabled(False)

        self._wdgTitle.layout().insertWidget(0, self._scenePovIcon)

        self.refresh()

    def scene(self) -> Scene:
        return self._scene

    def novel(self) -> Novel:
        return self._novel

    def refresh(self):
        if self._scene.type != SceneType.DEFAULT:
            self._icon.setIcon(IconRegistry.scene_type_icon(self._scene))
        self._icon.setVisible(self._scene.type != SceneType.DEFAULT)

        if self._scene.pov:
            avatar = avatars.avatar(self._scene.pov, fallback=False)
            if avatar:
                self._scenePovIcon.setIcon(avatar)
        else:
            avatar = None
        self._scenePovIcon.setVisible(avatar is not None)

        self.refreshTitle()

    def refreshTitle(self):
        self._lblTitle.setText(self._scene.title_or_index(self._novel))


class ChapterWidget(ContainerNode):
    deleted = pyqtSignal()
    addScene = pyqtSignal()

    def __init__(self, chapter: Chapter, novel: Novel, parent=None):
        super(ChapterWidget, self).__init__(chapter.title_index(novel), IconRegistry.chapter_icon(), parent)
        self._chapter = chapter
        self._novel = novel
        margins(self._wdgTitle, top=2, bottom=2)

        menu = QMenu()
        menu.addAction(IconRegistry.scene_icon(), 'Add scene', self.addScene.emit)
        self.setPlusMenu(menu)

        self._reStyle()

    def refresh(self):
        self._lblTitle.setText(self._chapter.title_index(self._novel))

    def chapter(self) -> Chapter:
        return self._chapter

    def novel(self) -> Novel:
        return self._novel

    def sceneWidgets(self) -> List[SceneWidget]:
        return self.childrenWidgets()


class ScenesTreeView(TreeView, EventListener):
    SCENE_MIME_TYPE = 'application/tree-scene-widget'
    CHAPTER_MIME_TYPE = 'application/tree-chapter-widget'
    sceneSelected = pyqtSignal(Scene)
    chapterSelected = pyqtSignal(Chapter)

    # noinspection PyTypeChecker
    def __init__(self, parent=None):
        super(ScenesTreeView, self).__init__(parent)
        self._novel: Optional[Novel] = None

        self._chapters: Dict[Chapter, ChapterWidget] = {}
        self._scenes: Dict[Scene, SceneWidget] = {}
        self._selectedScenes: Set[Scene] = set()
        self._selectedChapters: Set[Chapter] = set()
        self.setStyleSheet('ScenesTreeView {background-color: rgb(244, 244, 244);}')

        self._dummyWdg: Optional[Union[SceneWidget, ChapterWidget]] = None
        self._toBeRemoved: Optional[Union[SceneWidget, ChapterWidget]] = None
        self._spacer: QWidget = vspacer()
        vbox(self._spacer)
        self._spacer.setAcceptDrops(True)
        self._spacer.installEventFilter(
            DropEventFilter(self, [self.SCENE_MIME_TYPE, self.CHAPTER_MIME_TYPE], enteredSlot=self._dragEnteredForEnd,
                            leftSlot=self._dragLeftFromEnd, droppedSlot=self._drop))

        self._centralWidget.setAcceptDrops(True)
        self._centralWidget.installEventFilter(DropEventFilter(self, [self.SCENE_MIME_TYPE, self.CHAPTER_MIME_TYPE],
                                                               leftSlot=lambda: self._dummyWdg.setHidden(True)))

        event_dispatcher.register(self, SceneOrderChangedEvent)
        event_dispatcher.register(self, SceneDeletedEvent)
        event_dispatcher.register(self, SceneChangedEvent)
        self.repo = RepositoryPersistenceManager.instance()

    def setNovel(self, novel: Novel):
        self._novel = novel
        self.refresh()

    def selectedScenes(self) -> List[Scene]:
        return list(self._selectedScenes)

    def selectedChapters(self) -> List[Chapter]:
        return list(self._selectedChapters)

    def refresh(self):
        self.clearSelection()
        clear_layout(self, auto_delete=False)

        for scene in self._novel.scenes:
            if scene not in self._scenes.keys():
                self.__initSceneWidget(scene)

            sceneWdg = self._scenes[scene]
            if scene.chapter:
                if scene.chapter not in self._chapters.keys():
                    chapter_wdg = self.__initChapterWidget(scene.chapter)
                    self._centralWidget.layout().addWidget(chapter_wdg)
                self._chapters[scene.chapter].addChild(sceneWdg)
            else:
                self._centralWidget.layout().addWidget(sceneWdg)

        chapter_index = 0
        for i, chapter in enumerate(self._novel.chapters):
            if chapter not in self._chapters.keys():
                chapter_wdg = self.__initChapterWidget(chapter)
                if i > 0:
                    prev_chapter_wdg = self._chapters[self._novel.chapters[i - 1]]
                    chapter_index = self._centralWidget.layout().indexOf(prev_chapter_wdg)
                    chapter_index += 1
                self._centralWidget.layout().insertWidget(chapter_index, chapter_wdg)

        self._centralWidget.layout().addWidget(self._spacer)

    def addChapter(self):
        if self._novel.chapters:
            last_chapter = self._novel.chapters[-1]
            i = self._centralWidget.layout().indexOf(self._chapters[last_chapter]) + 1
        else:
            i = 0
        chapter = Chapter('')
        self._novel.chapters.append(chapter)
        wdg = self.__initChapterWidget(chapter)
        self._centralWidget.layout().insertWidget(i, wdg)

        self.repo.update_novel(self._novel)

    def selectChapter(self, chapter: Chapter):
        self.clearSelection()
        self._chapters[chapter].select()
        if chapter not in self._selectedChapters:
            self._selectedChapters.add(chapter)

    def selectScene(self, scene: Scene):
        self.clearSelection()
        self._scenes[scene].select()
        if scene not in self._selectedScenes:
            self._selectedScenes.add(scene)

    def clearSelection(self):
        for scene in self._selectedScenes:
            self._scenes[scene].deselect()
        for chapter in self._selectedChapters:
            self._chapters[chapter].deselect()
        self._selectedScenes.clear()
        self._selectedChapters.clear()

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, SceneDeletedEvent):
            if event.scene in self._selectedScenes:
                self._selectedScenes.remove(event.scene)
            if event.scene in self._scenes.keys():
                wdg = self._scenes.pop(event.scene)
                wdg.parent().layout().removeWidget(wdg)
                gc(wdg)
        elif isinstance(event, SceneChangedEvent):
            wdg = self._scenes.get(event.scene)
            if wdg is not None:
                wdg.refresh()
        elif isinstance(event, SceneOrderChangedEvent):
            self.refresh()

    def _addScene(self, chapterWdg: ChapterWidget):
        scene = self._novel.new_scene()
        scene.chapter = chapterWdg.chapter()
        self._novel.scenes.append(scene)
        self.repo.insert_scene(self._novel, scene)
        sceneWdg = self.__initSceneWidget(scene)
        chapterWdg.addChild(sceneWdg)

        self._reorderScenes()

    def _sceneSelectionChanged(self, sceneWdg: SceneWidget, selected: bool):
        if selected:
            self.clearSelection()
            self._selectedScenes.add(sceneWdg.scene())
            self.sceneSelected.emit(sceneWdg.scene())
        elif sceneWdg.scene() in self._selectedScenes:
            self._selectedScenes.remove(sceneWdg.scene())

    def _chapterSelectionChanged(self, chapterWdg: ChapterWidget, selected: bool):
        if selected:
            self.clearSelection()
            self._selectedChapters.add(chapterWdg.chapter())
            self.chapterSelected.emit(chapterWdg.chapter())
        elif chapterWdg.chapter() in self._selectedChapters:
            self._selectedChapters.remove(chapterWdg.chapter())

    def _deleteChapter(self, chapterWdg: ChapterWidget):
        chapter = chapterWdg.chapter()
        if chapter in self._selectedChapters:
            self._selectedChapters.remove(chapter)
        self._chapters.pop(chapter)

        i = self._centralWidget.layout().indexOf(chapterWdg)
        for wdg in chapterWdg.sceneWidgets():
            chapterWdg.containerWidget().layout().removeWidget(wdg)
            wdg.setParent(self._centralWidget)
            self._centralWidget.layout().insertWidget(i, wdg)
            i += 1

            wdg.scene().chapter = None
            self.repo.update_scene(wdg.scene())

        chapterWdg.setHidden(True)
        gc(chapterWdg)

        self._novel.chapters.remove(chapter)
        self.repo.update_novel(self._novel)

        for wdg in self._chapters.values():
            wdg.refresh()

        emit_event(ChapterChangedEvent(self))

    def _deleteScene(self, sceneWdg: SceneWidget):
        scene = sceneWdg.scene()
        if delete_scene(self._novel, scene):
            if scene in self._selectedScenes:
                self._selectedScenes.remove(scene)
            self._scenes.pop(scene)

            sceneWdg.setHidden(True)
            gc(sceneWdg)

            emit_event(SceneDeletedEvent(self, scene))

    def _dragStarted(self, wdg: QWidget):
        wdg.setHidden(True)
        if isinstance(wdg, SceneWidget):
            self._dummyWdg = SceneWidget(wdg.scene(), wdg.novel())
        elif isinstance(wdg, ChapterWidget):
            self._dummyWdg = ChapterWidget(wdg.chapter(), wdg.novel())
            for v in self._scenes.values():
                v.setDisabled(True)
        else:
            return

        translucent(self._dummyWdg)
        self._dummyWdg.setHidden(True)
        self._dummyWdg.setParent(self._centralWidget)
        self._dummyWdg.setAcceptDrops(True)
        self._dummyWdg.installEventFilter(
            DropEventFilter(self._dummyWdg, [self.SCENE_MIME_TYPE, self.CHAPTER_MIME_TYPE], droppedSlot=self._drop))

    def _dragStopped(self, wdg: QWidget):
        if self._dummyWdg:
            gc(self._dummyWdg)
            self._dummyWdg = None

        if self._toBeRemoved:
            gc(self._toBeRemoved)
            self._toBeRemoved = None

            self._reorderScenes()
        else:
            wdg.setVisible(True)

        for v in self._scenes.values():
            v.setEnabled(True)

    def _dragEnteredForEnd(self, _: QMimeData):
        self._spacer.layout().addWidget(self._dummyWdg, alignment=Qt.AlignmentFlag.AlignTop)
        self._dummyWdg.setVisible(True)

    def _dragLeftFromEnd(self):
        self._dummyWdg.setHidden(True)
        self._spacer.layout().removeWidget(self._dummyWdg)
        self._dummyWdg.setParent(self._centralWidget)

    def _dragMovedOnChapter(self, chapterWdg: ChapterWidget, edge: Qt.Edge, _: QPointF):
        i = self._centralWidget.layout().indexOf(chapterWdg)
        if edge == Qt.Edge.TopEdge:
            self._centralWidget.layout().insertWidget(i, self._dummyWdg)
        else:
            chapterWdg.insertChild(0, self._dummyWdg)
        self._dummyWdg.setVisible(True)

    def _drop(self, mimeData: QMimeData):
        self.clearSelection()

        ref = mimeData.reference()
        if self._dummyWdg.isHidden():
            return
        if isinstance(ref, Scene):
            sceneWdg = self._scenes[ref]
            self._toBeRemoved = sceneWdg
            new_widget = self.__initSceneWidget(ref)
            if self._dummyWdg.parent() is self._centralWidget:
                ref.chapter = None
                new_widget.setParent(self._centralWidget)
                i = self._centralWidget.layout().indexOf(self._dummyWdg)
                self._centralWidget.layout().insertWidget(i, new_widget)
            elif self._dummyWdg.parent() is self._spacer:
                ref.chapter = None
                new_widget.setParent(self._centralWidget)
                self._centralWidget.layout().insertWidget(self._centralWidget.layout().count() - 1, new_widget)
            elif isinstance(self._dummyWdg.parent().parent(), ChapterWidget):
                chapter_wdg: ChapterWidget = self._dummyWdg.parent().parent()
                ref.chapter = chapter_wdg.chapter()
                new_widget.setParent(chapter_wdg)
                i = chapter_wdg.containerWidget().layout().indexOf(self._dummyWdg)
                chapter_wdg.insertChild(i, new_widget)
            self.repo.update_scene(ref)
        elif isinstance(ref, Chapter):
            chapter_wdg = self._chapters[ref]
            self._toBeRemoved = chapter_wdg
            new_widget = self.__initChapterWidget(ref)

            for wdg in chapter_wdg.sceneWidgets():
                new_widget.addChild(self.__initSceneWidget(wdg.scene()))

            new_widget.setParent(self._centralWidget)
            i = self._centralWidget.layout().indexOf(self._dummyWdg)
            self._centralWidget.layout().insertWidget(i, new_widget)
            # novel is saved later caught in dragStopped -> reorderScenes

        self._dummyWdg.setHidden(True)

    def _reorderScenes(self):
        chapters = []
        scenes = []

        for i in range(self._centralWidget.layout().count()):
            item = self._centralWidget.layout().itemAt(i)
            if item is None:
                continue
            wdg = item.widget()
            if isinstance(wdg, ChapterWidget):
                chapters.append(wdg.chapter())
                for scene_wdg in wdg.sceneWidgets():
                    scenes.append(scene_wdg.scene())
            elif isinstance(wdg, SceneWidget):
                scenes.append(wdg.scene())

        self._novel.chapters[:] = chapters
        self._novel.scenes[:] = scenes

        for wdg in self._chapters.values():
            wdg.refresh()
        for wdg in self._scenes.values():
            wdg.refreshTitle()

        emit_event(SceneOrderChangedEvent(self))
        self.repo.update_novel(self._novel)

    def _dragMovedOnScene(self, sceneWdg: SceneWidget, edge: Qt.Edge, _: QPointF):
        i = sceneWdg.parent().layout().indexOf(sceneWdg)
        if edge == Qt.Edge.TopEdge:
            sceneWdg.parent().layout().insertWidget(i, self._dummyWdg)
        else:
            sceneWdg.parent().layout().insertWidget(i + 1, self._dummyWdg)
        self._dummyWdg.setVisible(True)

    # noinspection PyTypeChecker
    def __initChapterWidget(self, chapter):
        chapterWdg = ChapterWidget(chapter, self._novel)
        chapterWdg.selectionChanged.connect(partial(self._chapterSelectionChanged, chapterWdg))
        chapterWdg.deleted.connect(partial(self._deleteChapter, chapterWdg))
        chapterWdg.addScene.connect(partial(self._addScene, chapterWdg))
        chapterWdg.installEventFilter(
            DragEventFilter(chapterWdg, self.CHAPTER_MIME_TYPE, dataFunc=lambda wdg: wdg.chapter(),
                            grabbed=chapterWdg.titleWidget(),
                            startedSlot=partial(self._dragStarted, chapterWdg),
                            finishedSlot=partial(self._dragStopped, chapterWdg)))
        chapterWdg.titleWidget().setAcceptDrops(True)
        chapterWdg.titleWidget().installEventFilter(
            DropEventFilter(chapterWdg, [self.SCENE_MIME_TYPE, self.CHAPTER_MIME_TYPE],
                            motionDetection=Qt.Orientation.Vertical,
                            motionSlot=partial(self._dragMovedOnChapter, chapterWdg),
                            droppedSlot=self._drop
                            )
        )
        self._chapters[chapter] = chapterWdg

        return chapterWdg

    # noinspection PyTypeChecker
    def __initSceneWidget(self, scene: Scene) -> SceneWidget:
        sceneWdg = SceneWidget(scene, self._novel)
        self._scenes[scene] = sceneWdg
        sceneWdg.selectionChanged.connect(partial(self._sceneSelectionChanged, sceneWdg))
        sceneWdg.deleted.connect(partial(self._deleteScene, sceneWdg))
        sceneWdg.installEventFilter(
            DragEventFilter(sceneWdg, self.SCENE_MIME_TYPE, dataFunc=lambda wdg: wdg.scene(),
                            startedSlot=partial(self._dragStarted, sceneWdg),
                            finishedSlot=partial(self._dragStopped, sceneWdg)))
        sceneWdg.setAcceptDrops(True)
        sceneWdg.installEventFilter(
            DropEventFilter(sceneWdg, [self.SCENE_MIME_TYPE],
                            motionDetection=Qt.Orientation.Vertical,
                            motionSlot=partial(self._dragMovedOnScene, sceneWdg),
                            droppedSlot=self._drop
                            )

        )
        return sceneWdg
