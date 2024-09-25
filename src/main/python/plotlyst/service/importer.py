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
from abc import abstractmethod
from pathlib import Path
from typing import Dict

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QIcon
from overrides import overrides
from qthandy import busy

from plotlyst.core.domain import Novel, Character, Chapter, Scene
from plotlyst.core.scrivener import ScrivenerParser
from plotlyst.event.core import emit_event
from plotlyst.events import NovelSyncEvent, NovelAboutToSyncEvent, CharacterDeletedEvent, \
    SceneDeletedEvent
from plotlyst.service.persistence import RepositoryPersistenceManager, flush_or_fail, delete_character, \
    delete_scene
from plotlyst.view.icons import IconRegistry


class SyncImporter(QObject):

    def __init__(self):
        super(SyncImporter, self).__init__()
        self._parser = ScrivenerParser()
        self.repo = RepositoryPersistenceManager.instance()

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def icon(self) -> QIcon:
        pass

    def location(self, novel: Novel) -> str:
        if novel.import_origin is None:
            return ''

        return Path(novel.import_origin.source).name

    def location_exists(self, novel: Novel) -> bool:
        path_ = Path(novel.import_origin.source)
        return path_.exists() and path_.is_dir()

    @abstractmethod
    def is_updated(self, novel: Novel) -> bool:
        return False

    def change_location(self, novel: Novel):
        pass

    @abstractmethod
    def sync(self, novel: Novel):
        pass


class ScrivenerSyncImporter(SyncImporter):

    @overrides
    def name(self) -> str:
        return 'Scrivener'

    @overrides
    def icon(self) -> QIcon:
        return IconRegistry.from_name('mdi.alpha-s-circle-outline', color='#410253')

    @overrides
    def location_exists(self, novel: Novel) -> bool:
        exists = super(ScrivenerSyncImporter, self).location_exists(novel)

        if exists:
            scriv_file = self._parser.find_scrivener_file(novel.import_origin.source)
            if not scriv_file:
                print('scriv file not found')
                return False

        return exists

    @overrides
    def is_updated(self, novel: Novel) -> bool:
        return self._mod_time(novel) == novel.import_origin.last_mod_time

    @overrides
    def change_location(self, novel: Novel):
        pass

    @busy
    def sync(self, novel: Novel):
        emit_event(novel, NovelAboutToSyncEvent(self, novel))
        novel.import_origin.last_mod_time = self._mod_time(novel)

        new_novel = self._parser.parse_project(novel.import_origin.source)
        flush_or_fail()

        self._sync_characters(novel, new_novel)
        for scene in novel.scenes:
            scene.chapter = None
        self._sync_chapters(novel, new_novel)
        self._sync_scenes(novel, new_novel)

        self.repo.update_project_novel(novel)
        emit_event(novel, NovelSyncEvent(self, novel))

    def _mod_time(self, novel: Novel) -> int:
        scriv_file = self._parser.find_scrivener_file(novel.import_origin.source)
        return Path(novel.import_origin.source).joinpath(scriv_file).stat().st_mtime_ns

    def _sync_characters(self, novel: Novel, new_novel: Novel):
        current: Dict[Character, Character] = {}
        updates: Dict[Character, bool] = {}
        for character in novel.characters:
            current[character] = character
            updates[character] = False

        for new_character in new_novel.characters:
            if new_character in current.keys():
                old_character = current[new_character]
                old_character.name = new_character.name
                updates[old_character] = True
            else:
                novel.characters.append(new_character)
                self.repo.insert_character(novel, new_character)

        for character, update in updates.items():
            if update:
                self.repo.update_character(character)
            else:
                delete_character(novel, character, forced=True)
                emit_event(novel, CharacterDeletedEvent(self, character))

    def _sync_chapters(self, novel: Novel, new_novel: Novel):
        current: Dict[Chapter, Chapter] = {}
        for chapter in novel.chapters:
            current[chapter] = chapter

        new_chapters = []
        for new_chapter in new_novel.chapters:
            if new_chapter in current.keys():
                new_chapters.append(current[new_chapter])
            else:
                new_chapters.append(new_chapter)

        novel.chapters[:] = new_chapters
        self.repo.update_novel(novel)

    def _sync_scenes(self, novel: Novel, new_novel: Novel):
        current: Dict[Scene, Scene] = {}
        chapters: Dict[Chapter, Chapter] = {}
        for chapter in novel.chapters:
            chapters[chapter] = chapter
        for scene in novel.scenes:
            current[scene] = scene

        new_scenes = []
        for new_scene in new_novel.scenes:
            if new_scene in current.keys():
                old_scene = current[new_scene]
                old_scene.title = new_scene.title
                if old_scene.manuscript and new_scene.manuscript:
                    old_scene.manuscript.content = new_scene.manuscript.content
                    old_scene.manuscript.loaded = True
                elif old_scene.manuscript and new_scene.manuscript is None:
                    old_scene.manuscript.content = ''
                elif old_scene.manuscript is None and new_scene.manuscript:
                    old_scene.manuscript = new_scene.manuscript

                if new_scene.chapter:
                    old_scene.chapter = chapters[new_scene.chapter]
                new_scenes.append(old_scene)

                self.repo.update_scene(old_scene)
                if old_scene.manuscript:
                    self.repo.update_doc(novel, old_scene.manuscript)
            else:
                new_scenes.append(new_scene)
                self.repo.insert_scene(novel, new_scene)
                if new_scene.manuscript:
                    self.repo.update_doc(novel, new_scene.manuscript)

        removed_scenes = [k for k in current.keys() if k not in new_novel.scenes]

        for scene in removed_scenes:
            delete_scene(novel, scene, forced=True)
            emit_event(novel, SceneDeletedEvent(self, scene))

        novel.scenes[:] = new_scenes
