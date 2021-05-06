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
        scenes_query = QSqlQuery("SELECT id, title, synopsis, type, pivotal, wip FROM Scenes")
        scenes = []
        while scenes_query.next():
            scene = Scene(id=scenes_query.value(0), title=scenes_query.value(1), synopsis=scenes_query.value(2),
                          type=scenes_query.value(3),
                          pivotal=scenes_query.value(4) == '1', wip=scenes_query.value(5))
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


client = SqlClient()
