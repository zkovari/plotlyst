from unittest.mock import create_autospec

from PyQt5 import QtCore
from PyQt5.QtGui import QMouseEvent

from src.main.python.plotlyst.core.domain import ProfileTemplate
from src.main.python.plotlyst.view.dialog.template import CharacterProfileEditorDialog


def new_diag(qtbot, template: ProfileTemplate) -> CharacterProfileEditorDialog:
    diag = CharacterProfileEditorDialog(template)
    qtbot.addWidget(diag)
    diag.show()
    qtbot.waitExposed(diag, timeout=5000)

    return diag


def drop(qtbot, diag: CharacterProfileEditorDialog):
    qtbot.mouseMove(diag.wdgEditor)
    qtbot.mouseRelease(diag.wdgEditor, QtCore.Qt.LeftButton, delay=15)


def test_empty_template_dialog(qtbot):
    template = ProfileTemplate(title='Test Template')
    diag = new_diag(qtbot, template)

    assert diag.lineName.text() == template.title

    diag._dragged = diag.btnFear
    event = create_autospec(QMouseEvent)
    event.pos.side_effect = lambda: diag.btnFear.pos()

    QtCore.QTimer.singleShot(40, lambda: drop(qtbot, diag))

    diag.mouseMoveEvent(event)
