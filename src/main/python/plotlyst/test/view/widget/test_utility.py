from src.main.python.plotlyst.test.common import show_widget, click_on_item
from src.main.python.plotlyst.view.widget.utility import IconSelectorWidget


def test_icon_picker(qtbot):
    icon_selector = IconSelectorWidget()
    show_widget(qtbot, icon_selector)

    assert icon_selector.model.rowCount()
    click_on_item(qtbot, icon_selector.lstIcons, 0)
