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
import math
from abc import abstractmethod
from typing import Union, List, Set

from PyQt5.QtCore import QSize, QModelIndex, Qt
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QFrame, QToolButton, QVBoxLayout, QMenu, QWidgetAction, \
    QSizePolicy

from src.main.python.plotlyst.common import truncate_string
from src.main.python.plotlyst.core.domain import Character, Conflict, ConflictType, SelectionItem
from src.main.python.plotlyst.model.common import SelectionItemsModel
from src.main.python.plotlyst.view.common import line
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog
from src.main.python.plotlyst.view.icons import set_avatar, IconRegistry, avatars
from src.main.python.plotlyst.view.layout import FlowLayout
from src.main.python.plotlyst.view.widget.items_editor import ItemsEditorWidget


class Label(QFrame):
    def __init__(self, parent=None):
        super(Label, self).__init__(parent)
        _layout = QHBoxLayout()
        _layout.setSpacing(2)
        _layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(_layout)


class LabelsWidget(QWidget):

    def __init__(self, parent=None):
        super(LabelsWidget, self).__init__(parent)
        self.setLayout(FlowLayout(margin=1, spacing=4))

    def addText(self, text: str, color: str = '#7c98b3'):
        label = QLabel(truncate_string(text, 40))
        rgb = QColor(color).getRgb()
        r = rgb[0]
        g = rgb[1]
        b = rgb[2]
        hsp = math.sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b))
        text_color = 'black' if hsp > 127.5 else 'white'
        label.setStyleSheet(
            f'''QLabel {{
                background-color: {color}; border-radius: 6px; color: {text_color};
                padding-left: 3px; padding-right: 3px;
            }}''')

        self.layout().addWidget(label)

    def addLabel(self, label: Union[Label, QLabel]):
        self.layout().addWidget(label)

    def clear(self):
        self.layout().clear()


class CharacterLabel(Label):
    def __init__(self, character: Character, pov: bool = False, parent=None):
        super(CharacterLabel, self).__init__(parent)
        self.character = character
        self.btnAvatar = QToolButton()
        self.btnAvatar.setStyleSheet('border: 0px;')
        self.btnAvatar.setIcon(QIcon(avatars.pixmap(self.character)))
        self.btnAvatar.setIconSize(QSize(24, 24))
        self.layout().addWidget(self.btnAvatar)
        self.layout().addWidget(QLabel(truncate_string(character.name)))

        role = self.character.role()
        if role:
            self.lblRole = QLabel()
            self.lblRole.setPixmap(IconRegistry.from_name(role.icon, role.icon_color).pixmap(QSize(24, 24)))
            self.layout().addWidget(line(vertical=True))
            self.layout().addWidget(self.lblRole)

        border_size = 3 if pov else 2
        border_color = '#3f7cac' if pov else '#bad7f2'

        self.setStyleSheet(f'''
        CharacterLabel {{
            border: {border_size}px solid {border_color}; 
            border-radius: 8px; padding-left: 3px; padding-right: 3px;}}
        ''')


class CharacterAvatarLabel(QToolButton):
    def __init__(self, character: Character, size: int = 24, parent=None):
        super(CharacterAvatarLabel, self).__init__(parent)
        self.setStyleSheet('border: 0px;')
        self.setIcon(QIcon(avatars.pixmap(character)))
        self.setIconSize(QSize(size, size))


class ConflictLabel(Label):
    def __init__(self, conflict: Conflict, parent=None):
        super(ConflictLabel, self).__init__(parent)
        self.conflict = conflict

        self.lblConflict = QLabel()
        self.lblConflict.setPixmap(IconRegistry.conflict_icon().pixmap(QSize(24, 24)))
        self.layout().addWidget(self.lblConflict)

        self.lblAvatar = QLabel()
        if self.conflict.character:
            set_avatar(self.lblAvatar, self.conflict.character, 24)
        else:
            if self.conflict.type == ConflictType.CHARACTER:
                icon = IconRegistry.conflict_character_icon()
            elif self.conflict.type == ConflictType.SOCIETY:
                icon = IconRegistry.conflict_society_icon()
            elif self.conflict.type == ConflictType.NATURE:
                icon = IconRegistry.conflict_nature_icon()
            elif self.conflict.type == ConflictType.TECHNOLOGY:
                icon = IconRegistry.conflict_technology_icon()
            elif self.conflict.type == ConflictType.SUPERNATURAL:
                icon = IconRegistry.conflict_supernatural_icon()
            elif self.conflict.type == ConflictType.SELF:
                icon = IconRegistry.conflict_self_icon()
            else:
                icon = IconRegistry.conflict_icon()
            self.lblAvatar.setPixmap(icon.pixmap(QSize(24, 24)))
        self.layout().addWidget(self.lblAvatar)
        self.layout().addWidget(QLabel(self.conflict.keyphrase))

        self.setStyleSheet('''
                ConflictLabel {
                    border: 2px solid #f3a712;
                    border-radius: 8px; padding-left: 3px; padding-right: 3px;}
                ''')


