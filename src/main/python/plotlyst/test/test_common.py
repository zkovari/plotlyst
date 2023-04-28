from src.main.python.plotlyst.common import camel_to_whitespace


def test_camel_to_whitespace():
    assert camel_to_whitespace('helloWorld') == 'hello World'
    assert camel_to_whitespace('theQuickBrownFox') == 'the Quick Brown Fox'
    assert camel_to_whitespace('oneTwoThree') == 'one Two Three'
    assert camel_to_whitespace('iAmAnExample') == 'i Am An Example'
    assert camel_to_whitespace('camelCaseIsCool') == 'camel Case Is Cool'
    assert camel_to_whitespace('') == ''
    assert camel_to_whitespace('not_camel_case') == 'not_camel_case'
    assert camel_to_whitespace('already whitespace separated') == 'already whitespace separated'
    assert camel_to_whitespace('snake_case_is_different') == 'snake_case_is_different'
