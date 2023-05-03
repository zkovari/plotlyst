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
APP_STYLESHEET = '''

* {
    icon-size: 20px;
}

QToolTip {
    border: 0px;
    font-size: 14pt;
    padding: 5px;
}

QPushButton[base=true] {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #f6f7fa, stop: 1 #dadbde);
    border: 2px solid #8f8f91;
    border-radius: 6px;
    padding: 2px;
}

QPushButton:hover[base=true] {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #c3c4c7, stop: 1 #f6f7fa);
}

QPushButton:pressed[base=true] {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #d7d8db, stop: 1 #f6f7fa);
    border: 2px solid darkGrey;
}

QPushButton:checked[base=true] {
    background-color: lightgrey;
}

QPushButton:disabled[base=true] {
    opacity: 0.65;
}

QPushButton[positive=true]:!disabled {
    background-color: #4B0763;
    border: 2px solid black;
    color: #fff;
    font: bold;
}

QPushButton[positive=true]:hover {
    background-color: #37065D;
}

QPushButton[highlighted=true]:!disabled {
    background-color: #071064;
    color: #fff;
    font: bold;
}

QPushButton[highlighted=true]:hover {
    background-color: #060F5D;
}

QPushButton[deconstructive=true]:!disabled {
    background-color: #EE8074;
    color: #fff;
    font: bold;
}

QPushButton[deconstructive=true]:hover {
    background-color: #c0392b;
}

QPushButton[transparent=true] {
    border: 0px;
    background-color: rgba(0, 0, 0, 0);
}

QToolButton::menu-indicator {
    width:0px;
}

QToolButton[transparent=true] {
    border: 0px;
    background-color: rgba(0, 0, 0, 0);
}

QToolButton[base=true] {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #f6f7fa, stop: 1 #dadbde);
    border: 1px solid #8f8f91;
    border-radius: 6px;
    padding: 2px;
}

QToolButton:hover[base=true] {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #c3c4c7, stop: 1 #f6f7fa);
}

QToolButton:pressed[base=true] {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #d7d8db, stop: 1 #f6f7fa);
}

QToolButton:checked[base=true] {
    background-color: lightgrey;
}

QToolButton:disabled[base=true] {
    opacity: 0.65;
}

QToolButton[transparent=true] {
    border: 0px;
    border-radius: 4px;
}

QToolButton:pressed[transparent=true] {
    border: 1px solid grey
}

QToolButton[transparent-circle-bg-on-hover] {
    border-radius: 12px;
    border: 1px hidden lightgrey;
    padding: 2px;
}
QToolButton::menu-indicator[transparent-circle-bg-on-hover] {
    width:0px;
}
QToolButton:hover[transparent-circle-bg-on-hover] {
    background: #EDEDED;
}
QToolButton:hover[transparent-circle-bg-on-hover][positive] {
    background: #d8f3dc;
}
QToolButton[transparent-circle-bg-on-hover][large] {
    border-radius: 18px;
    padding: 4px;
}

QHeaderView::section {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #D4B8E0, stop: 0.5 #4B0763,
                                      stop: 0.6 #4B0763, stop:1 #3C0764);
    color: white;
    padding-left: 4px;
    padding-bottom: 2px;
    border: 1px solid #3C0764;
    border-radius: 0px;
    font-size: 16px;
}

QToolBar {
    spacing: 1px;
}

QTreeView {
    background-color: rgb(244, 244, 244);
}

QTreeView::branch {
    background-color: rgb(244, 244, 244);
    border: 0px;
}

QTreeView::branch:selected {
    background-color: #D8D5D5;
    border: 0px;
}

QTreeView::branch:hover:!selected {
    background-color: #D8D5D5;
    border: 0px;
}

QTreeView::item:hover:!selected {
    background-color: #D8D5D5;
    border: 0px;
}

QTreeView::item:selected:active {
    background-color: #D8D5D5;
    color: black;
}

QTreeView::item:selected:!active {
    background-color: #D8D5D5;
    color: black;
}

QTabWidget::pane {
    border: 1px solid black;
    background: white;
}

QTabWidget::tab-bar:top {
    top: 1px;
}

QTabWidget::tab-bar:bottom {
    bottom: 1px;
}

QTabWidget::tab-bar:left {
    right: 1px;
}

QTabWidget::tab-bar:right {
    left: 1px;
}

QTabBar::tab {
    border: 1px solid black;
}

QTabBar::tab:selected {
    background: white;
}

QTabBar::tab:!selected {
    background: lightGrey;
}

QTabBar::tab:!selected:hover {
    background: #999;
}

QTabBar::tab:top:!selected {
    margin-top: 3px;
}

QTabBar::tab:bottom:!selected {
    margin-bottom: 3px;
}

QTabBar::tab:top, QTabBar::tab:bottom {
    margin-right: -1px;
    padding: 5px 10px 5px 10px;
}

QTabBar::tab:top:selected {
    border-bottom-color: none;
}

QTabBar::tab:bottom:selected {
    border-top-color: none;
}

QTabBar::tab:top:last, QTabBar::tab:bottom:last,
QTabBar::tab:top:only-one, QTabBar::tab:bottom:only-one {
    margin-right: 0;
}

QTabBar::tab:left:!selected {
    margin-right: 3px;
}

QTabBar::tab:right:!selected {
    margin-left: 3px;
}

QTabBar::tab:left, QTabBar::tab:right {
    min-height: 8ex;
    margin-bottom: -1px;
    padding: 10px 5px 10px 5px;
}

QTabBar::tab:left:selected {
    border-left-color: none;
}

QTabBar::tab:right:selected {
    border-right-color: none;
}

QTabBar::tab:left:last, QTabBar::tab:right:last,
QTabBar::tab:left:only-one, QTabBar::tab:right:only-one {
    margin-bottom: 0;
}


QSlider::groove:horizontal {
    border: 1px solid #999999;
    height: 6px; /* the groove expands to the size of the slider by default. by giving it a height, it has a fixed size */
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
    margin: 0px 0;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4B0763, stop:1 #4B0763);
    border: 1px solid #4B0763;
    width: 15px;
    margin: -3px -1px;
    border-radius: 3px;
}


.QWidget[white-bg] {
    background-color: white;
}

.QWidget[relaxed-white-bg] {
    background-color: #f8f9fa;
}

.QFrame[relaxed-white-bg] {
    background-color: #f8f9fa;
}

QDialog[relaxed-white-bg] {
    background-color: #f8f9fa;
}

QTextBrowser {
    background-color: #f8f9fa;
}
'''
