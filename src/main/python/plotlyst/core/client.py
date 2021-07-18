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
import time
from enum import Enum
from typing import List

from PyQt5.QtCore import QTimer, Qt
from peewee import Model, TextField, SqliteDatabase, IntegerField, BooleanField, ForeignKeyField, BlobField, Proxy
from playhouse.sqlite_ext import CSqliteExtDatabase

from src.main.python.plotlyst.core.domain import Novel, Character, Scene, StoryLine, Event, Chapter, CharacterArc


class ApplicationDbVersion(Enum):
    R0 = 0  # before ApplicationModel existed
    R1 = 1


LATEST = ApplicationDbVersion.R1


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
                 NovelCharactersModel, SceneCharactersModel])
            ApplicationModel.create(revision=ApplicationDbVersion.R1.value)
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
    novel = ForeignKeyField(NovelModel, backref='scenes')
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
    novel = ForeignKeyField(NovelModel, backref='characters', on_delete='CASCADE')  # on_delete='CASCADE'
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


class SqlClient:

    def novels(self) -> List[Novel]:
        novels = []
        for novel_m in NovelModel.select():
            novels.append(Novel(id=novel_m.id, title=novel_m.title))

        return novels

    def insert_novel(self, novel: Novel):
        m = NovelModel.create(title=novel.title)
        novel.id = m.id

    def fetch_novel(self, id: int) -> Novel:
        novel_model = NovelModel.get_by_id(id)

        characters: List[Character] = []
        for char_m in novel_model.characters:
            characters.append(
                Character(id=char_m.character.id, name=char_m.character.name, avatar=char_m.character.avatar))

        story_lines: List[StoryLine] = []
        for story_m in novel_model.story_lines:
            story_lines.append(StoryLine(id=story_m.id, text=story_m.text))

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
            scenes.append(Scene(id=scene_m.id, title=scene_m.title, synopsis=scene_m.synopsis, type=scene_m.type,
                                pivotal=scene_m.pivotal, sequence=scene_m.sequence, beginning=scene_m.beginning,
                                middle=scene_m.middle, end=scene_m.end, wip=scene_m.wip, day=day,
                                end_event=end_event, characters=scene_characters, pov=pov,
                                story_lines=scene_story_lines, beginning_type=scene_m.beginning_type,
                                ending_hook=scene_m.ending_hook, notes=scene_m.notes, chapter=scene_chapter, arcs=arcs))

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

    def delete_story_line(self, story_line: StoryLine):
        m = NovelStoryLinesModel.get(id=story_line.id)
        m.delete_instance()

    def update_story_line(self, story_line: StoryLine):
        m = NovelStoryLinesModel.get_by_id(story_line.id)
        m.text = story_line.text
        m.save()

    def replace_scene_events(self, novel: Novel, scene: Scene, events: List[Event]):
        return


client = SqlClient()
