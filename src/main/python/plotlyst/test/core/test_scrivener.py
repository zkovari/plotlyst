import sys
from pathlib import Path
from uuid import UUID

import pytest

from src.main.python.plotlyst.core.domain import Novel, Chapter, Scene
from src.main.python.plotlyst.core.scrivener import ScrivenerImporter


def test_empty_folder(tmp_path):
    importer = ScrivenerImporter()
    with pytest.raises(ValueError) as excinfo:
        importer.import_project(str(tmp_path))

        assert 'Could not find main Scrivener file with .scrivx extension under given folder' in str(excinfo)


def test_not_existing_input(tmp_path):
    importer = ScrivenerImporter()
    with pytest.raises(ValueError) as excinfo:
        importer.import_project(str(tmp_path.joinpath('not-existing-directory')))

        assert 'Input folder does not exist' in str(excinfo)


def test_import_with_acts(test_client):
    folder = Path(sys.path[0]).joinpath('resources/scrivener/v3/NovelWithParts')

    importer = ScrivenerImporter()
    novel: Novel = importer.import_project(str(folder))

    assert novel
    assert novel.chapters
    assert novel.scenes

    chapters = [Chapter(title='Chapter', id=UUID('58D0189B-0507-4669-B129-4A392CF07F36')),
                Chapter(title='Chapter', id=UUID('567B89D4-21E4-44DF-BD5C-3F32EEC78ADD')),
                Chapter(title='Chapter', id=UUID('245C2ABD-E9C1-4091-B1B7-DA32402644E7'))]
    scenes = [Scene(title='Scene 1', id=UUID('A9C97B44-46C8-4CA8-8F28-B8C0606A58EF'), chapter=chapters[0]),
              Scene(title='Scene 2', id=UUID('E6BBAC10-E639-4E86-A784-EDEEE7DF0206'), chapter=chapters[0]),
              Scene(title='Scene 3', id=UUID('2B5EF0AA-74AE-435D-98A6-096CEAF8F721'), chapter=chapters[0]),
              Scene(title='Scene', id=UUID('F5604565-3F9E-451B-98E0-142BE1BDE83D'), chapter=chapters[1]),
              Scene(title='Scene', id=UUID('156AAE33-5D68-4ACA-8469-6440CDFED4EA'), chapter=chapters[2])]
    expected_novel = Novel(title='Importer project', id=UUID('C4B3D990-B9C2-4FE6-861E-B06B498283A4'), chapters=chapters,
                           scenes=scenes, stages=novel.stages, story_structures=novel.story_structures)
    assert novel == expected_novel
