from src.main.python.plotlyst.core.client import client, json_client
from src.main.python.plotlyst.core.domain import Novel, Scene, SceneType, default_story_structures, three_act_structure, \
    SceneStoryBeat
from src.main.python.plotlyst.test.conftest import init_project


def test_insert_novel(test_client):
    novel = Novel(title='test1')
    client.insert_novel(novel)
    assert novel.id

    novels = client.novels()
    persisted_novel = client.fetch_novel(novels[0].id)
    novel.story_structures = [three_act_structure]
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
    novel = Novel(title='test1', story_structures=default_story_structures)
    novel.story_structures[0].active = True
    client.insert_novel(novel)

    scene = Scene(title='Scene 1', synopsis='Test synopsis', type=SceneType.ACTION, wip=True,
                  stage=novel.stages[1],
                  beats=[SceneStoryBeat.of(novel.active_story_structure, novel.active_story_structure.beats[0])])
    novel.scenes.append(scene)
    client.insert_scene(novel, scene)

    saved_novel = client.fetch_novel(novel.id)
    assert novel == saved_novel
    assert scene == novel.scenes[0]


def test_init_client(test_client):
    init_project()

    json_client.init(str(json_client.root_path))
