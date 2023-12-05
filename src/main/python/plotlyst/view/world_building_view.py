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
from typing import Optional

from PyQt6.QtGui import QColor
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel, WorldBuildingEntity
from src.main.python.plotlyst.core.template import default_location_profiles
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import link_buttons_to_pages, ButtonPressResizeEventFilter
from src.main.python.plotlyst.view.generated.world_building_view_ui import Ui_WorldBuildingView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.style.base import apply_bg_image
from src.main.python.plotlyst.view.widget.tree import TreeSettings
from src.main.python.plotlyst.view.widget.world.editor import EntityAdditionMenu, WorldBuildingProfileTemplateView


class WorldBuildingView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel)
        self.ui = Ui_WorldBuildingView()
        self.ui.setupUi(self.widget)
        # self.ui.wdgCenterEditor.setProperty('bg-image', True)
        apply_bg_image(self.ui.pageEntity, resource_registry.paper_bg)
        apply_bg_image(self.ui.scrollAreaWidgetContents, resource_registry.paper_bg)

        self._entity: Optional[WorldBuildingEntity] = None

        self.ui.btnNew.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnNew.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnNew))
        self._additionMenu = EntityAdditionMenu(self.ui.btnNew)
        self._additionMenu.entityTriggered.connect(self.ui.treeWorld.addEntity)

        self.ui.splitterNav.setSizes([150, 500])
        self.ui.splitterEditor.setSizes([500, 150])
        # self._lineName = AutoAdjustableLineEdit()
        # self._lineName.setPlaceholderText('Name')
        # transparent(self._lineName)
        # incr_font(self._lineName, 15)
        # self._lineName.textEdited.connect(self._name_edited)
        # self._btnIcon = IconSelectorButton()
        # self._btnIcon.iconSelected.connect(self._icon_changed)
        # self.ui.wdgName.layout().addWidget(self._btnIcon)
        # self.ui.wdgName.layout().addWidget(self._lineName)

        # self.ui.wdgWorldContainer.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # self.ui.treeWorld.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.ui.treeWorld.setSettings(TreeSettings(font_incr=2))
        self.ui.treeWorld.setNovel(self.novel)
        self.ui.treeWorld.entitySelected.connect(self._selection_changed)
        self.ui.treeWorld.selectRoot()

        # retain_when_hidden(self.ui.tabWidget)
        # set_tab_icon(self.ui.tabWidget, self.ui.tabPerception,
        #              IconRegistry.from_name('mdi.radio-tower', color_on=PLOTLYST_MAIN_COLOR))
        # set_tab_icon(self.ui.tabWidget, self.ui.tabGoals, IconRegistry.goal_icon('black', PLOTLYST_MAIN_COLOR))
        # set_tab_icon(self.ui.tabWidget, self.ui.tabTopics, IconRegistry.topics_icon(color_on=PLOTLYST_MAIN_COLOR))
        # set_tab_icon(self.ui.tabWidget, self.ui.tabHistory, IconRegistry.backstory_icon('black', PLOTLYST_MAIN_COLOR))
        # set_tab_icon(self.ui.tabWidget, self.ui.tabNotes, IconRegistry.document_edition_icon())

        self._setting_template = WorldBuildingProfileTemplateView(self.novel, default_location_profiles()[0])
        # hbox(self.ui.tabPerception).addWidget(self._setting_template)
        # self._group_template = WorldBuildingProfileTemplateView(self.novel, default_group_profile())
        # hbox(self.ui.tabGoals).addWidget(self._group_template)

        link_buttons_to_pages(self.ui.stackedWidget, [(self.ui.btnWorldView, self.ui.pageEntity),
                                                      (self.ui.btnMapView, self.ui.pageMap)])
        self.ui.btnWorldView.setChecked(True)

    @overrides
    def refresh(self):
        pass

    def _selection_changed(self, entity: WorldBuildingEntity):
        self._entity = entity
        self.ui.lineName.setText(self._entity.name)
        # self._btnIcon.setVisible(True)
        # self.ui.tabWidget.setVisible(True)
        # if entity.icon:
        #     self._btnIcon.selectIcon(self._entity.icon, self._entity.icon_color)
        # else:
        #     self._btnIcon.reset()

        # if entity.type == WorldBuildingEntityType.SETTING:
        #     set_tab_visible(self.ui.tabWidget, self.ui.tabPerception)
        #     set_tab_visible(self.ui.tabWidget, self.ui.tabGoals, False)
        #     self._setting_template.setEntity(self._entity)
        # elif entity.type == WorldBuildingEntityType.GROUP:
        #     set_tab_visible(self.ui.tabWidget, self.ui.tabPerception, False)
        #     set_tab_visible(self.ui.tabWidget, self.ui.tabGoals, False)
        #     # self._group_template.setEntity(self._entity)
        # elif entity.type == WorldBuildingEntityType.CONTAINER:
        #     self.ui.tabWidget.setHidden(True)
        #     self._btnIcon.setHidden(True)
        # else:
        #     set_tab_visible(self.ui.tabWidget, self.ui.tabPerception, False)
        #     set_tab_visible(self.ui.tabWidget, self.ui.tabGoals, False)

    def _name_edited(self, name: str):
        self._entity.name = name
        self.ui.treeWorld.updateEntity(self._entity)

    def _icon_changed(self, icon_name: str, color: QColor):
        self._entity.icon = icon_name
        self._entity.icon_color = color.name()
        self.ui.treeWorld.updateEntity(self._entity)
