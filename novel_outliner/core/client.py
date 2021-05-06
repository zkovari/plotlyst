import logging
from typing import List

from PyQt5.QtSql import QSqlDatabase, QSqlQuery

from novel_outliner.core.domain import Novel, Character, Scene


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

        novel.characters.extend(client.fetch_characters())
        novel.scenes.extend(client.fetch_scenes())

        return novel

    def fetch_characters(self) -> List[Character]:
        characters_query = QSqlQuery("SELECT id, name FROM Characters")
        characters = []
        while characters_query.next():
            characters.append(Character(id=characters_query.value(0), name=characters_query.value(1)))
        return characters

    def fetch_scenes(self) -> List[Scene]:
        scenes_query = QSqlQuery("SELECT id, title, synopsis, type, pivotal, wip, beginning, middle, end FROM Scenes")
        scenes = []
        while scenes_query.next():
            scene = Scene(id=scenes_query.value(0), title=scenes_query.value(1), synopsis=scenes_query.value(2),
                          type=scenes_query.value(3),
                          pivotal=scenes_query.value(4) == '1', wip=scenes_query.value(5),
                          beginning=scenes_query.value(6), middle=scenes_query.value(7), end=scenes_query.value(8))
            scenes.append(scene)

        characters = self.fetch_characters()
        for scene in scenes:
            scene_characters_query = QSqlQuery(
                f"SELECT character_id, type FROM SceneCharacters where scene_id = {scene.id}")
            while scene_characters_query.next():
                id = scene_characters_query.value(0)
                type = scene_characters_query.value(1)
                match = [x for x in characters if x.id == id]
                if match:
                    if type == 'pov':
                        scene.pov = match[0]
                        scene.characters.append(match[0])
                    elif type == 'active':
                        scene.characters.append(match[0])
        return scenes

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

    def insert_scene(self, novel: Novel, scene: Scene) -> int:
        scenes_query = QSqlQuery()
        scenes_query.prepare(
            "INSERT INTO Scenes (title, novel_id, type, synopsis, pivotal, beginning, middle, end) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
        scenes_query.addBindValue(scene.title)
        scenes_query.addBindValue(novel.id)
        scenes_query.addBindValue(scene.type)
        scenes_query.addBindValue(scene.synopsis)
        scenes_query.addBindValue(scene.pivotal)
        scenes_query.addBindValue(scene.beginning)
        scenes_query.addBindValue(scene.middle)
        scenes_query.addBindValue(scene.end)
        scenes_query.exec()
        id = scenes_query.lastInsertId()

        char_scenes_query = QSqlQuery()
        char_scenes_query.prepare('INSERT INTO SceneCharacters (scene_id, character_id, type) VALUES (?, ?, ?)')
        if scene.pov:
            char_scenes_query.addBindValue(id)
            char_scenes_query.addBindValue(scene.pov.id)
            char_scenes_query.addBindValue('pov')
            char_scenes_query.exec()
        for char in scene.characters:
            char_scenes_query.addBindValue(id)
            char_scenes_query.addBindValue(char.id)
            char_scenes_query.addBindValue('active')
            char_scenes_query.exec()

        return id

    def delete_scene(self, scene: Scene):
        query = QSqlQuery()
        query.prepare('DELETE FROM Scenes WHERE id = :id')
        query.bindValue(':id', scene.id)
        query.exec()


client = SqlClient()
