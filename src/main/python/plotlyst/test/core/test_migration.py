# def test_schema_version(test_client):
#     version: AppDbSchemaVersion = app_db_schema_version()
#     assert version.up_to_date
#     assert version.revision == LATEST
#
#
# def test_old_schema_version(test_client):
#     m = ApplicationModel.get_by_id(1)
#     m.revision = LATEST.value - 1
#     m.save()
#
#     version: AppDbSchemaVersion = app_db_schema_version()
#     assert not version.up_to_date
#     assert version.revision != LATEST
#
#
# def test_migration_from_rev2(tmp_path):
#     shutil.copyfile(sys.path[0] + '/resources/rev-2.sqlite', tmp_path.joinpath('novels.sqlite'))
#     context.init(tmp_path)
#
#     version: AppDbSchemaVersion = app_db_schema_version()
#     assert version.revision == ApplicationDbVersion.R2
#
#     migration = Migration()
#     migration.migrate(context.db(), version)
#
#     version = app_db_schema_version()
#     assert version.revision == LATEST
