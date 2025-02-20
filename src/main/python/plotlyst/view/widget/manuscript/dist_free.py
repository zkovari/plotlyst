"""
Plotlyst
Copyright (C) 2021-2025  Zsolt Kovari

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
from typing import Optional

from PyQt6.QtGui import QScreen
from PyQt6.QtWidgets import QWidget, QApplication

from plotlyst.core.sprint import TimerModel
from plotlyst.view.generated.distraction_free_manuscript_editor_ui import Ui_DistractionFreeManuscriptEditor
from plotlyst.view.widget.manuscript import SprintWidget
from plotlyst.view.widget.manuscript.editor import ManuscriptEditor


class DistractionFreeManuscriptEditor(QWidget, Ui_DistractionFreeManuscriptEditor):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._firstInit: bool = True

        self.wdgSprint = SprintWidget(self)
        self.wdgSprint.setCompactMode(True)

        self.btnTypewriterMode.toggled.connect(self._toggle_typewriter_mode)

    def activate(self, editor: ManuscriptEditor, timer: Optional[TimerModel] = None):
        if timer and timer.isActive():
            self.wdgSprint.setModel(timer)
            self.wdgSprint.setVisible(True)
        else:
            self.wdgSprint.setHidden(True)

        if self._firstInit:
            self.btnTypewriterMode.setChecked(True)
            self._firstInit = False
        else:
            self._toggle_typewriter_mode(self.btnTypewriterMode.isChecked())

    def _toggle_typewriter_mode(self, toggled: bool):
        return
        viewportMargins = self.editor.textEdit.viewportMargins()
        if toggled:
            screen: QScreen = QApplication.screenAt(self.editor.pos())
            viewportMargins.setBottom(screen.size().height() // 2)
        else:
            viewportMargins.setBottom(30)

        self.editor.textEdit.setViewportMargins(viewportMargins.left(), viewportMargins.top(),
                                                viewportMargins.right(), viewportMargins.bottom())
        self.editor.textEdit.ensureCursorVisible()
