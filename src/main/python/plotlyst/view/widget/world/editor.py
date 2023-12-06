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
from functools import partial
from typing import Optional, Dict, Set

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QTextCharFormat, QTextCursor, QFont
from PyQt6.QtWidgets import QWidget, QSplitter, QLineEdit
from qthandy import vspacer, clear_layout, transparent, vbox, margins, hbox
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget, ActionTooltipDisplayMode

from src.main.python.plotlyst.common import recursive
from src.main.python.plotlyst.core.domain import Novel, WorldBuildingEntity, WorldBuildingEntityType, \
    WorldBuildingEntityElement, WorldBuildingEntityElementType
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.view.common import action, push_btn, frame
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.display import Icon
from src.main.python.plotlyst.view.widget.input import AutoAdjustableTextEdit, AutoAdjustableLineEdit
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode, TreeSettings


class EntityAdditionMenu(MenuWidget):
    entityTriggered = pyqtSignal(WorldBuildingEntity)

    def __init__(self, parent=None):
        super(EntityAdditionMenu, self).__init__(parent)
        self.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)

        self.addAction(action('Location', IconRegistry.location_icon(),
                              slot=lambda: self._triggered(WorldBuildingEntityType.SETTING),
                              tooltip='Physical location in the world'))
        self.addAction(action('Entity', IconRegistry.world_building_icon(),
                              slot=lambda: self._triggered(WorldBuildingEntityType.ABSTRACT),
                              tooltip='Abstract entity in the world, e.g., nation, kingdom, or magic'))
        self.addAction(action('Social group', IconRegistry.group_icon(),
                              slot=lambda: self._triggered(WorldBuildingEntityType.GROUP),
                              tooltip='Social group in the world, e.g., a guild or an organization'))
        self.addSeparator()
        self.addAction(action('Item', IconRegistry.from_name('mdi.ring', '#b6a6ca'),
                              slot=lambda: self._triggered(WorldBuildingEntityType.ITEM),
                              tooltip='Relevant item in the world, e.g., an artifact'))
        self.addSeparator()
        self.addAction(action('Container',
                              slot=lambda: self._triggered(WorldBuildingEntityType.CONTAINER),
                              tooltip='General container to group worldbuilding entities together'))

    def _triggered(self, wdType: WorldBuildingEntityType):
        if wdType == WorldBuildingEntityType.SETTING:
            name = 'New location'
            icon_name = 'fa5s.map-pin'
        elif wdType == WorldBuildingEntityType.GROUP:
            name = 'New group'
            icon_name = 'mdi.account-group'
        elif wdType == WorldBuildingEntityType.ITEM:
            name = 'New item'
            icon_name = ''
        elif wdType == WorldBuildingEntityType.CONTAINER:
            name = 'Container'
            icon_name = ''
        else:
            name = 'New entity'
            icon_name = ''

        entity = WorldBuildingEntity(name, icon=icon_name, type=wdType)

        self.entityTriggered.emit(entity)


class EntityNode(ContainerNode):
    addEntity = pyqtSignal(WorldBuildingEntity)

    def __init__(self, entity: WorldBuildingEntity, parent=None, settings: Optional[TreeSettings] = None):
        super(EntityNode, self).__init__(entity.name, parent=parent, settings=settings)
        self._entity = entity
        self.setPlusButtonEnabled(True)
        self._additionMenu = EntityAdditionMenu(self._btnAdd)
        self._additionMenu.entityTriggered.connect(self.addEntity.emit)
        self.setPlusMenu(self._additionMenu)
        self.refresh()

    def entity(self) -> WorldBuildingEntity:
        return self._entity

    def refresh(self):
        self._lblTitle.setText(self._entity.name)

        if self._entity.icon:
            self._icon.setIcon(IconRegistry.from_name(self._entity.icon, self._entity.icon_color))
            self._icon.setVisible(True)
        else:
            self._icon.setHidden(True)


class RootNode(EntityNode):

    def __init__(self, entity: WorldBuildingEntity, parent=None, settings: Optional[TreeSettings] = None):
        super(RootNode, self).__init__(entity, parent=parent, settings=settings)
        self.setMenuEnabled(False)
        self.setPlusButtonEnabled(False)


