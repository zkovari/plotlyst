"""
Plotlyst
Copyright (C) 2021-2023  Zsolt Kovari

This file is part of Plotlyst.

Plotlyst is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Plotlyst is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from PyQt6.QtWidgets import QWidget

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR

style = '''
QLabel[description=true] {
    color: #8d99ae;
}

QTextBrowser {
    background-color: #f8f9fa;
}

QLineEdit {
    background-color: #f8f9fa;
}

QTextEdit {
    background-color: #f8f9fa;
}

QLabel[night-mode=true] {
    color: #f8f9fa;
}

HintWidget {
    border: 2px solid #7209b7;
    border-radius: 4px;
    background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                          stop: 0 #dec9e9);
}

QTextEdit[transparent=true] {
    border: 0px;
    background-color: rgba(0, 0, 0, 0);
}

QLineEdit[transparent=true] {
    border: 0px;
    background-color: rgba(0, 0, 0, 0);
}

'''


def apply_texteditor_toolbar_style(widget: QWidget):
    widget.setStyleSheet(f'''
                            QFrame {{
                                background-color: {RELAXED_WHITE_COLOR};
                            }}

                            QToolButton {{
                                border: 1px hidden black;
                            }}
                            QToolButton:checked {{
                                background-color: #ced4da;
                            }}
                            QToolButton:hover:!checked {{
                                background-color: #e5e5e5;
                            }}
                        ''')
