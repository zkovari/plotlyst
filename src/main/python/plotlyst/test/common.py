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
from typing import Any

from PyQt5.QtCore import Qt, QPoint, QAbstractItemModel
from PyQt5.QtWidgets import QAbstractItemView, QLineEdit

from src.main.python.plotlyst.view.characters_view import CharactersView
from src.main.python.plotlyst.view.main_window import MainWindow
from src.main.python.plotlyst.view.novel_view import NovelView
from src.main.python.plotlyst.view.scenes_view import ScenesOutlineView


def click_on_item(qtbot, view: QAbstractItemView, row: int, column: int = 0, parent=None, modifier=Qt.NoModifier):
    position: QPoint = _get_position_or_fail(view, row, column, parent)
    qtbot.mouseClick(view.viewport(), Qt.LeftButton, pos=position, modifier=modifier)


def _get_position_or_fail(view: QAbstractItemView, row: int, column: int = 0, parent=None) -> QPoint:
    _assert_row_and_column(row, column)

    if parent:
        index = view.model().index(row, column, parent)
    else:
        index = view.model().index(row, column)
    assert index.isValid(), f'The given row and column do not not have a valid index. Row: {row}, column: {column}'

    return view.visualRect(index).center()


def _assert_row_and_column(row: int, column: int):
    assert row >= 0, f'Row must not be negative: {row}'
    assert column >= 0, f'Column must not be negative: {column}'


def assert_data(model: QAbstractItemModel, value: Any, row: int, column: int = 0, role: int = Qt.DisplayRole,
                parent=None):
    _assert_row_and_column(row, column)
    if parent:
        assert model.rowCount(parent) > row
    else:
        assert model.rowCount() > row

    if parent:
        assert model.data(model.index(row, column, parent),
                          role) == value, f'{model.data(model.index(row, column, parent), role)} != {value}'
    else:
        assert model.data(model.index(row, column),
                          role) == value, f'{model.data(model.index(row, column), role)} != {value}'


def create_character(qtbot, window: MainWindow, name: str):
    characters: CharactersView = window.characters_view
    window.btnCharacters.setChecked(True)

    characters.ui.btnNew.click()
    assert characters.editor

    click_on_item(qtbot, characters.editor.ui.tblGeneral, 0, 1)
    index = characters.editor.ui.tblGeneral.model().index(0, 1)
    editor = characters.editor.ui.tblGeneral.indexWidget(index)
    assert editor, "Editor should be open at position 0,1"
    assert isinstance(editor, QLineEdit)
    qtbot.keyClicks(editor, name)
    characters.editor.ui.tblGeneral.itemDelegate().commitData.emit(editor)
    characters.editor.ui.tblGeneral.itemDelegate().closeEditor.emit(editor)

    assert_data(characters.editor.ui.tblGeneral.model(), name, 0, 1)

    characters.editor.ui.btnClose.click()


def create_story_line(qtbot, window: MainWindow, text: str):
    novels: NovelView = window.novel_view
    window.btnNovel.setChecked(True)

    novels.ui.btnAdd.click()
    click_on_item(qtbot, novels.ui.lstStoryLines, 0)
    novels.ui.btnEdit.click()

    index = novels.ui.lstStoryLines.model().index(0, 0)
    editor = novels.ui.lstStoryLines.indexWidget(index)
    assert editor, "Editor should be open at position 0,0"
    assert isinstance(editor, QLineEdit)

    qtbot.keyClicks(editor, text)
    novels.ui.lstStoryLines.itemDelegate().commitData.emit(editor)
    novels.ui.lstStoryLines.itemDelegate().closeEditor.emit(editor)

    assert_data(novels.ui.lstStoryLines.model(), text, 0)


def start_new_scene_editor(window: MainWindow) -> ScenesOutlineView:
    scenes: ScenesOutlineView = window.scenes_outline_view
    window.btnScenes.setChecked(True)
    scenes.ui.btnNew.click()
    assert scenes.editor
    assert scenes.ui.stackedWidget.currentWidget() == scenes.ui.pageEditor
    return scenes
