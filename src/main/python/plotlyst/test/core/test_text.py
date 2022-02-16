from src.main.python.plotlyst.core.domain import SceneBuilderElement, SceneBuilderElementType
from src.main.python.plotlyst.core.text import generate_text_from_scene_builder, wc, sentence_count


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


def test_wc():
    text = 'Simple sentence with five words.'
    assert wc(text) == 5

    text = 'Do not count - characters.'
    assert wc(text) == 4

    text = "Four words's 1 sentence."
    assert wc(text) == 4

    text = 'What about French ?'
    assert wc(text) == 3

    text = ''
    assert wc(text) == 0

    text = 'I-I don’t know.'
    assert wc(text) == 3


def test_sentence_count():
    text = """One sentence. Two sentence."""
    assert sentence_count(text) == 2

    text = ""
    assert sentence_count(text) == 0

    text = """
    "Hello," said John. Then he grabbed the torch.
    """
    assert sentence_count(text) == 2

    text = "This is...just ellipses."
    assert sentence_count(text) == 2

    text = "“No, not enough I’m afraid.”"
    assert sentence_count(text) == 1
