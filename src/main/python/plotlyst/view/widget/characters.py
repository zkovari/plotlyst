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
from functools import partial
from typing import Iterable, List

from PyQt5.QtCore import QItemSelection, Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QToolButton, QButtonGroup, QFrame

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel, Character, Conflict, ConflictType, Scene
from src.main.python.plotlyst.model.characters_model import CharactersScenesDistributionTableModel
from src.main.python.plotlyst.model.common import proxy
from src.main.python.plotlyst.view.common import spacer_widget
from src.main.python.plotlyst.view.generated.character_conflict_widget_ui import Ui_CharacterConflictWidget
from src.main.python.plotlyst.view.generated.scene_dstribution_widget_ui import Ui_CharactersScenesDistributionWidget
from src.main.python.plotlyst.view.icons import avatars, IconRegistry


class CharactersScenesDistributionWidget(QWidget):
    avg_text: str = 'Average characters per scenes: '
    common_text: str = 'Common scenes: '

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.ui = Ui_CharactersScenesDistributionWidget()
        self.ui.setupUi(self)
        self.novel = novel
        self.average = 0
        self._model = CharactersScenesDistributionTableModel(self.novel)
        self._scenes_proxy = proxy(self._model)
        self._scenes_proxy.sort(0, Qt.DescendingOrder)
        self.ui.tblSceneDistribution.horizontalHeader().setDefaultSectionSize(26)
        self.ui.tblSceneDistribution.setModel(self._scenes_proxy)
        self.ui.tblSceneDistribution.hideColumn(0)
        self.ui.tblCharacters.setModel(self._scenes_proxy)
        self.ui.tblCharacters.setColumnWidth(0, 70)
        self.ui.tblCharacters.setMaximumWidth(70)

        self.ui.tblCharacters.selectionModel().selectionChanged.connect(self._on_character_selected)
        self.ui.tblSceneDistribution.selectionModel().selectionChanged.connect(self._on_scene_selected)

        self.refresh()

    def refresh(self):
        if self.novel.scenes:
            self.average = sum([len(x.characters) + 1 for x in self.novel.scenes]) / len(self.novel.scenes)
        else:
            self.average = 0
        for col in range(self._model.columnCount()):
            if col == 0:
                continue
            self.ui.tblCharacters.hideColumn(col)
        self.ui.spinAverage.setValue(self.average)
        self.ui.tblSceneDistribution.horizontalHeader().setMaximumSectionSize(15)
        self._model.modelReset.emit()

    def _on_character_selected(self):
        selected = self.ui.tblCharacters.selectionModel().selectedIndexes()
        self._model.highlightCharacters(
            [self._scenes_proxy.mapToSource(x) for x in selected])

        if selected and len(selected) > 1:
            self.ui.spinAverage.setPrefix(self.common_text)
            self.ui.spinAverage.setValue(self._model.commonScenes())
        else:
            self.ui.spinAverage.setPrefix(self.avg_text)
            self.ui.spinAverage.setValue(self.average)

        self.ui.tblSceneDistribution.clearSelection()

    def _on_scene_selected(self, selection: QItemSelection):
        indexes = selection.indexes()
        if not indexes:
            return
        self._model.highlightScene(self._scenes_proxy.mapToSource(indexes[0]))
        self.ui.tblCharacters.clearSelection()


class CharacterSelectorWidget(QWidget):
    characterToggled = pyqtSignal(Character)

    def __init__(self, parent=None):
        super(CharacterSelectorWidget, self).__init__(parent)
        self._layout = QHBoxLayout()
        self._btn_group = QButtonGroup()
        self._buttons: List[QToolButton] = []
        self.setLayout(self._layout)

    def setCharacters(self, characters: Iterable[Character]):
        item = self._layout.itemAt(0)
        while item:
            self._layout.removeItem(item)
            item = self._layout.itemAt(0)
        for btn in self._buttons:
            self._btn_group.removeButton(btn)
            btn.deleteLater()
        self._buttons.clear()
        self._update(characters)
        if self._buttons:
            self._buttons[0].setChecked(True)

    def _update(self, characters: Iterable[Character]):
        self._layout.addWidget(spacer_widget())
        for char in characters:
            tool_btn = QToolButton()
            tool_btn.setIcon(QIcon(avatars.pixmap(char)))
            tool_btn.setCheckable(True)
            tool_btn.toggled.connect(partial(self.characterToggled.emit, char))

            self._buttons.append(tool_btn)
            self._btn_group.addButton(tool_btn)
            self._btn_group.setExclusive(True)
            self._layout.addWidget(tool_btn)
        self._layout.addWidget(spacer_widget())


class CharacterConflictWidget(QFrame, Ui_CharacterConflictWidget):
    new_conflict_added = pyqtSignal(Conflict)

    def __init__(self, novel: Novel, scene: Scene, parent=None):
        super(CharacterConflictWidget, self).__init__(parent)
        self.novel = novel
        self.scene = scene
        self.setupUi(self)
        self.setMaximumWidth(270)

        self.btnCharacter.setIcon(IconRegistry.conflict_character_icon())
        self.btnSociety.setIcon(IconRegistry.conflict_society_icon())
        self.btnNature.setIcon(IconRegistry.conflict_nature_icon())
        self.btnTechnology.setIcon(IconRegistry.conflict_technology_icon())
        self.btnSupernatural.setIcon(IconRegistry.conflict_supernatural_icon())
        self.btnSelf.setIcon(IconRegistry.conflict_self_icon())

        for char in self.novel.characters:
            self.cbCharacter.addItem(char.name, char)

        self.btnAddNew.setIcon(IconRegistry.ok_icon())
        self.btnAddNew.setDisabled(True)
        self.btnConfirm.setHidden(True)

        self.lineKey.textChanged.connect(self._keyphrase_edited)

        self.btnGroupConflicts.buttonToggled.connect(self._type_toggled)
        self._type = ConflictType.CHARACTER
        self.btnCharacter.setChecked(True)

        self.btnAddNew.clicked.connect(self._add_new)

    def _type_toggled(self):
        lbl_prefix = 'Character vs.'
        self.cbCharacter.setVisible(self.btnCharacter.isChecked())
        if self.btnCharacter.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} Character')
            self._type = ConflictType.CHARACTER
        elif self.btnSociety.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} Society')
            self._type = ConflictType.SOCIETY
        elif self.btnNature.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} Nature')
            self._type = ConflictType.NATURE
        elif self.btnTechnology.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} Technology')
            self._type = ConflictType.TECHNOLOGY
        elif self.btnSupernatural.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} Supernatural')
            self._type = ConflictType.SUPERNATURAL
        elif self.btnSelf.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} Self')
            self._type = ConflictType.SELF

    def _keyphrase_edited(self, text: str):
        self.btnAddNew.setEnabled(len(text) > 0)

    def _add_new(self):
        conflict = Conflict(self.lineKey.text(), self._type)
        if self._type == ConflictType.CHARACTER:
            conflict.character = self.cbCharacter.currentData()

        self.novel.conflicts.append(conflict)
        self.scene.conflicts.append(conflict)
        client.update_novel(self.novel)
        client.update_scene(self.scene)
        self.new_conflict_added.emit(conflict)

        self.lineKey.clear()