class TraitLabel(QLabel):
    def __init__(self, trait: str, positive: bool = True, parent=None):
        super(TraitLabel, self).__init__(parent)

        self.setText(trait)

        if positive:
            bg_color = '#519872'
            border_color = '#034732'
        else:
            bg_color = '#db5461'
            border_color = '#ef2917'
        self.setStyleSheet(f'''TraitLabel {{
            background-color: {bg_color};
            border: 2px solid {border_color};
            border-radius: 8px;
            color: white;
            padding-left: 0px; padding-right: 0px; padding-top: 0px; padding-bottom: 0px;
        }}''')


class SelectionItemLabel(Label):
    def __init__(self, item: SelectionItem, parent=None):
        super(SelectionItemLabel, self).__init__(parent)
        self.item = item

        if self.item.icon:
            self.lblIcon = QLabel()
            self.lblIcon.setPixmap(IconRegistry.from_name(self.item.icon, self.item.icon_color).pixmap(QSize(24, 24)))
            self.layout().addWidget(self.lblIcon)

        self.lblText = QLabel(self.item.text)
        self.layout().addWidget(self.lblText)

        self.setStyleSheet('''
                        SelectionItemLabel {
                            border: 2px solid #2e5266;
                            border-radius: 8px; padding-left: 3px; padding-right: 3px;}
                        ''')


class LabelsEditorWidget(QFrame):
    def __init__(self, parent=None):
        super(LabelsEditorWidget, self).__init__(parent)
        self.setLineWidth(1)
        self.setFrameShape(QFrame.Box)
        self.setStyleSheet('LabelsSelectionWidget {background: white;}')
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(1, 1, 1, 1)
        self._labels_index = {}
        for item in self.items():
            self._labels_index[item.text] = item

        self._btnEdit = QToolButton()
        self._btnEdit.setIcon(IconRegistry.plus_edit_icon())

        self._model = self._initModel()
        self._model.item_edited.connect(self._selectionChanged)
        self._model.setCheckable(True, SelectionItemsModel.ColName)
        self._popup = self._initPopupWidget()
        self._model.selection_changed.connect(self._selectionChanged)

        menu = QMenu(self._btnEdit)
        action = QWidgetAction(menu)
        action.setDefaultWidget(self._popup)
        menu.addAction(action)
        self._btnEdit.setMenu(menu)
        self._btnEdit.setPopupMode(QToolButton.InstantPopup)
        self.layout().addWidget(self._btnEdit)

        self._wdgLabels = LabelsWidget()
        self._wdgLabels.setStyleSheet('LabelsWidget {border: 1px solid black;}')
        self._wdgLabels.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.layout().addWidget(self._wdgLabels)

    @abstractmethod
    def _initModel(self) -> SelectionItemsModel:
        pass

    @abstractmethod
    def items(self) -> List[SelectionItem]:
        pass

    def value(self) -> List[str]:
        return [x.text for x in self._model.selections()]

    def setValue(self, values: List[str]):
        self._model.uncheckAll()
        for v in values:
            item = self._labels_index.get(v)
            if item:
                self._model.checkItem(item)
        self._model.modelReset.emit()
        self._selectionChanged()

    def _initPopupWidget(self) -> QWidget:
        wdg = ItemsEditorWidget()
        wdg.setModel(self._model)
        wdg.tableView.clicked.connect(self._choiceClicked)
        return wdg

    def _choiceClicked(self, index: QModelIndex):
        if index.column() == SelectionItemsModel.ColIcon:
            result = IconSelectorDialog(self).display()
            if result:
                self._model.setData(index, (result[0], result[1].name()), role=Qt.DecorationRole)

    def _selectionChanged(self):
        self._wdgLabels.clear()
        self._addItems(self._model.selections())

    def _addItems(self, items: Set[SelectionItem]):
        for item in items:
            self._wdgLabels.addLabel(SelectionItemLabel(item))
