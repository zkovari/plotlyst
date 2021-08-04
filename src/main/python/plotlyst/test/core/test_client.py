from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel, Scene


def test_insert_novel(test_client):
    novel = Novel(title='test1')
    client.insert_novel(novel)
    assert novel.id

    novels = client.novels()
    persisted_novel = client.fetch_novel(novels[0].id)
    assert novel == persisted_novel


def test_delete_novel(test_client):
    novel = Novel(title='test1')
    client.insert_novel(novel)
    novels = client.novels()
    assert len(novels) == 1

    client.delete_novel(novels[0])

    assert not client.novels()


def test_has_novel(test_client):
    novel = Novel(title='test1')
    client.insert_novel(novel)

    assert client.has_novel(novel.id)
    assert not client.has_novel(99)


def test_insert_scene(test_client):
    novel = Novel(title='test1')
    client.insert_novel(novel)

    scene = Scene(title='Scene 1', synopsis='Test synopsis', type='action', wip=True, beginning='Beginning',
                  middle='Middle', end='End', action_resolution=True, without_action_conflict=True,
                  stage=novel.stages[1])
    novel.scenes.append(scene)
    client.insert_scene(novel, scene)

    saved_novel = client.fetch_novel(novel.id)
    assert novel == saved_novel
    assert scene == novel.scenes[0]
