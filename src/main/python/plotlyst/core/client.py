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
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Iterable, Any

from PyQt5.QtCore import QTimer, Qt
from atomicwrites import atomic_write
from dataclasses_json import dataclass_json, Undefined
from peewee import Model, TextField, SqliteDatabase, IntegerField, BooleanField, ForeignKeyField, BlobField, Proxy, \
    DoesNotExist
from playhouse.sqlite_ext import CSqliteExtDatabase

from src.main.python.plotlyst.core.domain import Novel, Character, Scene, StoryLine, Chapter, CharacterArc, \
    SceneBuilderElement, SceneBuilderElementType, NpcCharacter
from src.main.python.plotlyst.settings import STORY_LINE_COLOR_CODES


class ApplicationDbVersion(Enum):
    R0 = 0  # before ApplicationModel existed
    R1 = 1
    R2 = 2
    R3 = 3
    R4 = 4  # add SceneBuilderElementModel


LATEST = ApplicationDbVersion.R4


class DbContext:

    def __init__(self):
        self._db = Proxy()
        self._ext_db = None
        self.workspace = None
        self._backup_timer = QTimer()
        self._backup_timer.setInterval(2 * 60 * 1000 * 60)  # 2 hours
        self._backup_timer.setTimerType(Qt.VeryCoarseTimer)
        self._backup_timer.timeout.connect(self._backup)

    def init(self, workspace: str):
        if workspace == ':memory:':
            db_file_name = workspace
            _create_tables = True
        else:
            db_file_name = os.path.join(workspace, 'novels.sqlite')
            _create_tables = False
            if not os.path.exists(db_file_name) or os.path.getsize(db_file_name) == 0:
                _create_tables = True
        runtime_db = SqliteDatabase(db_file_name, pragmas={
            'cache_size': 10000,  # 10000 pages, or ~40MB
            'foreign_keys': 1,  # Enforce foreign-key constraints
            'ignore_check_constraints': 0,
        })
        self._db.initialize(runtime_db)
        self._db.connect()

        if _create_tables:
            self._db.create_tables(
                [ApplicationModel, NovelModel, ChapterModel, SceneModel, CharacterModel, CharacterArcModel,
                 NovelStoryLinesModel,
                 SceneStoryLinesModel,
                 NovelCharactersModel, SceneCharactersModel, SceneBuilderElementModel])
            ApplicationModel.create(revision=LATEST.value)
            NovelModel.create(title='My First Novel')

        self._ext_db = CSqliteExtDatabase(db_file_name)
        self.workspace = workspace
        self._backup_timer.start()

    def db(self):
        return self._db

    def _backup(self):
        backup_dir = os.path.join(self.workspace, 'backups')
        if not os.path.exists(backup_dir):
            os.mkdir(backup_dir)
        elif os.path.isfile(backup_dir):
            os.remove(backup_dir)
            os.mkdir(backup_dir)
        files = os.listdir(backup_dir)
        if len(files) >= 10:
            os.remove(os.path.join(backup_dir, sorted(files)[0]))
        backup_file = os.path.join(backup_dir, f'{time.time()}.sqlite')
        backup_db = CSqliteExtDatabase(backup_file)
        self._ext_db.backup(backup_db)


context = DbContext()


class ApplicationModel(Model):
    revision = IntegerField()

    class Meta:
        table_name = 'Application'
        database = context.db()


class NovelModel(Model):
    title = TextField()

    class Meta:
        table_name = 'Novels'
        database = context.db()


class ChapterModel(Model):
    title = TextField()
    sequence = IntegerField()
    novel = ForeignKeyField(NovelModel, backref='chapters', on_delete='CASCADE')

    class Meta:
        table_name = 'Chapters'
        database = context.db()


