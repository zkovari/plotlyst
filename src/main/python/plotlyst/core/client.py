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
import os
import pathlib
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any, Dict

from PyQt5.QtCore import QByteArray, QBuffer, QIODevice
from PyQt5.QtGui import QImage, QImageReader
from atomicwrites import atomic_write
from dataclasses_json import dataclass_json, Undefined

from src.main.python.plotlyst.core.domain import Novel, Character, Scene, StoryLine, Chapter, CharacterArc, \
    SceneBuilderElement, SceneBuilderElementType, NpcCharacter, SceneStage, default_stages
from src.main.python.plotlyst.settings import STORY_LINE_COLOR_CODES


class ApplicationDbVersion(Enum):
    R0 = 0  # before ApplicationModel existed
    R1 = 1
    R2 = 2
    R3 = 3
    R4 = 4  # add SceneBuilderElementModel


LATEST = ApplicationDbVersion.R4


class SqlClient:

    def novels(self) -> List[Novel]:
        return json_client.novels()

    def has_novel(self, id: uuid.UUID) -> bool:
        return json_client.has_novel(id)

    def insert_novel(self, novel: Novel):
        json_client.insert_novel(novel)

    def delete_novel(self, novel: Novel):
        json_client.delete_novel(novel)

    def update_novel(self, novel: Novel):
        json_client.update_novel(novel)

    def fetch_novel(self, id: uuid.UUID) -> Novel:
        return json_client.fetch_novel(id)

    def insert_character(self, novel: Novel, character: Character):
        json_client.insert_character(novel, character)

    def update_character(self, character: Character):
        json_client.update_character(character)

    def delete_character(self, novel: Novel, character: Character):
        json_client.delete_character(novel, character)

    def update_scene(self, scene: Scene):
        json_client.update_scene(scene)

    def insert_scene(self, novel: Novel, scene: Scene):
        json_client.insert_scene(novel, scene)

    def delete_scene(self, novel: Novel, scene: Scene):
        json_client.delete_scene(novel, scene)


client = SqlClient()


@dataclass_json
@dataclass
class CharacterInfo:
    name: str
    id: uuid.UUID
    avatar_id: Optional[uuid.UUID] = None


@dataclass
class CharacterArcInfo:
    arc: int
    character: uuid.UUID


@dataclass
class SceneBuilderElementInfo:
    type: SceneBuilderElementType
    text: str = ''
    children: List['SceneBuilderElementInfo'] = field(default_factory=list)
    character: Optional[uuid.UUID] = None
    has_suspense: bool = False
    has_tension: bool = False
    has_stakes: bool = False


@dataclass_json
@dataclass
class SceneInfo:
    title: str
    id: uuid.UUID
    synopsis: str = ''
    type: str = ''
    pivotal: str = ''
    beginning: str = ''
    middle: str = ''
    end: str = ''
    pov: Optional[uuid.UUID] = None
    characters: List[uuid.UUID] = field(default_factory=list)
    wip: bool = False
    storylines: List[uuid.UUID] = field(default_factory=list)
    day: int = 1
    notes: str = ''
    chapter: Optional[uuid.UUID] = None
    arcs: List[CharacterArcInfo] = field(default_factory=list)
    action_resolution: bool = False
    without_action_conflict: bool = False
    scene_builder_elements: List[SceneBuilderElementInfo] = field(default_factory=list)
    stage: Optional[uuid.UUID] = None


@dataclass
class StorylineInfo:
    text: str
    id: uuid.UUID
    color_hexa: str = ''


@dataclass
class ChapterInfo:
    title: str
    id: uuid.UUID


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class NovelInfo:
    title: str
    id: uuid.UUID
    scenes: List[uuid.UUID] = field(default_factory=list)
    characters: List[uuid.UUID] = field(default_factory=list)
    storylines: List[StorylineInfo] = field(default_factory=list)
    chapters: List[ChapterInfo] = field(default_factory=list)
    stages: List[SceneStage] = field(default_factory=default_stages)


