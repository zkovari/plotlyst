from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel


def test_insert_novel(test_client):
    novel = Novel(title='test1')
    client.insert_novel(novel)
    assert novel.id

    novels = client.novels()
    assert novel in novels


def test_delete_novel(test_client):
    novels = client.novels()
    assert len(novels) == 1
    assert novels[0].id == 1

    client.delete_novel(novels[0])

    assert not client.novels()


def test_has_novel(test_client):
    novel = Novel(title='test1')
    client.insert_novel(novel)

    assert client.has_novel(novel.id)
    assert not client.has_novel(99)
