from src.main.python.plotlyst.core.template import positive_traits, negative_traits, default_character_profiles


def test_unique_traits():
    pos_traits_set = set(positive_traits)
    assert len(pos_traits_set) == len(positive_traits)

    neg_traits_set = set(negative_traits)
    assert len(neg_traits_set) == len(negative_traits)


def test_unique_template_ids():
    profiles = default_character_profiles()
    for prof in profiles:
        ids = set()
        for el in prof.elements:
            assert el.field.id
            assert str(el.field.id) not in ids
            ids.add(str(el.field.id))
