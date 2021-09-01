from src.main.python.plotlyst.test.common import show_widget
from src.main.python.plotlyst.view.widget.input import RichTextEditor


def test_rich_text_editor(qtbot):
    editor = RichTextEditor()
    show_widget(qtbot, editor)

    editor.btnBold.setChecked(True)

    editor.cbHeading.setCurrentIndex(1)

    qtbot.keyClicks(editor.textEditor, 'Test text')
