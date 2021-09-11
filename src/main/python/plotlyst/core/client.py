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
import codecs
import json
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

from src.main.python.plotlyst.core.domain import Novel, Character, Scene, Chapter, CharacterArc, \
    SceneBuilderElement, SceneBuilderElementType, NpcCharacter, SceneStage, default_stages, StoryStructure, \
    default_story_structures, NovelDescriptor, ProfileTemplate, default_character_profiles, TemplateValue, \
    DramaticQuestion, ConflictType, Conflict, BackstoryEvent, Comment, SceneGoal, Document, SelectionItem, \
    default_tags, default_documents


class ApplicationDbVersion(Enum):
    R0 = 0  # before ApplicationModel existed
    R1 = 1
    R2 = 2
    R3 = 3
    R4 = 4  # add SceneBuilderElementModel


LATEST = ApplicationDbVersion.R4


class SqlClient:

    def novels(self) -> List[NovelDescriptor]:
        return json_client.novels()

    def has_novel(self, id: uuid.UUID) -> bool:
        return json_client.has_novel(id)

    def insert_novel(self, novel: Novel):
        json_client.insert_novel(novel)

    def delete_novel(self, novel: Novel):
        json_client.delete_novel(novel)

    def update_project_novel(self, novel: Novel):
        json_client.update_project_novel(novel)

    def update_novel(self, novel: Novel):
        json_client.update_novel(novel)

    def fetch_novel(self, id: uuid.UUID) -> Novel:
        return json_client.fetch_novel(id)

    def insert_character(self, novel: Novel, character: Character):
        json_client.insert_character(novel, character)

    def update_character(self, character: Character, update_avatar: bool = False):
        json_client.update_character(character, update_avatar)

    def delete_character(self, novel: Novel, character: Character):
        json_client.delete_character(novel, character)

    def update_scene(self, scene: Scene):
        json_client.update_scene(scene)

    def insert_scene(self, novel: Novel, scene: Scene):
        json_client.insert_scene(novel, scene)

    def delete_scene(self, novel: Novel, scene: Scene):
        json_client.delete_scene(novel, scene)


client = SqlClient()


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CharacterInfo:
    name: str
    id: uuid.UUID
    avatar_id: Optional[uuid.UUID] = None
    template_values: List[TemplateValue] = field(default_factory=list)
    backstory: List[BackstoryEvent] = field(default_factory=list)


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


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SceneInfo:
    title: str
    id: uuid.UUID
    synopsis: str = ''
    type: str = ''
    beginning: str = ''
    middle: str = ''
    end: str = ''
    pov: Optional[uuid.UUID] = None
    characters: List[uuid.UUID] = field(default_factory=list)
    wip: bool = False
    dramatic_questions: List[uuid.UUID] = field(default_factory=list)
    storylines: List[uuid.UUID] = field(default_factory=list)
    day: int = 1
    notes: str = ''
    chapter: Optional[uuid.UUID] = None
    arcs: List[CharacterArcInfo] = field(default_factory=list)
    action_resolution: bool = False
    action_trade_off: bool = False
    without_action_conflict: bool = False
    scene_builder_elements: List[SceneBuilderElementInfo] = field(default_factory=list)
    stage: Optional[uuid.UUID] = None
    beat: Optional[uuid.UUID] = None
    conflicts: List[uuid.UUID] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class ChapterInfo:
    title: str
    id: uuid.UUID


@dataclass
class ConflictInfo:
    keyphrase: str
    type: ConflictType
    id: uuid.UUID
    pov: uuid.UUID
    character: Optional[uuid.UUID] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class NovelInfo:
    id: uuid.UUID
    story_structure: uuid.UUID = default_story_structures[0].id
    scenes: List[uuid.UUID] = field(default_factory=list)
    characters: List[uuid.UUID] = field(default_factory=list)
    storylines: List[DramaticQuestion] = field(default_factory=list)
    dramatic_questions: List[DramaticQuestion] = field(default_factory=list)
    chapters: List[ChapterInfo] = field(default_factory=list)
    stages: List[SceneStage] = field(default_factory=default_stages)
    character_profiles: List[ProfileTemplate] = field(default_factory=default_character_profiles)
    conflicts: List[ConflictInfo] = field(default_factory=list)
    scene_goals: List[SceneGoal] = field(default_factory=list)
    tags: List[SelectionItem] = field(default_factory=default_tags)
    documents: List[Document] = field(default_factory=default_documents)


