from plotlyst.view.main_window import MainWindow


def _prepare_test(qtbot, main_window):
    main_window.show()
    qtbot.addWidget(main_window)
    qtbot.waitExposed(main_window, timeout=5000)


def test_main_window_is_initialized(qtbot, test_client):
    main_window = MainWindow()
    _prepare_test(qtbot, main_window)

    assert main_window
