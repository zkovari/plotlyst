import logging
from typing import List

from PyQt5.QtSql import QSqlDatabase, QSqlQuery

from novel_outliner.core.domain import Novel, Character, Scene, StoryLine, Event


class SqlClient:
    def __init__(self):
        con = QSqlDatabase.addDatabase("QSQLITE")
        con.setDatabaseName("/home/zkovari/novels/novels.sqlite")

        if not con.open():
            logging.error("Unable to connect to the database")

    def fetch_novel(self) -> Novel:
        novels_query = QSqlQuery("SELECT id, title FROM Novels")
        novels_query.first()
        novel = Novel(id=novels_query.value(0), title=novels_query.value(1))

        novel.characters.extend(self.fetch_characters())
        novel.story_lines.extend(self.fetch_story_lines(novel))
        novel.scenes.extend(self.fetch_scenes(novel))
        novel.events.extend(self.fetch_events(novel))

        return novel

    def fetch_characters(self) -> List[Character]:
        characters_query = QSqlQuery("SELECT id, name FROM Characters")
        characters = []
        while characters_query.next():
            characters.append(Character(id=characters_query.value(0), name=characters_query.value(1)))
        return characters

    def fetch_scenes(self, novel: Novel) -> List[Scene]:
        scenes_query = QSqlQuery(
            """
            SELECT id, title, synopsis, type, pivotal, wip, beginning, middle, end, sequence, end_event, day
            FROM Scenes
            """)
        scenes = []
        while scenes_query.next():
            day = scenes_query.value(11) if scenes_query.value(11) else 0
            end_event = scenes_query.value(10) if scenes_query.value(10) else True
            scene = Scene(id=scenes_query.value(0), title=scenes_query.value(1), synopsis=scenes_query.value(2),
                          type=scenes_query.value(3),
                          pivotal=scenes_query.value(4) == '1', wip=scenes_query.value(5),
                          beginning=scenes_query.value(6), middle=scenes_query.value(7), end=scenes_query.value(8),
                          sequence=scenes_query.value(9),
                          end_event=end_event,
                          day=day)
            scenes.append(scene)
        scenes = sorted(scenes, key=lambda x: x.sequence)

        for scene in scenes:
            scene_characters_query = QSqlQuery(
                f"SELECT character_id, type FROM SceneCharacters where scene_id = {scene.id}")
            while scene_characters_query.next():
                id = scene_characters_query.value(0)
                type = scene_characters_query.value(1)
                match = [x for x in novel.characters if x.id == id]
                if match:
                    if type == 'pov':
                        scene.pov = match[0]
                    elif type == 'active':
                        scene.characters.append(match[0])
            scene_story_lines_query = QSqlQuery(
                f"SELECT story_line_id FROM StoryLinesScenes where scene_id = {scene.id}")
            while scene_story_lines_query.next():
                id = scene_story_lines_query.value(0)
                match = [x for x in novel.story_lines if x.id == id]
                if match:
                    scene.story_lines.append(match[0])

        return scenes

    def fetch_story_lines(self, novel: Novel) -> List[StoryLine]:
        query = QSqlQuery(f'SELECT id, text FROM NovelStoryLines WHERE novel_id={novel.id}')
        story_lines: List[StoryLine] = []
        while query.next():
            story_lines.append(StoryLine(id=query.value(0), text=query.value(1)))
        return story_lines

    def fetch_events(self, novel: Novel) -> List[Event]:
        query = QSqlQuery(f'SELECT id, event, day FROM Events WHERE novel_id={novel.id}')
        events: List[Event] = []
        while query.next():
            events.append(Event(id=query.value(0), event=query.value(1), day=query.value(2)))
        return events

    def insert_character(self, character: Character):
        query = QSqlQuery()
        query.prepare('INSERT INTO Characters (name) VALUES (?)')
        query.addBindValue(character.name)
        query.exec()

    def delete_character(self, character: Character):
        query = QSqlQuery()
        query.prepare('DELETE FROM Characters WHERE id = :id')
        query.bindValue(':id', character.id)
        query.exec()

    def update_scene(self, scene: Scene):
        update_query = QSqlQuery()
        update_query.prepare(
            """
            UPDATE Scenes SET 
                title=:title, synopsis=:synopsis,
                wip=:wip, type=:type,
                pivotal=:pivotal, beginning=:beginning,
                middle=:middle, end=:end,
                end_event=:end_event, day=:day
            WHERE id = :id
            """)
        update_query.bindValue(':id', scene.id)
        update_query.bindValue(':title', scene.title)
        update_query.bindValue(':synopsis', scene.synopsis)
        update_query.bindValue(':type', scene.type)
        update_query.bindValue(':wip', scene.wip)
        update_query.bindValue(':pivotal', scene.pivotal)
        update_query.bindValue(':beginning', scene.beginning)
        update_query.bindValue(':middle', scene.middle)
        update_query.bindValue(':end', scene.end)
        update_query.bindValue(':end_event', scene.end_event)
        update_query.bindValue(':day', scene.day)
        result = update_query.exec()

        delete_scene_characters_query = QSqlQuery()
        delete_scene_characters_query.prepare("DELETE FROM SceneCharacters WHERE scene_id=:id")
        delete_scene_characters_query.bindValue(':id', scene.id)
        delete_scene_characters_query.exec()

        delete_scene_story_lines_query = QSqlQuery()
        delete_scene_story_lines_query.prepare("DELETE FROM StoryLinesScenes WHERE scene_id=:id")
        delete_scene_story_lines_query.bindValue(':id', scene.id)
        result = delete_scene_story_lines_query.exec()

        self._insert_scene_characters(scene)
        self._insert_scene_story_lines(scene)

    def insert_scene(self, novel: Novel, scene: Scene):
        scenes_query = QSqlQuery()
        scenes_query.prepare(
            """
            INSERT INTO Scenes (title, novel_id, type, synopsis, pivotal, 
                beginning, middle, end, end_event, day)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)
        scenes_query.addBindValue(scene.title)
        scenes_query.addBindValue(novel.id)
        scenes_query.addBindValue(scene.type)
        scenes_query.addBindValue(scene.synopsis)
        scenes_query.addBindValue(scene.pivotal)
        scenes_query.addBindValue(scene.beginning)
        scenes_query.addBindValue(scene.middle)
        scenes_query.addBindValue(scene.end)
        scenes_query.exec()
        scene.id = scenes_query.lastInsertId()

        self._insert_scene_characters(scene)
        self._insert_scene_story_lines(scene)

    def _insert_scene_characters(self, scene: Scene):
        char_scenes_query = QSqlQuery()
        char_scenes_query.prepare('INSERT INTO SceneCharacters (scene_id, character_id, type) VALUES (?, ?, ?)')
        if scene.pov:
            char_scenes_query.addBindValue(scene.id)
            char_scenes_query.addBindValue(scene.pov.id)
            char_scenes_query.addBindValue('pov')
            char_scenes_query.exec()
        for char in scene.characters:
            char_scenes_query.addBindValue(scene.id)
            char_scenes_query.addBindValue(char.id)
            char_scenes_query.addBindValue('active')
            char_scenes_query.exec()

    def _insert_scene_story_lines(self, scene: Scene):
        query = QSqlQuery()
        query.prepare('INSERT INTO StoryLinesScenes (scene_id, story_line_id) VALUES (?, ?)')

        for story_line in scene.story_lines:
            query.addBindValue(scene.id)
            query.addBindValue(story_line.id)
            query.exec()

    def delete_scene(self, scene: Scene):
        query = QSqlQuery()
        query.prepare('DELETE FROM Scenes WHERE id = :id')
        query.bindValue(':id', scene.id)
        query.exec()

    def replace_scene_events(self, novel: Novel, scene: Scene, events: List[Event]):
        query = QSqlQuery(f"DELETE FROM Events WHERE scene_id={scene.id}")
        query.exec()

        query = QSqlQuery()
        query.prepare("INSERT INTO Events (event, day, novel_id, scene_id) VALUES (?, ?, ?, ?)")
        for event in events:
            query.addBindValue(event.event)
            query.addBindValue(event.day)
            query.addBindValue(novel.id)
            query.addBindValue(scene.id)
            result = query.exec()
            if not result:
                print(query.lastError().text())


client = SqlClient()
