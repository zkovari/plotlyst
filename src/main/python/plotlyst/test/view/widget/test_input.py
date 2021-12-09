from src.main.python.plotlyst.test.common import show_widget
from src.main.python.plotlyst.view.widget.input import RichTextEditor, PowerBar


def test_rich_text_editor(qtbot):
    editor = RichTextEditor()
    show_widget(qtbot, editor)

    editor.actionBold.setChecked(True)

    editor.cbHeading.setCurrentIndex(1)

    qtbot.keyClicks(editor.textEditor, 'Test text')


def test_powerbar(qtbot):
    bar = PowerBar()
    show_widget(qtbot, bar)

    assert bar.value() == 0
    bar.btnMinus.click()
    assert bar.value() == 0

    bar.btnPlus.click()
    assert bar.value() == 1
