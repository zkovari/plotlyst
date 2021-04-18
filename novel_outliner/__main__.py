import os
import sys

from PyQt5 import QtWidgets

from novel_outliner.common import EXIT_CODE_RESTART
from novel_outliner.view.main_window import MainWindow

if __name__ == '__main__':
    while True:
        app = QtWidgets.QApplication.instance()
        if not app:
            app = QtWidgets.QApplication(sys.argv)
        window = MainWindow()

        window.show()
        exit_code = app.exec()
        if exit_code < EXIT_CODE_RESTART:
            break

        # restart process
        python = sys.executable
        os.execl(python, python, *sys.argv)