class SceneModel(Model):
    title = TextField()
    novel = ForeignKeyField(NovelModel, backref='scenes', on_delete='CASCADE')
    type = TextField(null=True)
    synopsis = TextField(null=True)
    wip = BooleanField(default=False)
    pivotal = TextField(null=True)
    sequence = IntegerField(null=True)
    beginning = TextField(null=True)
    middle = TextField(null=True)
    end = TextField(null=True)
    chapter = ForeignKeyField(ChapterModel, backref='scenes', null=True, default=None)
    end_event = BooleanField(null=True)
    day = IntegerField(null=True)
    beginning_type = TextField(null=True)
    ending_hook = TextField(null=True)
    notes = TextField(null=True)
    draft_status = TextField(null=True)
    edition_status = TextField(null=True)
    action_resolution = BooleanField(null=True)
    without_action_conflict = BooleanField(null=True)

    class Meta:
        table_name = 'Scenes'
        database = context.db()


class CharacterModel(Model):
    name = TextField()
    avatar = BlobField(null=True)

    class Meta:
        table_name = 'Characters'
        database = context.db()


class CharacterArcModel(Model):
    arc = IntegerField()
    scene = ForeignKeyField(SceneModel, backref='arcs', on_delete='CASCADE')
    character = ForeignKeyField(CharacterModel, on_delete='CASCADE')

    class Meta:
        table_name = 'CharacterArcs'
        database = context.db()


class NovelStoryLinesModel(Model):
    text = TextField()
    color_hexa = TextField(null=True)
    novel = ForeignKeyField(NovelModel, backref='story_lines', on_delete='CASCADE')

    class Meta:
        table_name = 'NovelStoryLines'
        database = context.db()


class SceneStoryLinesModel(Model):
    story_line = ForeignKeyField(NovelStoryLinesModel, on_delete='CASCADE')
    scene = ForeignKeyField(SceneModel, backref='story_lines', on_delete='CASCADE')

    class Meta:
        table_name = 'StoryLinesScenes'
        database = context.db()


class NovelCharactersModel(Model):
    novel = ForeignKeyField(NovelModel, backref='characters', on_delete='CASCADE')
    character = ForeignKeyField(CharacterModel, on_delete='CASCADE')

    class Meta:
        table_name = 'NovelCharacters'
        database = context.db()


class SceneCharactersModel(Model):
    scene = ForeignKeyField(SceneModel, backref='characters', on_delete='CASCADE')
    character = ForeignKeyField(CharacterModel, on_delete='CASCADE')
    type = TextField()

    class Meta:
        table_name = 'SceneCharacters'
        database = context.db()


class SceneBuilderElementModel(Model):
    sequence = IntegerField()
    type = TextField()
    text = TextField(null=True)
    scene = ForeignKeyField(SceneModel, backref='elements', on_delete='CASCADE')
    character = ForeignKeyField(CharacterModel, null=True, on_delete='CASCADE')
    parent = ForeignKeyField('self', related_name='children', null=True, on_delete='CASCADE')
    suspense = BooleanField(default=False)
    tension = BooleanField(default=False)
    stakes = BooleanField(default=False)

    class Meta:
        table_name = 'SceneBuilderElements'
        database = context.db()


