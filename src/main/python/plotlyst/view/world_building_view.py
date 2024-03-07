"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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

import qtanim
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap
from overrides import overrides
from qthandy import line

from plotlyst.common import PLOTLYST_SECONDARY_COLOR
from plotlyst.core.domain import Novel, WorldBuildingEntity
from plotlyst.env import app_env
from plotlyst.resources import resource_registry
from plotlyst.view._view import AbstractNovelView
from plotlyst.view.common import link_buttons_to_pages, ButtonPressResizeEventFilter, shadow, \
    insert_before_the_end
from plotlyst.view.generated.world_building_view_ui import Ui_WorldBuildingView
from plotlyst.view.icons import IconRegistry
from plotlyst.view.style.base import apply_bg_image
from plotlyst.view.widget.tree import TreeSettings
from plotlyst.view.widget.world.editor import EntityAdditionMenu, WorldBuildingEntityEditor, \
    WorldBuildingGlossaryEditor
from plotlyst.view.widget.world.map import WorldBuildingMapView


class WorldBuildingView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel)
        self.ui = Ui_WorldBuildingView()
        self.ui.setupUi(self.widget)
        apply_bg_image(self.ui.pageEntity, resource_registry.paper_bg)
        apply_bg_image(self.ui.pageGlossary, resource_registry.paper_bg)
        apply_bg_image(self.ui.scrollAreaWidgetContents, resource_registry.paper_bg)
        # background: #F2F2F2;
        # 692345;
        self.ui.wdgCenterEditor.setStyleSheet('''
        #wdgCenterEditor {
            background: #ede0d4;
            border-radius: 12px;
        }
        ''')
        self.ui.lblBanner.setPixmap(QPixmap(resource_registry.vintage_pocket_banner))

        self._entity: Optional[WorldBuildingEntity] = None

        self.ui.btnNew.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnNew.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnNew))
        self.ui.btnTreeToggle.setIcon(IconRegistry.from_name('mdi.file-tree-outline'))
        self.ui.btnTreeToggle.clicked.connect(lambda x: qtanim.toggle_expansion(self.ui.wdgWorldContainer, x))
        shadow(self.ui.wdgWorldContainer)
        self._additionMenu = EntityAdditionMenu(self.ui.btnNew)
        self._additionMenu.entityTriggered.connect(self.ui.treeWorld.addEntity)
        self.ui.iconReaderMode.setIcon(IconRegistry.from_name('fa5s.eye'))

        self.ui.wdgSeparator.layout().addWidget(line(color='#510442'))

        self.ui.btnWorldView.setIcon(IconRegistry.world_building_icon())
        self.ui.btnMapView.setIcon(IconRegistry.from_name('fa5s.map-marked-alt', color_on=PLOTLYST_SECONDARY_COLOR))
        self.ui.btnHistoryView.setIcon(
            IconRegistry.from_name('mdi.timeline-outline', color_on=PLOTLYST_SECONDARY_COLOR))
        self.ui.btnGlossaryView.setIcon(IconRegistry.from_name('mdi.book-alphabet', color_on=PLOTLYST_SECONDARY_COLOR))

        self.ui.splitterNav.setSizes([100, 500])
        font = self.ui.lineName.font()
        font.setPointSize(32)
        if app_env.is_mac():
            family = 'Helvetica Neue'
        elif app_env.is_windows():
            family = 'Calibri'
        else:
            family = 'Sans Serif'
        font.setFamily(family)
        self.ui.lineName.setFont(font)
        self.ui.lineName.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ui.lineName.setStyleSheet(f'''
        QLineEdit {{
            border: 0px;
            background-color: rgba(0, 0, 0, 0);
            color: #510442; 
        }}''')

        self.ui.lineName.textEdited.connect(self._name_edited)

        self._editor = WorldBuildingEntityEditor(self.novel)
        insert_before_the_end(self.ui.wdgCenterEditor, self._editor)

        self.ui.treeWorld.setSettings(TreeSettings(font_incr=2))
        self.ui.treeWorld.setNovel(self.novel)
        self.ui.treeWorld.entitySelected.connect(self._selection_changed)
        self.ui.treeWorld.selectRoot()

        self.map = WorldBuildingMapView(self.novel)
        self.ui.pageMap.layout().addWidget(self.map)

        self.glossaryEditor = WorldBuildingGlossaryEditor(self.novel)
        self.ui.wdgGlossaryParent.layout().addWidget(self.glossaryEditor)

        link_buttons_to_pages(self.ui.stackedWidget, [(self.ui.btnWorldView, self.ui.pageEntity),
                                                      (self.ui.btnMapView, self.ui.pageMap),
                                                      (self.ui.btnHistoryView, self.ui.pageTimeline),
                                                      (self.ui.btnGlossaryView, self.ui.pageGlossary)])
        self.ui.btnWorldView.setChecked(True)

        self.ui.iconReaderMode.setHidden(True)
        self.ui.readerModeToggle.setHidden(True)
        self.ui.btnHistoryView.setHidden(True)

        self.ui.btnTreeToggle.setChecked(True)

    @overrides
    def refresh(self):
        pass

    def _selection_changed(self, entity: WorldBuildingEntity):
        self._entity = entity
        self.ui.lineName.setText(self._entity.name)
        #         self._entity.elements = [
        #             WorldBuildingEntityElement(WorldBuildingEntityElementType.Text, text="""The Elensh people is a group that has had a cultural identity for many hundreds of years. They're primarily found in Olinthis as well as the southern parts of Elken. They are the main people of Olinthis but are considered a minority in Elken, though they're generally respected both places.
        # They're known as the people of the flowers, because many of their traditions feature colourful flowers and they're known for being the best flower traders through many parts of Dysvoll."""),
        #             WorldBuildingEntityElement(WorldBuildingEntityElementType.Section, title='Fauna', blocks=[
        #                 WorldBuildingEntityElement(WorldBuildingEntityElementType.Header, title='Fauna'),
        #                 WorldBuildingEntityElement(WorldBuildingEntityElementType.Quote,
        #                                            text='This is a quoted text said by a smart person', ref='Beril'),
        #                 WorldBuildingEntityElement(WorldBuildingEntityElementType.Text)
        #             ]),
        #
        #         ]
        self._editor.setEntity(self._entity)
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
        self.repo.update_world(self.novel)

    def _icon_changed(self, icon_name: str, color: QColor):
        self._entity.icon = icon_name
        self._entity.icon_color = color.name()
        self.ui.treeWorld.updateEntity(self._entity)