class WorldBuildingTreeView(TreeView):
    entitySelected = pyqtSignal(WorldBuildingEntity)

    def __init__(self, parent=None, settings: Optional[TreeSettings] = None):
        super(WorldBuildingTreeView, self).__init__(parent)
        self._novel: Optional[Novel] = None
        self._settings: Optional[TreeSettings] = settings
        self._root: Optional[RootNode] = None
        self._entities: Dict[WorldBuildingEntity, EntityNode] = {}
        self._selectedEntities: Set[WorldBuildingEntity] = set()
        self._centralWidget.setStyleSheet('background: #ede0d4;')
        transparent(self)

    def selectRoot(self):
        self._root.select()
        self._entitySelectionChanged(self._root, self._root.isSelected())

    def setSettings(self, settings: TreeSettings):
        self._settings = settings

    def setNovel(self, novel: Novel):
        self._novel = novel
        self._root = RootNode(self._novel.world.root_entity, settings=self._settings)
        self._root.selectionChanged.connect(partial(self._entitySelectionChanged, self._root))
        self.refresh()

    def addEntity(self, entity: WorldBuildingEntity):
        wdg = self.__initEntityWidget(entity)
        self._root.addChild(wdg)

    def refresh(self):
        def addChildWdg(parent: WorldBuildingEntity, child: WorldBuildingEntity):
            childWdg = self.__initEntityWidget(child)
            self._entities[parent].addChild(childWdg)

        self.clearSelection()
        self._entities.clear()
        clear_layout(self._centralWidget)

        self._entities[self._novel.world.root_entity] = self._root
        self._centralWidget.layout().addWidget(self._root)
        for entity in self._novel.world.root_entity.children:
            wdg = self.__initEntityWidget(entity)
            self._root.addChild(wdg)
            recursive(entity, lambda parent: parent.children, addChildWdg)
        self._centralWidget.layout().addWidget(vspacer())

    def updateEntity(self, entity: WorldBuildingEntity):
        self._entities[entity].refresh()

    def clearSelection(self):
        for entity in self._selectedEntities:
            self._entities[entity].deselect()
        self._selectedEntities.clear()

    def _entitySelectionChanged(self, node: EntityNode, selected: bool):
        if selected:
            self.clearSelection()
            self._selectedEntities.add(node.entity())
            self.entitySelected.emit(node.entity())
        elif node.entity() in self._selectedEntities:
            self._selectedEntities.remove(node.entity())

    def _addEntity(self, parent: EntityNode, entity: WorldBuildingEntity):
        wdg = self.__initEntityWidget(entity)
        parent.addChild(wdg)
        parent.entity().children.append(entity)

    def __initEntityWidget(self, entity: WorldBuildingEntity) -> EntityNode:
        node = EntityNode(entity, settings=self._settings)
        node.selectionChanged.connect(partial(self._entitySelectionChanged, node))
        node.addEntity.connect(partial(self._addEntity, node))

        self._entities[entity] = node
        return node


class WorldBuildingEntityElementWidget(QWidget):
    def __init__(self, element: WorldBuildingEntityElement, parent=None):
        super().__init__(parent)
        self.element = element

    @staticmethod
    def newWidget(element: WorldBuildingEntityElement) -> 'WorldBuildingEntityElementWidget':
        if element.type == WorldBuildingEntityElementType.Text:
            return WorldBuildingEntityTextElementEditor(element)
        elif element.type == WorldBuildingEntityElementType.Section:
            return WorldBuildingEntitySectionElementEditor(element)
        elif element.type == WorldBuildingEntityElementType.Header:
            return WorldBuildingEntityHeaderElementEditor(element)
        elif element.type == WorldBuildingEntityElementType.Quote:
            return WorldBuildingEntityQuoteElementEditor(element)
        else:
            raise ValueError(f'Unsupported WorldBuildingEntityElement type {element.type}')


class WorldBuildingEntityTextElementEditor(WorldBuildingEntityElementWidget):
    def __init__(self, element: WorldBuildingEntityElement, parent=None):
        super().__init__(element, parent)
        self._capitalized = False

        self.textEdit = AutoAdjustableTextEdit()
        self.textEdit.setProperty('transparent', True)
        # self.textEdit.setProperty('rounded', True)
        self.textEdit.setPlaceholderText('Describe this entity...')
        self.textEdit.textChanged.connect(self._textChanged)
        self.textEdit.setMarkdown(element.text)

        font = self.textEdit.font()
        font.setPointSize(16)
        if app_env.is_mac():
            family = 'Helvetica Neue'
        elif app_env.is_windows():
            family = 'Calibri'
        else:
            family = 'Sans Serif'
        font.setFamily(family)
        self.textEdit.setFont(font)

        hbox(self, 0, 0).addWidget(self.textEdit)
        margins(self, left=15)

    def _textChanged(self):
        if not self.textEdit.toPlainText() or len(self.textEdit.toPlainText()) == 1:
            self._capitalized = False
            return

        if self._capitalized:
            return

        format_first_letter = QTextCharFormat()
        format_first_letter.setFontPointSize(32)

        cursor = QTextCursor(self.textEdit.document())
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor)
        self._capitalized = True
        cursor.setCharFormat(format_first_letter)


class WorldBuildingEntityHeaderElementEditor(WorldBuildingEntityElementWidget):
    def __init__(self, element: WorldBuildingEntityElement, parent=None):
        super().__init__(element, parent)

        vbox(self, 0)
        margins(self, top=10, bottom=10)
        self.lineTitle = QLineEdit()
        self.lineTitle.setProperty('transparent', True)
        font = self.lineTitle.font()
        font.setPointSize(24)
        if app_env.is_mac():
            family = 'Helvetica Neue'
        elif app_env.is_windows():
            family = 'Calibri'
        else:
            family = 'Sans Serif'
        font.setFamily(family)
        self.lineTitle.setFont(font)
        self.lineTitle.setStyleSheet(f'''
        QLineEdit {{
            border: 0px;
            background-color: rgba(0, 0, 0, 0);
            color: #510442;
        }}''')
        self.lineTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineTitle.setText(self.element.title)

        self.frame = frame()
        vbox(self.frame).addWidget(self.lineTitle, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self.frame)
        self.frame.setStyleSheet('''
        .QFrame {
            border-top: 1px outset #510442;
            border-bottom: 1px outset #510442;
            border-radius: 6px;
            background: #DABFA7;
        }''')


