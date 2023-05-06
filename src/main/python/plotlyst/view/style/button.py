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

style = '''
QPushButton::menu-indicator[no-menu] {
    width:0px;
}

QPushButton[base=true] {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #f6f7fa, stop: 1 #dadbde);
    border: 2px solid #8f8f91;
    border-radius: 6px;
    padding: 2px;
}

QPushButton[large=true] {
    font-size: 24px;
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

QPushButton[secondary-field-attribute=true] {
    border: 1px hidden black;
    border-radius: 6px;
    color: #343a40;
    padding: 2px;
}

QPushButton[top-level-nav=true] {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #89c2d9);
    border: 2px solid #2c7da0;
    border-radius: 6px;
    color: white;
    padding: 2px;
    font: bold;
}
QPushButton:disabled[top-level-nav=true] {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                          stop: 0 lightGray);
    border: 2px solid grey;
    color: grey;
    opacity: 0.45;
}
QPushButton:checked[top-level-nav=true] {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                          stop: 0 #014f86);
    border: 2px solid #013a63;
}

QPushButton[main-side-nav=true] {
    border: 0px;
    padding: 5px;
    padding-top: 6px;
    padding-bottom: 6px;
}
QPushButton:hover[main-side-nav=true] {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 0,
                              stop: 0 #d7e3fc);
    border: 1px hidden black;
}
QPushButton:checked[main-side-nav=true] {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 0,
                          stop: 0 #4e4187);
    border: 1px solid #9BB8F7;
    color: white;
}

QToolButton::menu-indicator {
    width:0px;
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
    background-color: rgba(0, 0, 0, 0);
    border-radius: 4px;
}

QToolButton[transparent-clickable=true] {
    border: 0px;
    background-color: rgba(0, 0, 0, 0);
    border-radius: 4px;
}

QToolButton:pressed[transparent-clickable=true] {
    border: 1px solid grey;
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

QToolButton:checked[emotion-very-unhappy] {
    background-color: rgb(239, 0, 0);
}

QToolButton:hover[emotion-very-unhappy] {
    border: 1px solid rgb(239, 0, 0);
}

QToolButton:checked[emotion-unhappy] {
    background-color: rgb(255, 142, 43);
}

QToolButton:hover[emotion-unhappy] {
    border: 1px solid rgb(255, 142, 43);
}

QToolButton::checked[emotion-neutral] {
    background-color: rgb(171, 171, 171);
}

QToolButton:hover[emotion-neutral] {
    border: 1px solid rgb(171, 171, 171);
}

QToolButton:checked[emotion-happy] {
    background-color: #93e5ab;
}

QToolButton:hover[emotion-happy] {
    border: 1px solid #93e5ab;
}

QToolButton:checked[emotion-very-happy] {
    background-color: rgb(0, 202, 148);
}

QToolButton:hover[emotion-very-happy] {
    border: 1px solid rgb(0, 202, 148);
}

'''