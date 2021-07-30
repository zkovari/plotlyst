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
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QToolButton, QButtonGroup

from src.main.python.plotlyst.core.domain import Novel, Character
from src.main.python.plotlyst.model.characters_model import CharactersScenesDistributionTableModel
from src.main.python.plotlyst.model.common import proxy
from src.main.python.plotlyst.view.common import spacer_widget
from src.main.python.plotlyst.view.generated.scene_dstribution_widget_ui import Ui_CharactersScenesDistributionWidget
from src.main.python.plotlyst.view.icons import avatars


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
    characterClicked = pyqtSignal(Character)

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
            tool_btn.toggled.connect(partial(self.characterClicked.emit, char))

            self._buttons.append(tool_btn)
            self._btn_group.addButton(tool_btn)
            self._btn_group.setExclusive(True)
            self._layout.addWidget(tool_btn)
        self._layout.addWidget(spacer_widget())