class SqlClient:

    def novels(self) -> List[Novel]:
        novels = []
        for novel_m in NovelModel.select():
            novels.append(Novel(id=novel_m.id, title=novel_m.title))

        return novels

    def has_novel(self, id: int) -> bool:
        try:
            NovelModel.get_by_id(id)
            return True
        except DoesNotExist:
            return False

    def insert_novel(self, novel: Novel):
        m = NovelModel.create(title=novel.title)
        novel.id = m.id

    def delete_novel(self, novel: Novel):
        novel_m = NovelModel.get(id=novel.id)
        novel_m.delete_instance()

    def update_novel(self, novel: Novel):
        novel_m = NovelModel.get(id=novel.id)
        novel_m.title = novel.title

        novel_m.save()

    def fetch_novel(self, id: int) -> Novel:
        return json_client.fetch_novel()
        novel_model = NovelModel.get_by_id(id)

        characters: List[Character] = []
        for char_m in novel_model.characters:
            characters.append(
                Character(id=char_m.character.id, name=char_m.character.name, avatar=char_m.character.avatar))

        story_lines: List[StoryLine] = []
        for i, story_m in enumerate(novel_model.story_lines):
            if story_m.color_hexa:
                color = story_m.color_hexa
            else:
                color = STORY_LINE_COLOR_CODES[i % len(STORY_LINE_COLOR_CODES)]
            story_lines.append(StoryLine(id=story_m.id, text=story_m.text, color_hexa=color))

        chapters: List[Chapter] = []
        for chapter_m in novel_model.chapters:
            chapters.append(Chapter(id=chapter_m.id, title=chapter_m.title, sequence=chapter_m.sequence))

        scenes: List[Scene] = []
        for scene_m in novel_model.scenes:
            scene_characters = []
            pov = None
            for char_m in scene_m.characters:
                for char in characters:
                    if char.id == char_m.character.id:
                        if char_m.type == 'pov':
                            pov = char
                        else:
                            scene_characters.append(char)

            scene_story_lines = []
            for story_m in scene_m.story_lines:
                for story in story_lines:
                    if story.id == story_m.story_line.id:
                        scene_story_lines.append(story)

            scene_chapter = None
            if scene_m.chapter:
                for chapter in chapters:
                    if chapter.id == scene_m.chapter.id:
                        scene_chapter = chapter
                        break
            arcs: List[CharacterArc] = []
            for arc_m in scene_m.arcs:
                for char in characters:
                    if char.id == arc_m.character.id:
                        arcs.append(CharacterArc(arc_m.arc, char))

            day = scene_m.day if scene_m.day else 0
            end_event = scene_m.end_event if scene_m.end_event else True
            without_action_conflict = scene_m.without_action_conflict if scene_m.without_action_conflict else False
            action_resolution = scene_m.action_resolution if scene_m.action_resolution else False
            scenes.append(Scene(id=scene_m.id, title=scene_m.title, synopsis=scene_m.synopsis, type=scene_m.type,
                                pivotal=scene_m.pivotal, sequence=scene_m.sequence, beginning=scene_m.beginning,
                                middle=scene_m.middle, end=scene_m.end, wip=scene_m.wip, day=day,
                                end_event=end_event, characters=scene_characters, pov=pov,
                                story_lines=scene_story_lines, beginning_type=scene_m.beginning_type,
                                ending_hook=scene_m.ending_hook, notes=scene_m.notes, chapter=scene_chapter, arcs=arcs,
                                without_action_conflict=without_action_conflict, action_resolution=action_resolution))

        scenes = sorted(scenes, key=lambda x: x.sequence)
        novel: Novel = Novel(id=novel_model.id, title=novel_model.title, scenes=scenes, characters=characters,
                             story_lines=story_lines, chapters=chapters)

        return novel

    def insert_character(self, novel: Novel, character: Character):
        character_m = CharacterModel.create(name=character.name, avatar=character.avatar)
        character.id = character_m.id

        novel_m = NovelModel.get(id=novel.id)
        NovelCharactersModel.create(novel=novel_m, character=character_m)

    def update_character(self, character: Character):
        character_m: CharacterModel = CharacterModel.get_by_id(character.id)
        character_m.name = character.name
        character_m.avatar = character.avatar

        character_m.save()

    def delete_character(self, character: Character):
        character_m = CharacterModel.get(id=character.id)
        character_m.delete_instance()

    def update_scene(self, scene: Scene):
        scene_m: SceneModel = SceneModel.get_by_id(scene.id)
        scene_m.title = scene.title
        scene_m.synopsis = scene.synopsis
        scene_m.type = scene.type
        scene_m.pivotal = scene.pivotal
        scene_m.sequence = scene.sequence
        scene_m.beginning = scene.beginning
        scene_m.middle = scene.middle
        scene_m.end = scene.end
        scene_m.wip = scene.wip
        scene_m.end_event = scene.end_event
        scene_m.day = scene.day
        scene_m.beginning_type = scene.beginning_type
        scene_m.ending_hook = scene.ending_hook
        scene_m.notes = scene.notes
        scene_m.without_action_conflict = scene.without_action_conflict
        scene_m.action_resolution = scene.action_resolution

        scene_m.save()

        self._update_scene_characters(scene)
        self._update_scene_story_lines(scene)
        self._update_scene_character_arcs(scene)

    def update_scene_chapter(self, scene: Scene):
        scene_m: SceneModel = SceneModel.get_by_id(scene.id)
        if scene.chapter:
            scene_m.chapter = scene.chapter.id
        else:
            scene_m.chapter = None

        scene_m.save()

    def update_scene_sequences(self, novel: Novel):
        for scene in novel.scenes:
            m = SceneModel.get_by_id(scene.id)
            m.sequence = scene.sequence
            m.save()

    def insert_scene(self, novel: Novel, scene: Scene):
        scene_m: SceneModel = SceneModel.create(title=scene.title, synopsis=scene.synopsis, type=scene.type,
                                                pivotal=scene.pivotal, sequence=scene.sequence,
                                                beginning=scene.beginning,
                                                middle=scene.middle, end=scene.end, novel=novel.id, wip=scene.wip,
                                                end_event=scene.end_event, day=scene.day,
                                                beginning_type=scene.beginning_type,
                                                ending_hook=scene.ending_hook, notes=scene.notes)
        scene.id = scene_m.id

        self._update_scene_characters(scene)
        self._update_scene_story_lines(scene)

    def _update_scene_story_lines(self, scene: Scene):
        scene_m = SceneModel.get_by_id(scene.id)
        for story_line in scene_m.story_lines:
            story_line.delete_instance()

        for story_line in scene.story_lines:
            SceneStoryLinesModel.create(story_line=story_line.id, scene=scene.id)

    def _update_scene_character_arcs(self, scene: Scene):
        scene_m = SceneModel.get_by_id(scene.id)
        for arc in scene_m.arcs:
            arc.delete_instance()

        for character_arc in scene.arcs:
            CharacterArcModel.create(arc=character_arc.arc, character=character_arc.character.id, scene=scene.id)

    def _update_scene_characters(self, scene: Scene):
        scene_m = SceneModel.get_by_id(scene.id)
        for char in scene_m.characters:
            char.delete_instance()
        for char in scene.characters:
            SceneCharactersModel.create(scene=scene.id, character=char.id, type='active')
        if scene.pov:
            SceneCharactersModel.create(scene=scene.id, character=scene.pov.id, type='pov')

    def delete_scene(self, scene: Scene):
        scene_m = SceneModel.get(id=scene.id)
        scene_m.delete_instance()

    def insert_chapter(self, novel: Novel, chapter: Chapter):
        m = ChapterModel.create(title=chapter.title, novel=novel.id, sequence=chapter.sequence)
        chapter.id = m.id

    def insert_story_line(self, novel: Novel, story_line: StoryLine):
        m = NovelStoryLinesModel.create(text=story_line.text, novel=novel.id)
        story_line.id = m.id
        story_line.color_hexa = story_line.color_hexa

    def delete_story_line(self, story_line: StoryLine):
        m = NovelStoryLinesModel.get(id=story_line.id)
        m.delete_instance()

    def update_story_line(self, story_line: StoryLine):
        m = NovelStoryLinesModel.get_by_id(story_line.id)
        m.text = story_line.text
        m.color_hexa = story_line.color_hexa
        m.save()

    def fetch_scene_builder_elements(self, novel: Novel, scene: Scene) -> List[SceneBuilderElement]:
        scene_m = SceneModel.get_by_id(scene.id)
        parents_by_id: Dict[int, SceneBuilderElement] = {}
        characters: Dict[int, Character] = {}
        for char in novel.characters:
            if char.id:
                characters[char.id] = char

        elements: List[SceneBuilderElement] = []
        for element_m in scene_m.elements:
            element = self.__get_scene_builder_element(scene, element_m, parents_by_id, characters)
            if not element_m.parent:
                elements.append(parents_by_id[element.id])
        for el in elements:
            self._sort_children(el)
        return elements

    def __get_scene_builder_element(self, scene: Scene, element_m,
                                    parents_by_id: Dict[int, SceneBuilderElement],
                                    characters: Dict[int, Character]) -> SceneBuilderElement:
        if element_m.parent:
            if element_m.parent.id not in parents_by_id.keys():
                self.__get_scene_builder_element(scene, element_m.parent, parents_by_id, characters)
            parent = parents_by_id[element_m.parent.id]
        else:
            parent = None
        if element_m.character:
            character = characters[element_m.character.id]
        elif element_m.type == SceneBuilderElementType.SPEECH.value:
            character = NpcCharacter('Other')
        elif element_m.type == SceneBuilderElementType.CHARACTER_ENTRY.value:
            character = NpcCharacter('Other')
        else:
            character = None
        new_element = SceneBuilderElement(scene=scene, type=SceneBuilderElementType(element_m.type),
                                          sequence=element_m.sequence,
                                          character=character,
                                          text=element_m.text,
                                          has_suspense=element_m.suspense,
                                          has_tension=element_m.tension,
                                          has_stakes=element_m.stakes, id=element_m.id)
        if new_element.id not in parents_by_id.keys():
            parents_by_id[new_element.id] = new_element
        if parent:
            parent.children.append(new_element)
        return new_element

    def _sort_children(self, element: SceneBuilderElement):
        element.children = sorted(element.children, key=lambda x: x.sequence)
        for child in element.children:
            self._sort_children(child)

    def update_scene_builder_elements(self, scene: Scene, elements: List[SceneBuilderElement]):
        scene_m = SceneModel.get_by_id(scene.id)
        for el_m in scene_m.elements:
            el_m.delete_instance()

        for seq, el in enumerate(elements):
            self._create_scene_builder_element(scene, el, seq)

    def _create_scene_builder_element(self, scene: Scene, element: SceneBuilderElement, sequence: int, parent_id=None):
        if element.character:
            char_id = element.character.id
        else:
            char_id = None
        el_parent = SceneBuilderElementModel.create(scene=scene.id, character=char_id, text=element.text,
                                                    parent=parent_id,
                                                    sequence=sequence,
                                                    type=element.type.value, suspense=element.has_suspense,
                                                    stakes=element.has_stakes,
                                                    tension=element.has_tension)
        for seq_child, el_child in enumerate(element.children):
            self._create_scene_builder_element(scene, el_child, seq_child, el_parent.id)


