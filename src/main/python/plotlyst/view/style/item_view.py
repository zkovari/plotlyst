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

QHeaderView::section {
    background-color: #f8f9fa; border: 0px; color: black;
}

QHeaderView {
    background-color: #f8f9fa;
}

QTableView {
    background-color: #f8f9fa;
}

QTableView QTableCornerButton::section {
    background-color: #f8f9fa;
}

QHeaderView::section[main-header] {
    background: #622675;
    color: #f8f0fa;
    padding: 4px;
    border-right: 1px solid #f8f0fa;
    font-size: 16px;
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

'''
