from plotlyst.test.common import show_widget, click_on_item
from plotlyst.view.widget.utility import IconSelectorWidget


def test_icon_picker(qtbot):
    icon_selector = IconSelectorWidget()
    show_widget(qtbot, icon_selector)

    assert icon_selector.model.rowCount()
    click_on_item(qtbot, icon_selector.lstIcons, 0)

    icon_selector.btnFood.click()

    icon_selector.lineFilter.setText('cat')
    assert icon_selector.btnAll.isChecked()
