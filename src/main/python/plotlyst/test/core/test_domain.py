from typing import Set

from src.main.python.plotlyst.core.domain import default_story_structures


def test_unique_story_structures():
    structures = default_story_structures

    structure_ids: Set[str] = set()
    beat_ids: Set[str] = set()
    for structure in structures:
        assert structure.title
        assert not structure.custom
        assert str(structure.id) not in structure_ids
        structure_ids.add(str(structure.id))

        act = 1

        for beat in structure.beats:
            assert beat.text
            assert beat.act == act
            assert beat.act
            assert str(beat.id) not in beat_ids
            beat_ids.add(str(beat.id))

            if beat.ends_act:
                act += 1
