import nltk

from src.main.python.plotlyst.core.text import wc, sentence_count

nltk.download('punkt')


def test_wc():
    assert wc('Simple sentence with five words.') == 5
    assert wc('Do not count - characters.') == 4
    assert wc("Four words's 1 sentence.") == 4
    assert wc('What about French ?') == 3
    assert wc('') == 0
    assert wc('I-I don’t know.') == 3
    assert wc('one-word') == 1
    assert wc('8 a.m.') == 2


def test_sentence_count():
    assert sentence_count("One sentence. Two sentence.") == 2
    assert sentence_count('') == 0
    assert sentence_count(""""Hello," said John. Then he grabbed the torch.""") == 2
    assert sentence_count("This is...just ellipses.") == 2
    assert sentence_count("This is...Just what is it?") == 2
    assert sentence_count("This is... I just don't know") == 2
    assert sentence_count("Without punctuation") == 1
    assert sentence_count("“No, too many quotation marks I’m afraid.”") == 1
    assert sentence_count("At 8 a.m. then we shall meet.") == 1
    assert sentence_count("At 8 a.m., then we shall meet.") == 1
    assert sentence_count('"No but."') == 1
    assert sentence_count('A') == 1
    assert sentence_count('Sentence (with comment inside). Then another sentence') == 2
    assert sentence_count('Too many dots.. .') == 1
    assert sentence_count('Tab      sentence.') == 1
    assert sentence_count('Mr. Anderson. Hello.') == 2
    assert sentence_count('Dr. Anderson. Hello.') == 2
    assert sentence_count('Hello John F. Kennedy. This is my second sentence.') == 2
