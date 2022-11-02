"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.core.template import default_location_profiles
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.generated.world_building_view_ui import Ui_WorldBuildingView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.location import LocationProfileTemplateView
from src.main.python.plotlyst.view.widget.world_building import WorldBuildingEditor


class WorldBuildingView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel)
        self.ui = Ui_WorldBuildingView()
        self.ui.setupUi(self.widget)

        self.widget.setPalette(QPalette(Qt.GlobalColor.white))
        self.ui.btnEditorToggle.setIcon(IconRegistry.document_edition_icon())

        self._editor = WorldBuildingEditor(self.novel.world.root_entity)
        self.ui.wdgEditorParent.layout().addWidget(self._editor)
        self.ui.wdgSidebar.setVisible(self.ui.btnEditorToggle.isChecked())
        self.ui.wdgSidebar.layout().addWidget(LocationProfileTemplateView(self.novel, default_location_profiles()[0]))
        self.ui.splitter.setSizes([500, 150])

        self._editor.scene().modelChanged.connect(lambda: self.repo.update_novel(self.novel))

    @overrides
    def refresh(self):
        pass
