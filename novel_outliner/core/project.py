from novel_outliner.core.client import client
from novel_outliner.core.domain import Novel


class ProjectFinder:

    def __init__(self):
        self._novel = client.fetch_novel()

    @property
    def novel(self) -> Novel:
        return self._novel

    # def _persist_to_db(self):
    #     con = QSqlDatabase.addDatabase("QSQLITE")
    #     con.setDatabaseName("/home/zkovari/novels/novels.sqlite")
    #
    #     if not con.open():
    #         return print("Unable to connect to the database")
    #     chars_query = QSqlQuery("SELECT id, name FROM Characters")
    #     while chars_query.next():
    #         for char in self.novel.characters:
    #             if not char.image_path:
    #                 continue
    #             if char.name == chars_query.value(1):
    #                 pixmap = avatars.pixmap(char)
    #                 array = QByteArray()
    #                 buffer = QBuffer(array)
    #                 buffer.open(QIODevice.WriteOnly)
    #                 pixmap.save(buffer, 'JPEG')
    #
    #                 update_query = QSqlQuery()
    #                 update_query.prepare("UPDATE Characters SET avatar = :array WHERE id = :id")
    #                 update_query.bindValue(':id', chars_query.value(0))
    #                 update_query.bindValue(':array', array)
    #                 result = update_query.exec()
    #                 if not result:
    #                     print(update_query.lastError().text())

    # insert_query = QSqlQuery()
    # insert_query.prepare(
    #     """
    #     INSERT INTO SceneCharacters (
    #         scene_id,
    #         character_id,
    #         type
    #     )
    #     VALUES (?, ?, ?)
    #     """
    # )
    # # chars_query = QSqlQuery("SELECT id, name FROM Characters")
    # scenes_query = QSqlQuery("SELECT id, title FROM Scenes")
    # while scenes_query.next():
    #     scene_id = scenes_query.value(0)
    #     title = scenes_query.value(1)
    #     for s in self.novel.scenes:
    #         if s.title == title:
    #             chars_query = QSqlQuery("SELECT id, name FROM Characters")
    #             while chars_query.next():
    #                 char_name = chars_query.value(1)
    #                 if s.pov.name == char_name:
    #                     print(f'pov match {char_name} in scene {s.title}')
    #                     insert_query.addBindValue(scene_id)
    #                     insert_query.addBindValue(chars_query.value(0))
    #                     insert_query.addBindValue('pov')
    #                     insert_query.exec()
    #                     # chars_query.clear()
    #                 elif char_name in [x.name for x in s.characters]:
    #                     print(f'active match {char_name} in scene {s.title}')
    #                     insert_query.addBindValue(scene_id)
    #                     insert_query.addBindValue(chars_query.value(0))
    #                     insert_query.addBindValue('active')
    #                     insert_query.exec()

    # query = QSqlQuery()
    # query.prepare(
    #     """
    #     INSERT INTO Scenes (
    #         title,
    #         novel_id,
    #         type,
    #         synopsis,
    #         pivotal,
    #         wip
    #     )
    #     VALUES (?, ?, ?, ?, ?, ?)
    #     """
    # )
    # for scene in self.novel.scenes:
    #     query.addBindValue(scene.title)
    #     query.addBindValue(1)
    #     query.addBindValue(scene.type)
    #     query.addBindValue(scene.synopsis)
    #     query.addBindValue(scene.pivotal)
    #     query.addBindValue(scene.wip)
    #     query.exec()
