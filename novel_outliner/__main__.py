import os
import subprocess
import sys

from fbs_runtime.application_context.PyQt5 import ApplicationContext

from novel_outliner.common import EXIT_CODE_RESTART
from novel_outliner.event.handler import exception_handler
from novel_outliner.view.main_window import MainWindow
from novel_outliner.view.stylesheet import APP_STYLESHEET

if __name__ == '__main__':
    appctxt = ApplicationContext()
    while True:
        app = appctxt.app
        window = MainWindow()
        app.setStyleSheet(APP_STYLESHEET)

        window.show()
        sys.excepthook = exception_handler  # type: ignore
        exit_code = appctxt.app.exec_()
        if exit_code < EXIT_CODE_RESTART:
            break

        # restart process
        subprocess.call('./gen.sh')
        python = sys.executable
        os.execl(python, python, *sys.argv)