client = SqlClient()


@dataclass_json
@dataclass
class CharacterInfo:
    name: str
    id: uuid.UUID


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
    # chapter: Optional[Chapter] = None
    # arcs: List[CharacterArc] = field(default_factory=list)
    action_resolution: bool = False
    without_action_conflict: bool = False


@dataclass
class StorylineInfo:
    text: str
    id: uuid.UUID
    color_hexa: str = ''


@dataclass
class NovelInfo:
    title: str
    id: uuid.UUID
    scenes: List[uuid.UUID] = field(default_factory=list)
    characters: List[uuid.UUID] = field(default_factory=list)
    storylines: List[StorylineInfo] = field(default_factory=list)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Project:
    novels: List[NovelInfo] = field(default_factory=list)


class JsonClient:

    def __init__(self):
        self.project: Optional[Project] = None
        self._workspace = ''
        self.project_file_path = ''
        self.root_path: Optional[pathlib.Path] = None
        self.scenes_dir: Optional[pathlib.Path] = None
        self.characters_dir: Optional[pathlib.Path] = None

    def init(self, workspace: str):
        self.project_file_path = os.path.join(workspace, 'project.plotlyst')

        if not os.path.exists(self.project_file_path) or os.path.getsize(self.project_file_path) == 0:
            self.project = Project()
        else:
            with open(self.project_file_path) as json_file:
                data = json_file.read()
                self.project = Project.from_json(data)

        self._workspace = workspace
        self.root_path = pathlib.Path(self._workspace)
        self.scenes_dir = self.root_path.joinpath('scenes')
        self.characters_dir = self.root_path.joinpath('characters')

    def fetch_novel(self) -> Novel:
        novel_info = self.project.novels[0]

        storylines = [StoryLine(text=x.text, id=x.id, color_hexa=x.color_hexa) for x in novel_info.storylines]
        storylines_ids = {}
        for sl in storylines:
            storylines_ids[str(sl.id)] = sl

        characters = []
        for char_id in novel_info.characters:
            path = self.characters_dir.joinpath(self.__json_file(char_id))
            if not os.path.exists(path):
                continue
            with open(path) as json_file:
                data = json_file.read()
                info: CharacterInfo = CharacterInfo.from_json(data)
                characters.append(Character(name=info.name, id=info.id))
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
                print(scene_characters)
                scene = Scene(title=info.title, id=info.id, synopsis=info.synopsis, type=info.type,
                              beginning=info.beginning,
                              middle=info.middle, end=info.end, wip=info.wip, pivotal=info.pivotal, day=info.day,
                              notes=info.notes,
                              action_resolution=info.action_resolution,
                              without_action_conflict=info.without_action_conflict, sequence=seq,
                              story_lines=scene_storylines, pov=pov, characters=scene_characters)
                scenes.append(scene)

        return Novel(title=novel_info.title, id=novel_info.id, story_lines=storylines, characters=characters,
                     scenes=scenes)

    def persist(self, novel: Novel):
        novel.id = uuid.uuid4()
        for scene in novel.scenes:
            scene.id = uuid.uuid4()
        for char in novel.characters:
            char.id = uuid.uuid4()
        for storyline in novel.story_lines:
            storyline.id = uuid.uuid4()

        self.project.novels.clear()
        novel_info = NovelInfo(title=novel.title, id=novel.id, scenes=[x.id for x in novel.scenes],
                               storylines=[StorylineInfo(text=x.text, id=x.id, color_hexa=x.color_hexa) for x in
                                           novel.story_lines], characters=[x.id for x in novel.characters])
        self.project.novels.append(novel_info)
        with atomic_write(self.project_file_path, overwrite=True) as f:
            f.write(self.project.to_json())

        self._persist_characters(self.root_path, novel)
        self._persist_scenes(self.root_path, novel)

    def _persist_characters(self, root_path: pathlib.Path, novel: Novel):
        if not os.path.exists(str(self.characters_dir)):
            os.mkdir(self.characters_dir)

        infos = [CharacterInfo(id=x.id, name=x.name) for x in novel.characters]
        self.__persist_info(self.characters_dir, infos)

    def _persist_scenes(self, root_path: pathlib.Path, novel: Novel):
        if not os.path.exists(str(self.scenes_dir)):
            os.mkdir(self.scenes_dir)

        scene_infos = []
        for scene in novel.scenes:
            storylines = [x.id for x in scene.story_lines]
            characters = [x.id for x in scene.characters]
            info = SceneInfo(id=scene.id, title=scene.title, synopsis=scene.synopsis, type=scene.type,
                             beginning=scene.beginning, middle=scene.middle,
                             end=scene.end, wip=scene.wip, pivotal=scene.pivotal, day=scene.day, notes=scene.notes,
                             action_resolution=scene.action_resolution,
                             without_action_conflict=scene.without_action_conflict,
                             pov=scene.pov.id if scene.pov else None, storylines=storylines, characters=characters)
            scene_infos.append(info)
        self.__persist_info(self.scenes_dir, scene_infos)

    def __json_file(self, uuid: uuid.UUID) -> str:
        return f'{uuid}.json'

    def __persist_info(self, dir, infos: Iterable[Any]):
        for info in infos:
            with atomic_write(dir.joinpath(self.__json_file(info.id)), overwrite=True) as f:
                f.write(info.to_json())


json_client = JsonClient()
