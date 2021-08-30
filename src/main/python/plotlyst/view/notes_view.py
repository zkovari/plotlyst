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
from PyQt5.QtCore import QModelIndex, QTimer
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.events import SceneChangedEvent, SceneDeletedEvent
from src.main.python.plotlyst.model.scenes_model import ScenesTableModel, ScenesNotesTableModel
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.generated.notes_view_ui import Ui_NotesView


class NotesView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel, [SceneChangedEvent, SceneDeletedEvent])
        self.ui = Ui_NotesView()
        self.ui.setupUi(self.widget)

        self.scenes_model = ScenesNotesTableModel(self.novel)
        self.ui.lstScenes.setModel(self.scenes_model)
        self.ui.lstScenes.setModelColumn(ScenesTableModel.ColTitle)
        self.ui.lstScenes.clicked.connect(self._on_scene_selected)

        self._scene = None
        self._save_timer = QTimer()
        self._save_timer.setInterval(500)
        self._first_update: bool = True
        self.ui.textNotes.textChanged.connect(lambda: self._save_timer.start())
        self._save_timer.timeout.connect(self._save)

    @overrides
    def refresh(self):
        self.scenes_model.modelReset.emit()

    def _on_scene_selected(self, index: QModelIndex):
        self._scene = self.scenes_model.data(index, role=ScenesTableModel.SceneRole)
        self._first_update = True
        self.ui.textNotes.setPlainText(self._scene.notes)

    def _save(self):
        if self._first_update:
            self._first_update = False
        self._save_timer.stop()
        if not self._scene:
            return
        self._scene.notes = self.ui.textNotes.toPlainText()
        self.repo.update_scene(self._scene)
        self.scenes_model.dataChanged.emit(self.ui.lstScenes.selectedIndexes()[0],
                                           self.ui.lstScenes.selectedIndexes()[0])