class WorldBuildingEntityQuoteElementEditor(WorldBuildingEntityElementWidget):
    def __init__(self, element: WorldBuildingEntityElement, parent=None):
        super().__init__(element, parent)

        vbox(self, 0)
        margins(self, left=15, top=5, bottom=5)
        self.textEdit = AutoAdjustableTextEdit()
        self.textEdit.setStyleSheet(f'''
                border: 0px;
                background-color: rgba(0, 0, 0, 0);
                color: grey;
        ''')
        # self.textEdit.setProperty('transparent', True)
        self.textEdit.setPlaceholderText('Edit quote')
        font: QFont = self.textEdit.font()
        font.setPointSize(14)
        if app_env.is_mac():
            family = 'Helvetica Neue'
        elif app_env.is_windows():
            family = 'Calibri'
        else:
            family = 'Sans Serif'
        font.setFamily(family)
        font.setItalic(True)
        self.textEdit.setFont(font)
        self.textEdit.setText(self.element.text)

        self.lineEditRef = AutoAdjustableLineEdit()
        self.lineEditRef.setFont(font)
        self.lineEditRef.setStyleSheet(f'''
                QLineEdit {{
                    border: 0px;
                    background-color: rgba(0, 0, 0, 0);
                    color: #510442;
                }}''')
        self.lineEditRef.setPlaceholderText('Source')
        self.wdgQuoteRef = QWidget()
        hbox(self.wdgQuoteRef, 2, 0)
        iconDash = Icon()
        iconDash.setIcon(IconRegistry.from_name('msc.dash', '#510442', scale=2.0))
        self.wdgQuoteRef.layout().addWidget(iconDash)
        self.wdgQuoteRef.layout().addWidget(self.lineEditRef)

        self.frame = frame()
        vbox(self.frame, 5)
        margins(self.frame, left=20, right=15)
        self.frame.layout().addWidget(self.textEdit)
        self.frame.layout().addWidget(self.wdgQuoteRef, alignment=Qt.AlignmentFlag.AlignRight)
        self.layout().addWidget(self.frame)
        self.frame.setStyleSheet('''
                .QFrame {
                    border-left: 3px outset #510442;
                    border-radius: 2px;
                    background: #E3D0BD;
                }''')


class WorldBuildingEntitySectionElementEditor(WorldBuildingEntityElementWidget):
    def __init__(self, element: WorldBuildingEntityElement, parent=None):
        super().__init__(element, parent)

        vbox(self, 0)

        for el in self.element.blocks:
            wdg = WorldBuildingEntityElementWidget.newWidget(el)
            # self.header = WorldBuildingEntityHeaderElementEditor(self.element)
            self.layout().addWidget(wdg)


class WorldBuildingEntityEditor(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._entity: Optional[WorldBuildingEntity] = None

        self.wdgEditorMiddle = QWidget()
        vbox(self.wdgEditorMiddle)
        margins(self.wdgEditorMiddle, left=15)
        self.wdgEditorSide = QWidget()
        vbox(self.wdgEditorSide)
        margins(self.wdgEditorSide, right=15)

        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.wdgEditorMiddle)
        splitter.addWidget(self.wdgEditorSide)
        splitter.setSizes([500, 150])

        vbox(self, 0, 0).addWidget(splitter)

    def setEntity(self, entity: WorldBuildingEntity):
        self._entity = entity

        for element in self._entity.elements:
            self._addElement(element)

        for element in self._entity.side_elements:
            self._addElement(element, False)

        self._addPlaceholder()
        self._addPlaceholder(False)
        self.wdgEditorSide.layout().addWidget(vspacer())

    def _addPlaceholder(self, middle: bool = True):
        wdg = push_btn(IconRegistry.plus_icon('grey'), 'Add section', transparent_=True)
        wdg.installEventFilter(OpacityEventFilter(wdg, enterOpacity=0.8))
        if middle:
            self.wdgEditorMiddle.layout().addWidget(wdg, alignment=Qt.AlignmentFlag.AlignLeft)
        else:
            self.wdgEditorSide.layout().addWidget(wdg, alignment=Qt.AlignmentFlag.AlignCenter)

    def _addElement(self, element: WorldBuildingEntityElement, middle: bool = True):
        wdg = WorldBuildingEntityElementWidget.newWidget(element)

        if middle:
            self.wdgEditorMiddle.layout().addWidget(wdg)
        else:
            self.wdgEditorSide.layout().addWidget(wdg)
