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
from overrides import overrides
from qthandy import incr_font, transparent

from src.main.python.plotlyst.core.domain import Novel, WorldBuildingEntity
from src.main.python.plotlyst.core.template import default_location_profiles
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import link_buttons_to_pages, ButtonPressResizeEventFilter
from src.main.python.plotlyst.view.generated.world_building_view_ui import Ui_WorldBuildingView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.input import AutoAdjustableLineEdit
from src.main.python.plotlyst.view.widget.tree import TreeSettings
from src.main.python.plotlyst.view.widget.utility import IconSelectorButton
from src.main.python.plotlyst.view.widget.world.editor import EntityAdditionMenu
from src.main.python.plotlyst.view.widget.world_building import WorldBuildingProfileTemplateView


class WorldBuildingView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel)
        self.ui = Ui_WorldBuildingView()
        self.ui.setupUi(self.widget)

        self.ui.btnNew.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnNew.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnNew))
        self._additionMenu = EntityAdditionMenu(self.ui.btnNew)
        self._additionMenu.entityTriggered.connect(self.ui.treeWorld.addEntity)

        self._settingTemplate = WorldBuildingProfileTemplateView(self.novel, default_location_profiles()[0])
        self.ui.splitter.setSizes([150, 500])
        self._lineName = AutoAdjustableLineEdit()
        self._lineName.setPlaceholderText('Name')
        transparent(self._lineName)
        incr_font(self._lineName, 15)
        self._btnIcon = IconSelectorButton()
        self.ui.wdgName.layout().addWidget(self._btnIcon)
        self.ui.wdgName.layout().addWidget(self._lineName)

        self.ui.treeWorld.setSettings(TreeSettings(font_incr=2))
        self.ui.treeWorld.setNovel(self.novel)
        self.ui.treeWorld.entitySelected.connect(self._selection_changed)
        self.ui.treeWorld.selectRoot()

        link_buttons_to_pages(self.ui.stackedWidget, [(self.ui.btnWorldView, self.ui.pageEditor),
                                                      (self.ui.btnHistoryView, self.ui.pageHistory)])
        self.ui.btnWorldView.setChecked(True)

    @overrides
    def refresh(self):
        pass

    def _selection_changed(self, entity: WorldBuildingEntity):
        self._lineName.setText(entity.name)
        if entity.icon:
            self._btnIcon.selectIcon(entity.icon, entity.icon_color)
        else:
            self._btnIcon.reset()