@dataclass
class ProjectNovelInfo:
    title: str
    id: uuid.UUID


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Project:
    novels: List[ProjectNovelInfo] = field(default_factory=list)


class JsonClient:

    def __init__(self):
        self.project: Optional[Project] = None
        self._workspace = ''
        self.project_file_path = ''
        self.root_path: Optional[pathlib.Path] = None
        self.novels_dir: Optional[pathlib.Path] = None
        self.scenes_dir: Optional[pathlib.Path] = None
        self.characters_dir: Optional[pathlib.Path] = None
        self.images_dir: Optional[pathlib.Path] = None

    def init(self, workspace: str):
        self.project_file_path = os.path.join(workspace, 'project.plotlyst')

        if not os.path.exists(self.project_file_path) or os.path.getsize(self.project_file_path) == 0:
            self.project = Project()
            self._persist_project()
        else:
            with open(self.project_file_path) as json_file:
                data = json_file.read()
                self.project = Project.from_json(data)

        self._workspace = workspace
        self.root_path = pathlib.Path(self._workspace)
        self.novels_dir = self.root_path.joinpath('novels')
        self.scenes_dir = self.root_path.joinpath('scenes')
        self.characters_dir = self.root_path.joinpath('characters')
        self.images_dir = self.root_path.joinpath('images')

        if not os.path.exists(str(self.novels_dir)):
            os.mkdir(self.novels_dir)
        if not os.path.exists(str(self.scenes_dir)):
            os.mkdir(self.scenes_dir)
        if not os.path.exists(str(self.characters_dir)):
            os.mkdir(self.characters_dir)
        if not os.path.exists(str(self.images_dir)):
            os.mkdir(self.images_dir)

    def novels(self) -> List[Novel]:
        return [Novel(title=x.title, id=x.id) for x in self.project.novels]

    def has_novel(self, id: uuid.UUID):
        for novel in self.project.novels:
            if novel.id == id:
                return True
        return False

    def insert_novel(self, novel: Novel):
        project_novel_info = ProjectNovelInfo(title=novel.title, id=novel.id)
        self.project.novels.append(project_novel_info)
        self._persist_project()
        self._persist_novel(novel)

    def delete_novel(self, novel: Novel):
        novel_info = self._find_project_novel_info_or_fail(novel.id)
        self.project.novels.remove(novel_info)
        self._persist_project()
        self.__delete_info(self.novels_dir, novel_info.id)

    def update_novel(self, novel: Novel):
        novel_info = self._find_project_novel_info_or_fail(novel.id)
        if novel_info.title != novel.title:
            novel_info.title = novel.title
            self._persist_project()
        self._persist_novel(novel)

    def insert_scene(self, novel: Novel, scene: Scene):
        self._persist_scene(scene)
        self._persist_novel(novel)

    def update_scene(self, scene: Scene):
        self._persist_scene(scene)

    def delete_scene(self, novel: Novel, scene: Scene):
        self._persist_novel(novel)
        self.__delete_info(self.scenes_dir, scene.id)

    def insert_character(self, novel: Novel, character: Character):
        self._persist_character(character)
        self._persist_novel(novel)

    def update_character(self, character: Character):
        self._persist_character(character)

    def delete_character(self, novel: Novel, character: Character):
        self._persist_novel(novel)
        self.__delete_info(self.characters_dir, character.id)

    def _find_project_novel_info_or_fail(self, id: uuid.UUID) -> ProjectNovelInfo:
        for info in self.project.novels:
            if info.id == id:
                return info
        raise ValueError(f'Could not find novel with id {id}')

    def fetch_novel(self, id: uuid.UUID) -> Novel:
        project_novel_info = self._find_project_novel_info_or_fail(id)
        novel_info = self._read_novel_info(project_novel_info.id)

        storylines = []
        storylines_ids = {}
        for i, sl_info in enumerate(novel_info.storylines):
            color = sl_info.color_hexa if sl_info.color_hexa else STORY_LINE_COLOR_CODES[
                i % len(STORY_LINE_COLOR_CODES)]
            sl = StoryLine(text=sl_info.text, id=sl_info.id, color_hexa=color)
            storylines.append(sl)
            storylines_ids[str(sl_info.id)] = sl
        chapters = []
        chapters_ids = {}
        for seq, chapter_info in enumerate(novel_info.chapters):
            chapter = Chapter(title=chapter_info.title, sequence=seq, id=chapter_info.id)
            chapters.append(chapter)
            chapters_ids[str(chapter.id)] = chapter

        characters = []
        for char_id in novel_info.characters:
            path = self.characters_dir.joinpath(self.__json_file(char_id))
            if not os.path.exists(path):
                continue
            with open(path) as json_file:
                data = json_file.read()
                info: CharacterInfo = CharacterInfo.from_json(data)
                character = Character(name=info.name, id=info.id)
                if info.avatar_id:
                    bytes = self._load_image(self.__image_file(info.avatar_id))
                    if bytes:
                        character.avatar = bytes
                characters.append(character)
        characters_ids = {}
        for char in characters:
            characters_ids[str(char.id)] = char

        scenes: List[Scene] = []
        for seq, scene_id in enumerate(novel_info.scenes):
            path = self.scenes_dir.joinpath(self.__json_file(scene_id))
            if not os.path.exists(path):
                continue
            with open(path) as json_file:
                data = json_file.read()
                info: SceneInfo = SceneInfo.from_json(data)
                scene_storylines = []
                for sl_id in info.storylines:
                    if str(sl_id) in storylines_ids.keys():
                        scene_storylines.append(storylines_ids[str(sl_id)])
                if info.pov and str(info.pov) in characters_ids.keys():
                    pov = characters_ids[str(info.pov)]
                else:
                    pov = None

                scene_characters = []
                for char_id in info.characters:
                    if str(char_id) in characters_ids.keys():
                        scene_characters.append(characters_ids[str(char_id)])

                if info.chapter and str(info.chapter) in chapters_ids.keys():
                    chapter = chapters_ids[str(info.chapter)]
                else:
                    chapter = None

                builder_elements: List[SceneBuilderElement] = []
                for builder_info in info.scene_builder_elements:
                    builder_elements.append(self.__get_scene_builder_element(builder_info, characters_ids))

                stage = None
                if info.stage:
                    match = [x for x in novel_info.stages if x.id == info.stage]
                    if match:
                        stage = match[0]

                arcs = []
                for arc in info.arcs:
                    if str(arc.character) in characters_ids.keys():
                        arcs.append(CharacterArc(arc=arc.arc, character=characters_ids[str(arc.character)]))
                scene = Scene(title=info.title, id=info.id, synopsis=info.synopsis, type=info.type,
                              beginning=info.beginning,
                              middle=info.middle, end=info.end, wip=info.wip, pivotal=info.pivotal, day=info.day,
                              notes=info.notes,
                              action_resolution=info.action_resolution,
                              without_action_conflict=info.without_action_conflict, sequence=seq,
                              story_lines=scene_storylines, pov=pov, characters=scene_characters, arcs=arcs,
                              chapter=chapter, builder_elements=builder_elements, stage=stage)
                scenes.append(scene)

        return Novel(title=novel_info.title, id=novel_info.id, story_lines=storylines, characters=characters,
                     scenes=scenes, chapters=chapters, stages=novel_info.stages)

    def _read_novel_info(self, id: uuid.UUID) -> NovelInfo:
        path = self.novels_dir.joinpath(self.__json_file(id))
        if not os.path.exists(path):
            raise IOError(f'Could not find novel with id {id}')
        with open(path) as json_file:
            data = json_file.read()
            return NovelInfo.from_json(data)

    def _persist_project(self):
        with atomic_write(self.project_file_path, overwrite=True) as f:
            f.write(self.project.to_json())

    def _persist_novel(self, novel: Novel):
        novel_info = NovelInfo(title=novel.title, id=novel.id, scenes=[x.id for x in novel.scenes],
                               storylines=[StorylineInfo(text=x.text, id=x.id, color_hexa=x.color_hexa) for x in
                                           novel.story_lines], characters=[x.id for x in novel.characters],
                               chapters=[ChapterInfo(title=x.title, id=x.id) for x in novel.chapters],
                               stages=novel.stages)

        self.__persist_info(self.novels_dir, novel_info)

    def _persist_character(self, char: Character):
        char_info = CharacterInfo(id=char.id, name=char.name)
        self.__persist_info(self.characters_dir, char_info)

    def _persist_scene(self, scene: Scene):
        storylines = [x.id for x in scene.story_lines]
        characters = [x.id for x in scene.characters]
        arcs = [CharacterArcInfo(arc=x.arc, character=x.character.id) for x in scene.arcs]
        builder_elements = [self.__get_scene_builder_element_info(x) for x in
                            scene.builder_elements]
        info = SceneInfo(id=scene.id, title=scene.title, synopsis=scene.synopsis, type=scene.type,
                         beginning=scene.beginning, middle=scene.middle,
                         end=scene.end, wip=scene.wip, pivotal=scene.pivotal, day=scene.day, notes=scene.notes,
                         action_resolution=scene.action_resolution,
                         without_action_conflict=scene.without_action_conflict,
                         pov=scene.pov.id if scene.pov else None, storylines=storylines, characters=characters,
                         arcs=arcs, chapter=scene.chapter.id if scene.chapter else None,
                         scene_builder_elements=builder_elements,
                         stage=scene.stage.id if scene.stage else None)
        self.__persist_info(self.scenes_dir, info)

    def __get_scene_builder_element_info(self, el: SceneBuilderElement) -> SceneBuilderElementInfo:
        info = SceneBuilderElementInfo(type=el.type, text=el.text, character=el.character.id if el.character else None,
                                       has_suspense=el.has_suspense, has_stakes=el.has_stakes,
                                       has_tension=el.has_tension)
        for child in el.children:
            info.children.append(self.__get_scene_builder_element_info(child))

        return info

    def __get_scene_builder_element(self, info: SceneBuilderElementInfo,
                                    characters_ids: Dict[str, Character]) -> SceneBuilderElement:
        el = SceneBuilderElement(type=info.type, text=info.text,
                                 has_suspense=info.has_suspense, has_stakes=info.has_stakes,
                                 has_tension=info.has_tension)
        if info.character and str(info.character) in characters_ids.keys():
            el.character = characters_ids[str(info.character)]
        elif el.type == SceneBuilderElementType.SPEECH or el.type == SceneBuilderElementType.CHARACTER_ENTRY:
            el.character = NpcCharacter('Other')

        for child in info.children:
            el.children.append(self.__get_scene_builder_element(child, characters_ids))

        return el

    def __json_file(self, uuid: uuid.UUID) -> str:
        return f'{uuid}.json'

    def __image_file(self, uuid: uuid.UUID) -> str:
        return f'{uuid}.jpeg'

    def _load_image(self, filename) -> Optional[Any]:
        reader = QImageReader(str(self.images_dir.joinpath(filename)))
        reader.setAutoTransform(True)
        image: QImage = reader.read()
        if image is None:
            return None
        array = QByteArray()
        buffer = QBuffer(array)
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, 'PNG')
        return array

    def __persist_info(self, dir, info: Any):
        with atomic_write(dir.joinpath(self.__json_file(info.id)), overwrite=True) as f:
            f.write(info.to_json())

    def __delete_info(self, dir, id: uuid.UUID):
        os.remove(dir.joinpath(self.__json_file(id)))


json_client = JsonClient()
