from typing import List

from peewee import Model, TextField, SqliteDatabase, IntegerField, BooleanField, ForeignKeyField, BlobField

from novel_outliner.core.domain import Novel, Character, Scene, StoryLine, Event

db = SqliteDatabase("/home/zkovari/novels/novels.sqlite", pragmas={
    'journal_mode': 'wal',
    'cache_size': 10000,  # 10000 pages, or ~40MB
    'foreign_keys': 1,  # Enforce foreign-key constraints
    'ignore_check_constraints': 0,
})


class NovelModel(Model):
    title = TextField()

    class Meta:
        table_name = 'Novels'
        database = db


class SceneModel(Model):
    title = TextField()
    synopsis = TextField()
    type = TextField()
    pivotal = TextField()
    sequence = IntegerField()
    beginning = TextField()
    middle = TextField()
    end = TextField()
    novel = ForeignKeyField(NovelModel, backref='scenes')
    wip = BooleanField()
    end_event = BooleanField()
    day = IntegerField()

    class Meta:
        table_name = 'Scenes'
        database = db


class CharacterModel(Model):
    name = TextField()
    avatar = BlobField()

    class Meta:
        table_name = 'Characters'
        database = db


class NovelStoryLinesModel(Model):
    text = TextField()
    novel = ForeignKeyField(NovelModel, backref='story_lines')

    class Meta:
        table_name = 'NovelStoryLines'
        database = db


class SceneStoryLinesModel(Model):
    story_line = ForeignKeyField(NovelStoryLinesModel)
    scene = ForeignKeyField(SceneModel, backref='story_lines')

    class Meta:
        table_name = 'StoryLinesScenes'
        database = db


class NovelCharactersModel(Model):
    novel = ForeignKeyField(NovelModel, backref='characters')  # on_delete='CASCADE'
    character = ForeignKeyField(CharacterModel)

    class Meta:
        table_name = 'NovelCharacters'
        database = db


class SceneCharactersModel(Model):
    scene = ForeignKeyField(SceneModel, backref='characters')
    character = ForeignKeyField(CharacterModel)
    type = TextField()

    class Meta:
        table_name = 'SceneCharacters'
        database = db


db.connect()


class SqlClient:

    def fetch_novel(self) -> Novel:
        novel_model = NovelModel.select()[0]

        characters: List[Character] = []
        for char_m in novel_model.characters:
            characters.append(
                Character(id=char_m.character.id, name=char_m.character.name, avatar=char_m.character.avatar))

        story_lines: List[StoryLine] = []
        for story_m in novel_model.story_lines:
            story_lines.append(StoryLine(id=story_m.id, text=story_m.text))

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
            day = scene_m.day if scene_m.day else 0
            end_event = scene_m.end_event if scene_m.end_event else True
            scenes.append(Scene(id=scene_m.id, title=scene_m.title, synopsis=scene_m.synopsis, type=scene_m.type,
                                pivotal=scene_m.pivotal == '1', sequence=scene_m.sequence, beginning=scene_m.beginning,
                                middle=scene_m.middle, end=scene_m.end, wip=scene_m.wip, day=day,
                                end_event=end_event, characters=scene_characters, pov=pov,
                                story_lines=scene_story_lines))

        scenes = sorted(scenes, key=lambda x: x.sequence)
        novel: Novel = Novel(id=novel_model.id, title=novel_model.title, scenes=scenes, characters=characters,
                             story_lines=story_lines)

        return novel

    def insert_character(self, novel: Novel, character: Character):
        character_m = CharacterModel.create(name=character.name, avatar=character.avatar)
        character.id = character_m.id

        novel_m = NovelModel.get(id=novel.id)
        NovelCharactersModel.create(novel=novel_m, character=character_m)

    def delete_character(self, character: Character):
        character_m = CharacterModel.get(id=character.id)
        character_m.delete_instance()

    def update_scene(self, scene: Scene):
        scene_m = SceneModel.get_by_id(scene.id)
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

        scene_m.save()

        self._update_scene_characters(scene)
        self._update_scene_story_lines(scene)

    def insert_scene(self, novel: Novel, scene: Scene):
        scene_m = SceneModel.create(title=scene.title, synopsis=scene.synopsis, type=scene.type,
                                    pivotal=scene.pivotal, sequence=scene.sequence, beginning=scene.beginning,
                                    middle=scene.middle, end=scene.end, novel=novel.id, wip=scene.wip,
                                    end_event=scene.end_event, day=scene.day)
        scene.id = scene_m.id

        self._update_scene_characters(scene)
        self._update_scene_story_lines(scene)

    def _update_scene_story_lines(self, scene):
        scene_m = SceneModel.get_by_id(scene.id)
        for story_line in scene_m.story_lines:
            story_line.delete_instance()

        for story_line in scene.story_lines:
            SceneStoryLinesModel.create(story_line=story_line.id, scene=scene.id)

    def _update_scene_characters(self, scene):
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

    def replace_scene_events(self, novel: Novel, scene: Scene, events: List[Event]):
        return
        # raise ValueError('not implemented')
        # query = QSqlQuery(f"DELETE FROM Events WHERE scene_id={scene.id}")
        # query.exec()
        #
        # query = QSqlQuery()
        # query.prepare("INSERT INTO Events (event, day, novel_id, scene_id) VALUES (?, ?, ?, ?)")
        # for event in events:
        #     query.addBindValue(event.event)
        #     query.addBindValue(event.day)
        #     query.addBindValue(novel.id)
        #     query.addBindValue(scene.id)
        #     result = query.exec()
        #     if not result:
        #         print(query.lastError().text())


client = SqlClient()
