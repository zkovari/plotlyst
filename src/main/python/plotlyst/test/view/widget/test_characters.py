from src.main.python.plotlyst.test.common import show_widget
from src.main.python.plotlyst.view.widget.character.editor import CharacterRoleSelector


def test_role_selector(qtbot):
    widget = CharacterRoleSelector()
    show_widget(qtbot, widget)

    assert widget.btnItemProtagonist.isChecked()
    assert widget.stackedWidget.currentWidget() == widget.pageProtagonist
    assert widget.btnPromote.isHidden()

    widget.btnItemAntagonist.click()
    assert widget.stackedWidget.currentWidget() == widget.pageAntagonist
    assert widget.btnPromote.isHidden()

    widget.btnItemSecondary.click()
    assert widget.stackedWidget.currentWidget() == widget.pageSecondary
    assert widget.btnPromote.isVisible()

    widget.btnItemSidekick.click()
    assert widget.stackedWidget.currentWidget() == widget.pageSidekick
    assert widget.btnPromote.isHidden()

    widget.btnItemSupporter.click()
    assert widget.stackedWidget.currentWidget() == widget.pageSupporter
    assert widget.btnPromote.isHidden()

    widget.btnItemGuide.click()
    assert widget.stackedWidget.currentWidget() == widget.pageGuide
    assert widget.btnPromote.isHidden()

    widget.btnItemConfidant.click()
    assert widget.stackedWidget.currentWidget() == widget.pageConfidant
    assert widget.btnPromote.isHidden()

    widget.btnItemLoveInterest.click()
    assert widget.stackedWidget.currentWidget() == widget.pageLoveInterest
    assert widget.btnPromote.isVisible()

    widget.btnItemAdversary.click()
    assert widget.stackedWidget.currentWidget() == widget.pageAdversary
    assert widget.btnPromote.isHidden()

    widget.btnItemContagonist.click()
    assert widget.stackedWidget.currentWidget() == widget.pageContagonist
    assert widget.btnPromote.isVisible()

    widget.btnItemFoil.click()
    assert widget.stackedWidget.currentWidget() == widget.pageFoil
    assert widget.btnPromote.isVisible()

    widget.btnItemTertiary.click()
    assert widget.stackedWidget.currentWidget() == widget.pageTertiary
    assert widget.btnPromote.isHidden()

    widget.btnItemHenchmen.click()
    assert widget.stackedWidget.currentWidget() == widget.pageHenchmen
    assert widget.btnPromote.isHidden()
