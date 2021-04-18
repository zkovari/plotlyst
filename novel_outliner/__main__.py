import sys

from PyQt5 import QtWidgets

from novel_outliner.view.main_window import MainWindow

if __name__ == '__main__':
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()

    window.show()
    exit_code = app.exec()
