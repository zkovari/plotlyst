from PyQt5.QtSql import QSqlQuery

from novel_outliner.core.domain import Novel


def emit_save(novel: Novel):
    scenes_query = QSqlQuery()
    scenes_query.prepare("UPDATE Scenes SET title=:title, synopsis=:synopsis WHERE id = :id")

    for scene in novel.scenes:
        scenes_query.bindValue(':id', scene.id)
        scenes_query.bindValue(':title', scene.title)
        scenes_query.bindValue(':synopsis', scene.synopsis)
        scenes_query.exec()
