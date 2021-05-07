# from PyQt5.QtSql import QSqlQuery

# con = QSqlDatabase.addDatabase("QSQLITE")
# con.setDatabaseName("/home/zkovari/novels/novels.sqlite")
#
# if not con.open():
#     print("Unable to connect to the database")
#     sys.exit(1)

# createTableQuery = QSqlQuery()
# createTableQuery.exec('drop table Characters')
# createTableQuery.exec('drop table Locations')
# createTableQuery.exec('drop table Scenes')
# createTableQuery.exec('drop table Novels')
# createTableQuery.exec('drop table Series')
# createTableQuery.exec('drop table NovelCharacters')
# result = createTableQuery.exec(
#     """
#     CREATE TABLE IF NOT EXISTS Characters (
#         id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
#         name TEXT NOT NULL
#     );
#     """
# )
# print(f' {result} Created characters table')
# result = createTableQuery.exec(
#     """
#     CREATE TABLE IF NOT EXISTS Locations (
#         id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
#         name TEXT NOT NULL
#     );
#     """
# )
# print(f' {result} Created locations table')
#
# result = createTableQuery.exec(
#     """
#     CREATE TABLE IF NOT EXISTS Series (
#         id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
#         title TEXT NOT NULL
#     );
#     """
# )
# print(f' {result} Created series table')
#
# result = createTableQuery.exec(
#     """
#     CREATE TABLE IF NOT EXISTS Novels (
#         id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
#         title TEXT NOT NULL,
#         genre TEXT,
#         blurb TEXT
#     );
#     """
# )
# print(f' {result} Created novels table')
#
# result = createTableQuery.exec(
#     """
#     CREATE TABLE IF NOT EXISTS Scenes (
#         id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
#         title TEXT NOT NULL,
#         novel_id INTEGER NOT NULL,
#         type TEXT,
#         synopsis TEXT,
#         time TEXT,
#         wip BOOLEAN,
#         pivotal TEXT,
#         draft_status TEXT,
#         edition_status TEXT,
#         FOREIGN KEY (novel_id)
#             REFERENCES Novels (id)
#                 ON DELETE CASCADE
#                 ON UPDATE NO ACTION
#     );
#     """
# )
# print(f' {result} Created scenes table')

# result = createTableQuery.exec(
#     """
#     CREATE TABLE IF NOT EXISTS SceneCharacters (
#         id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
#         scene_id INTEGER NOT NULL,
#         character_id INTEGER NOT NULL,
#         type TEXT,
#         FOREIGN KEY (scene_id)
#             REFERENCES Scenes (id)
#                 ON DELETE CASCADE
#                 ON UPDATE NO ACTION,
#         FOREIGN KEY (character_id)
#             REFERENCES Characters (id)
#                 ON DELETE CASCADE
#                 ON UPDATE NO ACTION
#     );
#     """
# )
# print(f' {result} Created SceneCharacters table')
