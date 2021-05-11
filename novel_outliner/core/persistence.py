from PyQt5.QtSql import QSqlQuery

from novel_outliner.core.domain import Novel


def emit_save(novel: Novel):
    raise ValueError('not implemented')
    scenes_query = QSqlQuery()
    scenes_query.prepare("""
        UPDATE Scenes SET 
            title=:title, synopsis=:synopsis,
            wip=:wip,
            sequence=:sequence
        WHERE id = :id
        """)

    for index, scene in enumerate(novel.scenes):
        scenes_query.bindValue(':id', scene.id)
        scenes_query.bindValue(':title', scene.title)
        scenes_query.bindValue(':synopsis', scene.synopsis)
        scenes_query.bindValue(':wip', scene.wip)
        scenes_query.bindValue(':sequence', index)
        scenes_query.exec()
