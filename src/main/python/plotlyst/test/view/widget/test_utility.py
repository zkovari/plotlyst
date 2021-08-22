from src.main.python.plotlyst.test.common import show_widget
from src.main.python.plotlyst.view.widget.utility import IconSelectorWidget


def test_icon_picker(qtbot):
    icon_selector = IconSelectorWidget()
    show_widget(qtbot, icon_selector)

    assert icon_selector.model.rowCount()
