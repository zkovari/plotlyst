from src.main.python.plotlyst.core.domain import SceneBuilderElement, SceneBuilderElementType
from src.main.python.plotlyst.core.text import generate_text_from_scene_builder


def test_generate_text_from_scene_builder():
    elements = [SceneBuilderElement(SceneBuilderElementType.SIGHT, 'Saw something'),
                SceneBuilderElement(SceneBuilderElementType.REACTION, '',
                                    children=[SceneBuilderElement(SceneBuilderElementType.FEELING, 'Feeling.'),
                                              SceneBuilderElement(SceneBuilderElementType.REFLEX, 'Reflex'),
                                              SceneBuilderElement(SceneBuilderElementType.MONOLOG,
                                                                  'Monolog and question?'),
                                              SceneBuilderElement(SceneBuilderElementType.SPEECH, 'Speech')
                                              ]),

                ]
    text: str = generate_text_from_scene_builder(elements)
    expected_text = '''Saw something.
Feeling. Reflex. Monolog and question?
"Speech"'''
    assert text == expected_text
