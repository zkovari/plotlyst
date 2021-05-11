from typing import Optional

import qtawesome
from PyQt5.QtWidgets import QMessageBox


class ErrorMessageBox(QMessageBox):
    def __init__(self, msg: str, details: Optional[str] = None, warning: bool = False, parent=None):
        super().__init__(parent=parent)
        self.setText(msg)
        self.setWindowIcon(qtawesome.icon('fa5s.bomb'))

        if details:
            self.setDetailedText(details)
            for btn in self.buttons():
                if btn.text().startswith('Show Details'):
                    btn.click()

        if warning:
            self.setIcon(QMessageBox.Warning)
            self.setWindowTitle('Warning')
        else:
            self.setIcon(QMessageBox.Critical)
            self.setWindowTitle('Error')

    def display(self) -> int:
        return self.exec()
