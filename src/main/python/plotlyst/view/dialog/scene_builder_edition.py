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
from dataclasses import dataclass
from typing import Optional

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog
from overrides import overrides

from src.main.python.plotlyst.core.domain import Scene, Character, NpcCharacter
from src.main.python.plotlyst.view.generated.scene_element_edition_dialog_ui import Ui_SceneElementEditionDialog
from src.main.python.plotlyst.view.icons import avatars, IconRegistry


@dataclass
class SceneElementEditionResult:
    character: Character
    text: str


class SceneElementEditionDialog(QDialog, Ui_SceneElementEditionDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def display(self, scene: Scene) -> Optional[SceneElementEditionResult]:
        self._setup(scene)
        if not self.cbCharacter.count():
            self.cbCharacter.setHidden(True)
        result = self.exec()
        if result == QDialog.Rejected:
            return None
        return SceneElementEditionResult(self.cbCharacter.currentData(), self.lineText.text())

    def _setup(self, scene: Scene):
        pass


class CharacterBasedEditionDialog(SceneElementEditionDialog):
    @overrides
    def _setup(self, scene: Scene):
        for char in scene.characters:
            self.cbCharacter.addItem(QIcon(avatars.pixmap(char)), char.name, char)
        self.cbCharacter.insertSeparator(self.cbCharacter.count())
        self.cbCharacter.addItem(IconRegistry.portrait_icon(), 'Other', NpcCharacter('Other'))

        super()._setup(scene)


class DialogEditionDialog(CharacterBasedEditionDialog):

    @overrides
    def _setup(self, scene: Scene):
        if scene.pov:
            self.cbCharacter.addItem(QIcon(avatars.pixmap(scene.pov)), scene.pov.name, scene.pov)
            self.cbCharacter.insertSeparator(1)
        super()._setup(scene)
