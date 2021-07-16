from plotlyst.view.dialog.about import AboutDialog


def test_about_dialog(qtbot):
    about = AboutDialog()
    qtbot.addWidget(about)
    about.show()
    qtbot.waitExposed(about, timeout=5000)