@dataclass
class ProjectNovelInfo:
    title: str
    id: uuid.UUID


def _default_story_structures():
    return default_story_structures


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Project:
    novels: List[ProjectNovelInfo] = field(default_factory=list)
    story_structures: List[StoryStructure] = field(default_factory=_default_story_structures)


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
        self.docs_dir: Optional[pathlib.Path] = None

    def init(self, workspace: str):
        self.project_file_path = os.path.join(workspace, 'project.plotlyst')

        if not os.path.exists(self.project_file_path) or os.path.getsize(self.project_file_path) == 0:
            self.project = Project()
            self._persist_project()
        else:
            with open(self.project_file_path) as json_file:
                data = json_file.read()
                self.project = Project.from_json(data)
                self.project.story_structures = [x for x in self.project.story_structures if x.custom]
                self.project.story_structures.extend(default_story_structures)
            self._persist_project()

        self._workspace = workspace
        self.root_path = pathlib.Path(self._workspace)
        self.novels_dir = self.root_path.joinpath('novels')
        self.scenes_dir = self.root_path.joinpath('scenes')
        self.characters_dir = self.root_path.joinpath('characters')
        self.images_dir = self.root_path.joinpath('images')
        self.docs_dir = self.root_path.joinpath('docs')

        if not os.path.exists(str(self.novels_dir)):
            os.mkdir(self.novels_dir)
        if not os.path.exists(str(self.scenes_dir)):
            os.mkdir(self.scenes_dir)
        if not os.path.exists(str(self.characters_dir)):
            os.mkdir(self.characters_dir)
        if not os.path.exists(str(self.images_dir)):
            os.mkdir(self.images_dir)
        if not os.path.exists(str(self.docs_dir)):
            os.mkdir(self.docs_dir)

    def novels(self) -> List[NovelDescriptor]:
        return [NovelDescriptor(title=x.title, id=x.id) for x in self.project.novels]

    def has_novel(self, id: uuid.UUID):
        for novel in self.project.novels:
            if novel.id == id:
                return True
        return False

    def update_project_novel(self, novel: Novel):
        novel_info = self._find_project_novel_info_or_fail(novel.id)
        if novel_info.title != novel.title:
            novel_info.title = novel.title
            self._persist_project()

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
        self.update_character(character, True)
        self._persist_novel(novel)

    def update_character(self, character: Character, update_avatar: bool = False):
        avatar_id: Optional[uuid.UUID] = None

        path = self.characters_dir.joinpath(self.__json_file(character.id))
        if os.path.exists(path):
            with open(path) as json_file:
                data = json_file.read()
                info: CharacterInfo = CharacterInfo.from_json(data)
                avatar_id = info.avatar_id

        if update_avatar:
            if avatar_id:
                self.__delete_image(avatar_id)
                avatar_id = None
            if character.avatar:
                avatar_id = uuid.uuid4()
                image = QImage.fromData(character.avatar)
                image.save(str(self.images_dir.joinpath(self.__image_file(avatar_id))))

        self._persist_character(character, avatar_id)

    def delete_character(self, novel: Novel, character: Character):
        self._persist_novel(novel)
        self.__delete_info(self.characters_dir, character.id)

    def _find_project_novel_info_or_fail(self, id: uuid.UUID) -> ProjectNovelInfo:
        for info in self.project.novels:
            if info.id == id:
                return info
        raise ValueError(f'Could not find novel with id {id}')

    def load_document(self, novel: Novel, document: Document):
        if document.content_loaded:
            return

        content = self.__load_doc(novel, document.id)
        document.content = content
        document.content_loaded = True

    def save_document(self, novel: Novel, document: Document):
        self.__persist_doc(novel, document)

    def delete_document(self, novel: Novel, document: Document):
        self.__delete_doc(novel, document)

    def fetch_novel(self, id: uuid.UUID) -> Novel:
        project_novel_info: ProjectNovelInfo = self._find_project_novel_info_or_fail(id)
        novel_info = self._read_novel_info(project_novel_info.id)
        self.__persist_info(self.novels_dir, novel_info)

        dq_ids = {}
        for dq in novel_info.dramatic_questions:
            dq_ids[str(dq.id)] = dq
        chapters = []
        chapters_ids = {}
        for seq, chapter_info in enumerate(novel_info.chapters):
            chapter = Chapter(title=chapter_info.title, id=chapter_info.id)
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
                character = Character(name=info.name, id=info.id, template_values=info.template_values,
                                      backstory=info.backstory)
                if info.avatar_id:
                    bytes = self._load_image(self.__image_file(info.avatar_id))
                    if bytes:
                        character.avatar = bytes
                characters.append(character)
        characters_ids = {}
        for char in characters:
            characters_ids[str(char.id)] = char

        conflicts = []
        conflict_ids = {}
        for conflict_info in novel_info.conflicts:
            pov = characters_ids.get(str(conflict_info.pov))
            if not pov:
                continue
            character = None
            if conflict_info.character:
                character = characters_ids.get(str(conflict_info.character))
                if character is None:
                    continue

            conflict = Conflict(keyphrase=conflict_info.keyphrase, type=conflict_info.type, id=conflict_info.id,
                                pov=pov,
                                character=character)
            conflicts.append(conflict)
            conflict_ids[str(conflict.id)] = conflict

        goals_index = {}
        for goal in novel_info.scene_goals:
            goals_index[goal.text] = goal

        story_structure: StoryStructure = self.project.story_structures[0]
        for structure in self.project.story_structures:
            if structure.id == novel_info.story_structure:
                story_structure = structure
        beat_ids = {}
        for beat in story_structure.beats:
            beat_ids[str(beat.id)] = beat

        scenes: List[Scene] = []
        for seq, scene_id in enumerate(novel_info.scenes):
            path = self.scenes_dir.joinpath(self.__json_file(scene_id))
            if not os.path.exists(path):
                continue
            with open(path) as json_file:
                data = json_file.read()
                info: SceneInfo = SceneInfo.from_json(data)
                scene_storylines = []
                questions = info.storylines if info.storylines else info.dramatic_questions
                for sl_id in questions:
                    if str(sl_id) in dq_ids.keys():
                        scene_storylines.append(dq_ids[str(sl_id)])
                if info.pov and str(info.pov) in characters_ids.keys():
                    pov = characters_ids[str(info.pov)]
                else:
                    pov = None

                scene_characters = []
                for char_id in info.characters:
                    if str(char_id) in characters_ids.keys():
                        scene_characters.append(characters_ids[str(char_id)])

                scene_conflicts = []
                for conflict_id in info.conflicts:
                    if str(conflict_id) in conflict_ids.keys():
                        scene_conflicts.append(conflict_ids[str(conflict_id)])

                scene_goals = []
                for goal_text in info.goals:
                    if goal_text in goals_index.keys():
                        scene_goals.append(goals_index[goal_text])

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

                beat = beat_ids.get(str(info.beat))
                scene = Scene(title=info.title, id=info.id, synopsis=info.synopsis, type=info.type,
                              beginning=info.beginning,
                              middle=info.middle, end=info.end, wip=info.wip, day=info.day,
                              notes=info.notes,
                              action_resolution=info.action_resolution, action_trade_off=info.action_trade_off,
                              without_action_conflict=info.without_action_conflict, sequence=seq,
                              dramatic_questions=scene_storylines, pov=pov, characters=scene_characters, arcs=arcs,
                              chapter=chapter, builder_elements=builder_elements, stage=stage, beat=beat,
                              conflicts=scene_conflicts, goals=scene_goals, comments=info.comments, tags=info.tags)
                scenes.append(scene)
        return Novel(title=project_novel_info.title, id=novel_info.id, dramatic_questions=novel_info.dramatic_questions,
                     characters=characters,
                     scenes=scenes, chapters=chapters, stages=novel_info.stages,
                     story_structure=story_structure, character_profiles=novel_info.character_profiles,
                     conflicts=conflicts, scene_goals=novel_info.scene_goals, tags=novel_info.tags,
                     documents=novel_info.documents)

    def _read_novel_info(self, id: uuid.UUID) -> NovelInfo:
        path = self.novels_dir.joinpath(self.__json_file(id))
        if not os.path.exists(path):
            raise IOError(f'Could not find novel with id {id}')
        with open(path) as json_file:
            data = json_file.read()
            data_json = json.loads(data)
            if isinstance(data_json['story_structure'], dict):
                data_json['story_structure'] = self.project.story_structures[0].id
                return NovelInfo.from_dict(data_json)
            else:
                return NovelInfo.from_json(data)

    def _persist_project(self):
        with atomic_write(self.project_file_path, overwrite=True) as f:
            f.write(self.project.to_json())

    def _persist_novel(self, novel: Novel):
        novel_info = NovelInfo(id=novel.id, scenes=[x.id for x in novel.scenes],
                               dramatic_questions=novel.dramatic_questions,
                               characters=[x.id for x in novel.characters],
                               chapters=[ChapterInfo(title=x.title, id=x.id) for x in novel.chapters],
                               stages=novel.stages, story_structure=novel.story_structure.id,
                               character_profiles=novel.character_profiles,
                               conflicts=[ConflictInfo(x.keyphrase, x.type, x.id,
                                                       pov=x.pov.id,
                                                       character=x.character.id if x.character else None) for x in
                                          novel.conflicts],
                               scene_goals=novel.scene_goals, tags=novel.tags, documents=novel.documents)

        self.__persist_info(self.novels_dir, novel_info)

    def _persist_character(self, char: Character, avatar_id: Optional[uuid.UUID] = None):
        char_info = CharacterInfo(id=char.id, name=char.name, template_values=char.template_values, avatar_id=avatar_id,
                                  backstory=char.backstory)
        self.__persist_info(self.characters_dir, char_info)

    def _persist_scene(self, scene: Scene):
        dramatic_questions = [x.id for x in scene.dramatic_questions]
        characters = [x.id for x in scene.characters]
        arcs = [CharacterArcInfo(arc=x.arc, character=x.character.id) for x in scene.arcs]
        builder_elements = [self.__get_scene_builder_element_info(x) for x in
                            scene.builder_elements]
        conflicts = [x.id for x in scene.conflicts]
        info = SceneInfo(id=scene.id, title=scene.title, synopsis=scene.synopsis, type=scene.type,
                         beginning=scene.beginning, middle=scene.middle,
                         end=scene.end, wip=scene.wip, day=scene.day, notes=scene.notes,
                         action_resolution=scene.action_resolution, action_trade_off=scene.action_trade_off,
                         without_action_conflict=scene.without_action_conflict,
                         pov=self.__id_or_none(scene.pov), dramatic_questions=dramatic_questions, characters=characters,
                         arcs=arcs, chapter=self.__id_or_none(scene.chapter),
                         scene_builder_elements=builder_elements,
                         stage=self.__id_or_none(scene.stage),
                         beat=self.__id_or_none(scene.beat),
                         conflicts=conflicts, goals=[x.text for x in scene.goals], comments=scene.comments,
                         tags=scene.tags)
        self.__persist_info(self.scenes_dir, info)

    @staticmethod
    def __id_or_none(item):
        return item.id if item else None

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

    def __doc_file(self, uuid: uuid.UUID) -> str:
        return f'{uuid}.html'

    def _load_image(self, filename) -> Optional[Any]:
        path = self.images_dir.joinpath(filename)
        if not os.path.exists(path):
            return None
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        image: QImage = reader.read()
        if image is None:
            return None
        array = QByteArray()
        buffer = QBuffer(array)
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, 'PNG')
        return array

    def __load_doc(self, novel: Novel, doc_uuid: uuid.UUID) -> str:
        novel_doc_dir = self.docs_dir.joinpath(str(novel.id))
        path = novel_doc_dir.joinpath(self.__doc_file(doc_uuid))
        if not os.path.exists(path):
            return ''
        with codecs.open(str(path), "r", "utf-8") as doc_file:
            return doc_file.read()

    def __persist_doc(self, novel: Novel, doc: Document):
        novel_doc_dir = self.docs_dir.joinpath(str(novel.id))
        if not os.path.exists(str(novel_doc_dir)):
            os.mkdir(novel_doc_dir)

        doc_file_path = novel_doc_dir.joinpath(self.__doc_file(doc.id))
        with atomic_write(doc_file_path, overwrite=True) as f:
            f.write(doc.content)

    def __persist_info(self, dir, info: Any):
        with atomic_write(dir.joinpath(self.__json_file(info.id)), overwrite=True) as f:
            f.write(info.to_json())

    def __delete_info(self, dir, id: uuid.UUID):
        path = dir.joinpath(self.__json_file(id))
        if os.path.exists(path):
            os.remove(path)

    def __delete_image(self, id: uuid.UUID):
        path = self.images_dir.joinpath(self.__image_file(id))
        if os.path.exists(path):
            os.remove(path)

    def __delete_doc(self, novel: Novel, doc: Document):
        novel_doc_dir = self.docs_dir.joinpath(str(novel.id))
        if not os.path.exists(str(novel_doc_dir)):
            return
        doc_file_path = novel_doc_dir.joinpath(self.__doc_file(doc.id))
        if os.path.exists(doc_file_path):
            os.remove(doc_file_path)


json_client = JsonClient()
