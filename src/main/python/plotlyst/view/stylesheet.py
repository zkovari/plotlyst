"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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
APP_STYLESHEET = '''

* {
    icon-size: 20px;
}

QPushButton {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #f6f7fa, stop: 1 #dadbde);
    border: 2px solid #8f8f91;
    border-radius: 6px;
    padding: 2px;
    min-width: 60px;
}

QPushButton:hover {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #c3c4c7, stop: 1 #f6f7fa);
}

QPushButton:pressed {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #d7d8db, stop: 1 #f6f7fa);
}

QPushButton:disabled {
    opacity: 0.65;
}

QPushButton[positive=true]:!disabled {
    background-color: #2ecc71;
    color: #fff;
    font: bold;
}

QPushButton[positive=true]:hover {
    background-color: #27ae60;
}

QPushButton[deconstructive=true]:!disabled {
    background-color: #e74c3c;
    color: #fff;
    font: bold;
}

QPushButton[deconstructive=true]:hover {
    background-color: #c0392b;
}

QDockWidget::float-button {
    subcontrol-position: top left;
    subcontrol-origin: margin;
    position: absolute;
    top: 0px; left: 4px; bottom: 0px;
    width: 16px;
}

QHeaderView::section {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #2177b0, stop: 0.5 #185b87,
                                      stop: 0.6 #124669, stop:1 #1d608c);
    color: white;
    padding-left: 4px;
    border: 1px solid #6c6c6c;
    border-radius: 6px;
    font-size: 16px;
    font: bold;
}

QToolBar {
    spacing: 1px;
}

'''
