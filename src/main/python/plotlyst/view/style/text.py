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
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget

from plotlyst.common import RELAXED_WHITE_COLOR

label_style_description = """
    QLabel[description=true] {
        color: #8d99ae;
    }

    QLabel[description=true]:!enabled {
        color: #CED4DD;
    }
"""

label_style_error_night_mode = """
    QLabel[error=true] {
        color: #e76f51;
    }

    QLabel[night-mode=true] {
        color: #f8f9fa;
    }
"""

label_style_headings = """
    QLabel[h1=true] {
        font-size: 30pt;
    }

    QLabel[h2=true] {
        font-size: 20pt;
    }

    QLabel[h3=true] {
        font-size: 18pt;
    }

    QLabel[h4=true] {
        font-size: 16pt;
    }
    
    QLabel[h5=true] {
        font-size: 14pt;
    }
    
    QLabel[small-body=true] {
        font-size: 14pt;
    }
"""

# QTextBrowser styles
text_browser_styles = """
    QTextBrowser {
        background-color: #f8f9fa;
    }

    QTextBrowser[rounded=true] {
        border-radius: 6px;
        padding: 4px;
        border: 1px solid lightgrey;
    }
"""

# QLineEdit styles
line_edit_styles = """
    QLineEdit {
        background-color: #f8f9fa;
    }

    QLineEdit[white-bg=true] {
        background-color: #FcFcFc;
    }

    QLineEdit[rounded=true] {
        border-radius: 6px;
        padding: 4px;
        border: 1px solid lightgrey;
    }
    
    QLineEdit[transparent=true] {
        border: 0px;
        background-color: rgba(0, 0, 0, 0);
    }
"""

# QTextEdit styles
text_edit_styles = """
    QTextEdit {
        background-color: #f8f9fa;
    }

    QTextEdit[rounded=true] {
        border-radius: 6px;
        padding: 4px;
        border: 1px solid lightgrey;
    }

    QTextEdit[white-bg=true] {
        background-color: #FcFcFc;
    }

    QTextEdit[transparent=true] {
        border: 0px;
        background-color: rgba(0, 0, 0, 0);
    }

    QTextEdit[borderless=true] {
        border: 0px;
        background-color: #f8f9fa;
    }
"""

widget_styles_hint_widget = """
    HintWidget {
        border: 2px solid #7209b7;
        border-radius: 4px;
        background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #dec9e9);
    }
"""

style = "\n".join([
    label_style_description,
    label_style_error_night_mode,
    label_style_headings,
    text_browser_styles,
    line_edit_styles,
    text_edit_styles,
    widget_styles_hint_widget
])


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


def apply_text_color(editor: QWidget, color: QColor):
    palette = editor.palette()
    palette.setColor(QPalette.ColorRole.Text, color)
    color.setAlpha(125)
    palette.setColor(QPalette.ColorRole.PlaceholderText, color)
    editor.setPalette(palette)
