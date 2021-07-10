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
from PyQt5.QtSql import QSqlQuery

from plotlyst.core.domain import Novel


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
