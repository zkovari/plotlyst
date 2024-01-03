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
from typing import Optional, Dict, Set, Any, List

import qtanim
from PyQt6.QtCore import pyqtSignal, Qt, QModelIndex, QSize
from PyQt6.QtGui import QTextCharFormat, QTextCursor, QFont, QResizeEvent, QMouseEvent, QColor
from PyQt6.QtWidgets import QWidget, QSplitter, QLineEdit, QTableView, QApplication, QDialog, QGridLayout
from overrides import overrides
from qthandy import vspacer, clear_layout, transparent, vbox, margins, hbox, sp, retain_when_hidden, decr_icon, pointy, \
    grid, flow, spacer
from qthandy.filter import OpacityEventFilter, VisibilityToggleEventFilter, DisabledClickEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import recursive
from src.main.python.plotlyst.core.domain import Novel, WorldBuildingEntity, WorldBuildingEntityType, \
    WorldBuildingEntityElement, WorldBuildingEntityElementType, GlossaryItem, BackstoryEvent, Variable, VariableType, \
    Topic
from src.main.python.plotlyst.core.template import SelectionItem
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.model.common import SelectionItemsModel
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import action, push_btn, frame, insert_before_the_end, fade_out_and_gc, \
    tool_btn, label, scrolled
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.style.text import apply_text_color
from src.main.python.plotlyst.view.widget.button import DotsMenuButton
from src.main.python.plotlyst.view.widget.display import Icon, PopupDialog
from src.main.python.plotlyst.view.widget.input import AutoAdjustableTextEdit, AutoAdjustableLineEdit, RemovalButton
from src.main.python.plotlyst.view.widget.items_editor import ItemsEditorWidget
from src.main.python.plotlyst.view.widget.timeline import TimelineWidget, BackstoryCard, TimelineTheme
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode, TreeSettings
from src.main.python.plotlyst.view.widget.world._topics import ecological_topics, cultural_topics, historical_topics, \
    linguistic_topics, technological_topics, economic_topics, infrastructural_topics, religious_topics, \
    fantastic_topics, nefarious_topics, environmental_topics


class EntityAdditionMenu(MenuWidget):
    entityTriggered = pyqtSignal(WorldBuildingEntity)

    def __init__(self, parent=None):
        super(EntityAdditionMenu, self).__init__(parent)
        self.addAction(action('Entity', IconRegistry.world_building_icon(),
                              slot=lambda: self._triggered(WorldBuildingEntityType.ABSTRACT),
                              tooltip='Any physical, human, or abstract entity in the world, e.g., location, kingdom, magic, God, etc.'))
        self.addSeparator()

        submenu = MenuWidget()
        submenu.setTitle('Link')
        submenu.setIcon(IconRegistry.from_name('fa5s.link'))
        submenu.setDisabled(True)
        submenu.addAction(action('Location', IconRegistry.location_icon()))
        submenu.addAction(action('Social group', IconRegistry.group_icon()))
        submenu.addAction(action('Character', IconRegistry.character_icon()))

        self.addMenu(submenu)

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

        entity = WorldBuildingEntity(name, icon=icon_name, type=wdType,
                                     elements=[WorldBuildingEntityElement(WorldBuildingEntityElementType.Text)])

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

        self.repo = RepositoryPersistenceManager.instance()

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
        self._novel.world.root_entity.children.append(entity)
        self.repo.update_world(self._novel)

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
        self.repo.update_world(self._novel)

    def _removeEntity(self, node: EntityNode):
        entity = node.entity()
        self.clearSelection()
        self.selectRoot()

        node.parent().parent().entity().children.remove(entity)
        fade_out_and_gc(node.parent(), node)
        self.repo.update_world(self._novel)

    def __initEntityWidget(self, entity: WorldBuildingEntity) -> EntityNode:
        node = EntityNode(entity, settings=self._settings)
        node.selectionChanged.connect(partial(self._entitySelectionChanged, node))
        node.addEntity.connect(partial(self._addEntity, node))
        node.deleted.connect(partial(self._removeEntity, node))

        self._entities[entity] = node
        return node


class WorldBuildingEntityElementWidget(QWidget):
    def __init__(self, novel: Novel, element: WorldBuildingEntityElement, parent=None, removalEnabled: bool = True,
                 menuEnabled: bool = False):
        super().__init__(parent)
        self.novel = novel
        self.element = element
        self._removalEnabled = removalEnabled
        self._menuEnabled = menuEnabled
        if removalEnabled and removalEnabled == menuEnabled:
            raise ValueError('Cannot allow both removal and menu for WorldBuildingEntityElementWidget')

        self.btnAdd = tool_btn(IconRegistry.plus_icon('grey'), transparent_=True, tooltip='Insert new block')
        self.btnAdd.installEventFilter(OpacityEventFilter(self.btnAdd))
        decr_icon(self.btnAdd)
        self.btnAdd.setHidden(True)
        retain_when_hidden(self.btnAdd)

        self.btnRemove = RemovalButton(self, colorOff='grey', colorOn='#510442', colorHover='darkgrey')
        if self._removalEnabled:
            self.installEventFilter(VisibilityToggleEventFilter(self.btnRemove, self))
        else:
            self.btnRemove.setHidden(True)

        if self._menuEnabled:
            self.btnMenu = DotsMenuButton(self)
            self.menu = MenuWidget(self.btnMenu)
            self.installEventFilter(VisibilityToggleEventFilter(self.btnMenu, self))

        self._btnCornerButtonOffsetY = 1
        self._btnCornerButtonOffsetX = 20

    def save(self):
        RepositoryPersistenceManager.instance().update_world(self.novel)

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        if self._removalEnabled:
            self.btnRemove.setGeometry(event.size().width() - self._btnCornerButtonOffsetX,
                                       self._btnCornerButtonOffsetY, 20, 20)
        elif self._menuEnabled:
            self.btnMenu.setGeometry(event.size().width() - self._btnCornerButtonOffsetX, self._btnCornerButtonOffsetY,
                                     20, 20)
        super().resizeEvent(event)

    @staticmethod
    def newWidget(novel: Novel, element: WorldBuildingEntityElement,
                  parent: Optional[
                      'WorldBuildingEntitySectionElementEditor'] = None) -> 'WorldBuildingEntityElementWidget':
        if element.type == WorldBuildingEntityElementType.Text:
            return TextElementEditor(novel, element, parent)
        elif element.type == WorldBuildingEntityElementType.Section:
            return WorldBuildingEntitySectionElementEditor(novel, element, parent)
        elif element.type == WorldBuildingEntityElementType.Header:
            return HeaderElementEditor(novel, element, parent)
        elif element.type == WorldBuildingEntityElementType.Quote:
            return QuoteElementEditor(novel, element, parent)
        elif element.type == WorldBuildingEntityElementType.Variables:
            return VariablesElementEditor(novel, element, parent)
        elif element.type == WorldBuildingEntityElementType.Highlight:
            return HighlightedTextElementEditor(novel, element, parent)
        elif element.type == WorldBuildingEntityElementType.Timeline:
            return TimelineElementEditor(novel, element, parent)
        else:
            raise ValueError(f'Unsupported WorldBuildingEntityElement type {element.type}')


class TextElementEditor(WorldBuildingEntityElementWidget):
    def __init__(self, novel: Novel, element: WorldBuildingEntityElement, parent=None):
        super().__init__(novel, element, parent, removalEnabled=True if parent else False)
        self._capitalized = False

        self.textEdit = AutoAdjustableTextEdit()
        self.textEdit.setProperty('transparent', True)
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

        vbox(self, 0, 0).addWidget(self.textEdit)
        if parent:
            margins(self, left=15)
            self.layout().addWidget(self.btnAdd, alignment=Qt.AlignmentFlag.AlignCenter)
            self.installEventFilter(VisibilityToggleEventFilter(self.btnAdd, self))
            self.btnRemove.raise_()

    def _textChanged(self):
        self.element.text = self.textEdit.toMarkdown()
        self.save()

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


class HeaderElementEditor(WorldBuildingEntityElementWidget):
    def __init__(self, novel: Novel, element: WorldBuildingEntityElement, parent=None):
        super().__init__(novel, element, parent)

        vbox(self, 0)
        margins(self, top=10, bottom=10)

        self.icon = Icon()
        self.icon.setIconSize(QSize(32, 32))
        if self.element.icon:
            self.icon.setIcon(IconRegistry.from_name(self.element.icon, '#510442'))
        self.lineTitle = AutoAdjustableLineEdit(defaultWidth=50)
        self.lineTitle.setProperty('transparent', True)
        self.lineTitle.setPlaceholderText('New section')
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

        apply_text_color(self.lineTitle, QColor('#510442'))
        # palette = self.lineTitle.palette()
        # color = QColor('#510442')
        # palette.setColor(QPalette.ColorRole.Text, color)
        # color.setAlpha(125)
        # palette.setColor(QPalette.ColorRole.PlaceholderText, color)
        # self.lineTitle.setPalette(palette)

        self.lineTitle.setText(self.element.title)

        self.lineTitle.textEdited.connect(self._titleEdited)

        self.frame = frame()
        vbox(self.frame).addWidget(group(spacer(), self.icon, self.lineTitle, spacer(), margin=0, spacing=0))
        self.layout().addWidget(self.frame)
        self.frame.setStyleSheet('''
        .QFrame {
            border-top: 1px outset #510442;
            border-bottom: 1px outset #510442;
            border-radius: 6px;
            background: #DABFA7;
        }''')

        if parent:
            self.layout().addWidget(self.btnAdd, alignment=Qt.AlignmentFlag.AlignCenter)
            self.installEventFilter(VisibilityToggleEventFilter(self.btnAdd, self))

        self._btnCornerButtonOffsetY = 7
        self.btnRemove.raise_()

    def _titleEdited(self, title: str):
        self.element.title = title
        self.save()


class QuoteElementEditor(WorldBuildingEntityElementWidget):
    def __init__(self, novel: Novel, element: WorldBuildingEntityElement, parent=None):
        super().__init__(novel, element, parent)

        vbox(self, 0, 0)
        margins(self, left=15, right=15, top=5, bottom=5)
        self.textEdit = AutoAdjustableTextEdit()
        self.textEdit.setStyleSheet(f'''
                border: 0px;
                background-color: rgba(0, 0, 0, 0);
                color: grey;
        ''')
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
        self.textEdit.setMarkdown(self.element.text)
        self.textEdit.textChanged.connect(self._quoteChanged)

        self.lineEditRef = AutoAdjustableLineEdit()
        self.lineEditRef.setFont(font)
        self.lineEditRef.setStyleSheet(f'''
                QLineEdit {{
                    border: 0px;
                    background-color: rgba(0, 0, 0, 0);
                    color: #510442;
                }}''')
        self.lineEditRef.setPlaceholderText('Source')
        self.lineEditRef.textEdited.connect(self._quoteRefEdited)
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

        if parent:
            self.layout().addWidget(self.btnAdd, alignment=Qt.AlignmentFlag.AlignCenter)
            self.installEventFilter(VisibilityToggleEventFilter(self.btnAdd, self))

        self.btnRemove.raise_()

    def _quoteChanged(self):
        self.element.text = self.textEdit.toMarkdown()
        self.save()

    def _quoteRefEdited(self, text: str):
        self.element.ref = text
        self.save()


class VariableEditorDialog(PopupDialog):
    def __init__(self, variable: Optional[Variable] = None, parent=None):
        super().__init__(parent)
        self._variable: Optional[Variable] = variable

        self.lineKey = QLineEdit()
        self.lineKey.setProperty('white-bg', True)
        self.lineKey.setProperty('rounded', True)
        self.lineKey.setPlaceholderText('Key')
        self.lineKey.textChanged.connect(self._keyChanged)

        self.lineValue = QLineEdit()
        self.lineValue.setProperty('white-bg', True)
        self.lineValue.setProperty('rounded', True)
        self.lineValue.setPlaceholderText('Value')

        self.wdgTitle = QWidget()
        hbox(self.wdgTitle)
        self.wdgTitle.layout().addWidget(self.btnReset, alignment=Qt.AlignmentFlag.AlignRight)

        self.btnConfirm = push_btn(text='Confirm', properties=['base', 'positive'])
        sp(self.btnConfirm).h_exp()
        self.btnConfirm.clicked.connect(self.accept)
        self.btnConfirm.setDisabled(True)
        self.btnConfirm.installEventFilter(
            DisabledClickEventFilter(self.btnConfirm, lambda: qtanim.shake(self.lineKey)))

        if self._variable:
            self.lineKey.setText(self._variable.key)

        self.frame.layout().addWidget(self.wdgTitle)
        self.frame.layout().addWidget(self.lineKey)
        self.frame.layout().addWidget(self.lineValue)
        self.frame.layout().addWidget(self.btnConfirm)

    def display(self) -> Optional[Variable]:
        result = self.exec()

        if result == QDialog.DialogCode.Accepted:
            if self._variable is None:
                self._variable = Variable(self.lineKey.text(), VariableType.Text, '')
            self._variable.key = self.lineKey.text()
            self._variable.value = self.lineValue.text()

            return self._variable

    @classmethod
    def edit(cls, variable: Optional[Variable] = None) -> Optional[Variable]:
        return cls.popup(variable)

    def _keyChanged(self, key: str):
        self.btnConfirm.setEnabled(len(key) > 0)


class VariableWidget(QWidget):
    def __init__(self, variable: Variable, parent=None):
        super().__init__(parent)
        self.variable = variable
        vbox(self)
        self.lblKey = label(variable.key, bold=True)
        self.valueField = label(variable.value)
        self.layout().addWidget(self.lblKey, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(self.valueField, alignment=Qt.AlignmentFlag.AlignLeft)

        self.installEventFilter(OpacityEventFilter(self, 0.7, 1.0))
        pointy(self)

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.edit()

    def edit(self):
        edited = VariableEditorDialog.edit(self.variable)
        if edited:
            self.lblKey.setText(self.variable.key)
            self.valueField.setText(self.variable.value)


class VariablesElementEditor(WorldBuildingEntityElementWidget):
    def __init__(self, novel: Novel, element: WorldBuildingEntityElement, parent=None):
        super().__init__(novel, element, parent, removalEnabled=False, menuEnabled=True)
        vbox(self, 5)
        margins(self, right=15)

        self._btnCornerButtonOffsetX = 37
        self._btnCornerButtonOffsetY = 7

        self.frame = frame()
        vbox(self.frame, 10)
        self.frame.setStyleSheet('''
        .QFrame {
            border: 1px outset #510442;
            border-radius: 6px;
            background: #DABFA7;
        }
        ''')

        self.btnAdd = tool_btn(IconRegistry.plus_icon('grey'), transparent_=True)
        self.btnAdd.installEventFilter(OpacityEventFilter(self.btnAdd, enterOpacity=0.8))
        self.btnAdd.clicked.connect(self._addNew)
        self._variables: Dict[Variable, VariableWidget] = {}
        for variable in self.element.variables:
            wdg = VariableWidget(variable)
            self._variables[variable] = wdg
            self.frame.layout().addWidget(wdg)

        self.frame.layout().addWidget(self.btnAdd)

        self.layout().addWidget(self.frame)

        self.btnMenu.raise_()
        self.menu.aboutToShow.connect(self._fillMenu)

    def _addNew(self):
        variable = VariableEditorDialog.edit()
        if variable:
            self.element.variables.append(variable)
            wdg = VariableWidget(variable)
            self._variables[variable] = wdg
            insert_before_the_end(self.frame, wdg)
            qtanim.fade_in(wdg, teardown=lambda: wdg.setGraphicsEffect(None))
            self.save()

    def _edit(self, variable: Variable):
        self._variables[variable].edit()

    def _remove(self, variable: Variable):
        if self.menu.isVisible():
            self.menu.close()
        wdg = self._variables.pop(variable)
        fade_out_and_gc(self.frame, wdg)
        self.element.variables.remove(variable)
        self.save()

    def _fillMenu(self):
        self.menu.clear()
        wdg = QWidget()
        grid_layout: QGridLayout = grid(wdg)
        for i, variable in enumerate(self.element.variables):
            grid_layout.addWidget(label(variable.key), i, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignLeft)

            edit_btn = tool_btn(IconRegistry.edit_icon(), tooltip=f'Edit {variable.key}', transparent_=True)
            edit_btn.clicked.connect(partial(self._edit, variable))
            grid_layout.addWidget(edit_btn, i, 2)

            remove_btn = tool_btn(IconRegistry.trash_can_icon(), transparent_=True, tooltip=f'Remove {variable.key}')
            remove_btn.clicked.connect(partial(self._remove, variable))
            grid_layout.addWidget(remove_btn, i, 3)
        self.menu.addWidget(wdg)
        self.menu.addSeparator()
        self.menu.addAction(action('Remove all variables', IconRegistry.trash_can_icon(), slot=self.btnRemove.click))


class HighlightedTextElementEditor(WorldBuildingEntityElementWidget):
    def __init__(self, novel: Novel, element: WorldBuildingEntityElement, parent=None):
        super().__init__(novel, element, parent)
        vbox(self, 5)
        margins(self, right=15)

        self.frame = frame()
        sp(self.frame).v_max()
        self.frame.setStyleSheet('''
                        .QFrame {
                            border: 1px outset #510442;
                            border-left: 3px outset #510442;
                            border-radius: 4px;
                            background: #E3D0BD;
                        }''')
        self.textEdit = AutoAdjustableTextEdit()
        font: QFont = self.textEdit.font()
        font.setPointSize(14)
        self.textEdit.setFont(font)
        self.textEdit.setPlaceholderText('Begin writing...')
        self.textEdit.setProperty('transparent', True)
        self.textEdit.setMarkdown(self.element.text)
        self.textEdit.textChanged.connect(self._textChanged)
        vbox(self.frame, 10).addWidget(self.textEdit)

        self.layout().addWidget(self.frame)

    def _textChanged(self):
        self.element.text = self.textEdit.toMarkdown()
        self.save()


class EntityTimelineCard(BackstoryCard):
    def __init__(self, backstory: BackstoryEvent, parent=None):
        super().__init__(backstory, parent)
        self.refresh()


class EntityTimelineWidget(TimelineWidget):
    def __init__(self, element: WorldBuildingEntityElement, parent=None):
        super().__init__(TimelineTheme(timeline_color='#510442', card_bg_color='#E3D0BD'), parent)
        self.element = element
        self.refresh()

    @overrides
    def events(self) -> List[BackstoryEvent]:
        return self.element.events

    @overrides
    def cardClass(self):
        return EntityTimelineCard


class TimelineElementEditor(WorldBuildingEntityElementWidget):
    def __init__(self, novel: Novel, element: WorldBuildingEntityElement, parent=None):
        super().__init__(novel, element, parent)

        self.timeline = EntityTimelineWidget(element)
        vbox(self, 0, 0).addWidget(self.timeline)
        self.timeline.changed.connect(self.save)

        self.btnRemove.raise_()


class WorldBuildingEntitySectionElementEditor(WorldBuildingEntityElementWidget):
    removed = pyqtSignal()

    def __init__(self, novel: Novel, element: WorldBuildingEntityElement, parent=None):
        super().__init__(novel, element, parent, removalEnabled=False)

        vbox(self, 0)
        for element in self.element.blocks:
            wdg = self.__initBlockWidget(element)
            self.layout().addWidget(wdg)

    def _addBlock(self, wdg: WorldBuildingEntityElementWidget, type_: WorldBuildingEntityElementType):
        element = WorldBuildingEntityElement(type_)
        newBlockWdg = self.__initBlockWidget(element)

        index = self.element.blocks.index(wdg.element)
        if index == len(self.element.blocks) - 1:
            self.element.blocks.append(element)
            self.layout().addWidget(newBlockWdg)
        else:
            self.element.blocks.insert(index + 1, element)
            self.layout().insertWidget(index + 1, newBlockWdg)
        qtanim.fade_in(newBlockWdg, teardown=lambda: newBlockWdg.setGraphicsEffect(None))

    def _removeBlock(self, widget: WorldBuildingEntityElementWidget):
        if isinstance(widget, HeaderElementEditor):
            self.removed.emit()
            return

        self.element.blocks.remove(widget.element)
        self.save()
        fade_out_and_gc(self, widget)

    def __initBlockWidget(self, element: WorldBuildingEntityElement) -> WorldBuildingEntityElementWidget:
        wdg = WorldBuildingEntityElementWidget.newWidget(self.novel, element, self)
        menu = MainBlockAdditionMenu(wdg.btnAdd)
        menu.newBlockSelected.connect(partial(self._addBlock, wdg))
        wdg.btnRemove.clicked.connect(partial(self._removeBlock, wdg))

        return wdg


class TopicSelectionDialog(PopupDialog):
    DEFAULT_SELECT_BTN_TEXT: str = 'Select worldbuilding topics'

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selectedTopics = []

        self.frame.layout().addWidget(self.btnReset, alignment=Qt.AlignmentFlag.AlignRight)
        self._scrollarea, self._wdgCenter = scrolled(self.frame, frameless=True, h_on=False)
        vbox(self._wdgCenter, 10)
        # self._wdgCenter.setStyleSheet('QWidget {background: #ede0d4;}')
        self.setMinimumWidth(350)

        self._addSection('Ecological', ecological_topics)
        self._addSection('Cultural', cultural_topics)
        self._addSection('Historical', historical_topics)
        self._addSection('Linguistic', linguistic_topics)
        self._addSection('Technological', technological_topics)
        self._addSection('Economic', economic_topics)
        self._addSection('Infrastructural', infrastructural_topics)
        self._addSection('Religious', religious_topics)
        self._addSection('Fantastic', fantastic_topics)
        self._addSection('Nefarious', nefarious_topics)
        self._addSection('Environmental', environmental_topics)

        self.btnSelect = push_btn(IconRegistry.ok_icon('white'), self.DEFAULT_SELECT_BTN_TEXT,
                                  properties=['positive', 'base'])
        self.btnSelect.setDisabled(True)
        self.btnSelect.clicked.connect(self.accept)

        self._wdgCenter.layout().addWidget(vspacer())
        self.frame.layout().addWidget(self.btnSelect)

    def display(self) -> List[Topic]:
        result = self.exec()
        if result == QDialog.DialogCode.Accepted:
            return self._selectedTopics

        return []

    def _addSection(self, header: str, topics: List[Topic]):
        self._wdgCenter.layout().addWidget(label(header, bold=True), alignment=Qt.AlignmentFlag.AlignLeft)
        wdg = QWidget()
        flow(wdg)
        margins(wdg, left=10)

        for topic in topics:
            btn = tool_btn(IconRegistry.from_name(topic.icon), topic.description, checkable=True)
            btn.setText(topic.text)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.toggled.connect(partial(self._toggled, topic))
            btn.setStyleSheet('''
            QToolButton {
                border: 1px hidden lightgrey;
                border-radius: 10px;
            }
            QToolButton:hover:!checked {
                background: #FCF5FE;
            }
            QToolButton:checked {
                background: #D4B8E0;
            }
            ''')
            wdg.layout().addWidget(btn)

        self._wdgCenter.layout().addWidget(wdg)

    def _toggled(self, topic: Topic, checked: bool):
        if checked:
            self._selectedTopics.append(topic)
        else:
            self._selectedTopics.remove(topic)

        self.btnSelect.setEnabled(len(self._selectedTopics) > 0)
        if self._selectedTopics:
            self.btnSelect.setText(f'{self.DEFAULT_SELECT_BTN_TEXT} ({len(self._selectedTopics)})')
        else:
            self.btnSelect.setText(self.DEFAULT_SELECT_BTN_TEXT)


class SectionAdditionMenu(MenuWidget):
    newSectionSelected = pyqtSignal()
    topicSectionSelected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.addAction(action('New section', IconRegistry.plus_icon('grey'), slot=self.newSectionSelected))
        self.addSeparator()
        self.addAction(
            action('Select topic...', IconRegistry.world_building_icon('grey'), slot=self.topicSectionSelected))


class MainBlockAdditionMenu(MenuWidget):
    newBlockSelected = pyqtSignal(WorldBuildingEntityElementType)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.addAction(action('Text', IconRegistry.from_name('mdi.text'),
                              slot=lambda: self.newBlockSelected.emit(WorldBuildingEntityElementType.Text)))
        self.addAction(action('Quote', IconRegistry.from_name('ei.quote-right-alt'),
                              slot=lambda: self.newBlockSelected.emit(WorldBuildingEntityElementType.Quote)))
        self.addAction(action('Timeline', IconRegistry.from_name('mdi.timeline'),
                              slot=lambda: self.newBlockSelected.emit(WorldBuildingEntityElementType.Timeline)))


class SideBlockAdditionMenu(MenuWidget):
    newSideBlockSelected = pyqtSignal(WorldBuildingEntityElementType)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.addAction(action('Variables', IconRegistry.from_name('mdi.alpha-v-box-outline'),
                              slot=lambda: self.newSideBlockSelected.emit(WorldBuildingEntityElementType.Variables)))
        self.addAction(action('Highlighted text', IconRegistry.from_name('mdi6.card-text'),
                              slot=lambda: self.newSideBlockSelected.emit(WorldBuildingEntityElementType.Highlight)))


class WorldBuildingEntityEditor(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._entity: Optional[WorldBuildingEntity] = None

        self.wdgEditorMiddle = QWidget()
        vbox(self.wdgEditorMiddle, spacing=10)
        margins(self.wdgEditorMiddle, left=15, bottom=20)
        self.wdgEditorSide = QWidget()
        vbox(self.wdgEditorSide)
        margins(self.wdgEditorSide, left=10, right=15)

        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.wdgEditorMiddle)
        splitter.addWidget(self.wdgEditorSide)
        splitter.setSizes([500, 170])

        vbox(self, 0, 0).addWidget(splitter)

        self.repo = RepositoryPersistenceManager.instance()

    def setEntity(self, entity: WorldBuildingEntity):
        self._entity = entity

        clear_layout(self.wdgEditorMiddle)
        clear_layout(self.wdgEditorSide)

        for element in self._entity.elements:
            self._addElement(element)

        for element in self._entity.side_elements:
            self._addElement(element, False)

        self._addPlaceholder()
        self._addPlaceholder(False)
        self.wdgEditorSide.layout().addWidget(vspacer())

    def _addPlaceholder(self, middle: bool = True):
        wdg = push_btn(IconRegistry.plus_icon('grey'), 'Add section' if middle else 'Add block', transparent_=True)
        if middle:
            menu = SectionAdditionMenu(wdg)
            menu.newSectionSelected.connect(self._addNewSection)
            menu.topicSectionSelected.connect(self._selectNewTopic)
        else:
            menu = SideBlockAdditionMenu(wdg)
            menu.newSideBlockSelected.connect(self._addNewSideBlock)
        wdg.installEventFilter(OpacityEventFilter(wdg, enterOpacity=0.8))
        if middle:
            self.wdgEditorMiddle.layout().addWidget(wdg, alignment=Qt.AlignmentFlag.AlignLeft)
        else:
            self.wdgEditorSide.layout().addWidget(wdg, alignment=Qt.AlignmentFlag.AlignCenter)

    def _addElement(self, element: WorldBuildingEntityElement, middle: bool = True):
        wdg = self.__initElementWidget(element, middle)

        if middle:
            self.wdgEditorMiddle.layout().addWidget(wdg)
        else:
            self.wdgEditorSide.layout().addWidget(wdg)

    def _addNewSection(self, topic: Optional[Topic] = None):
        header = WorldBuildingEntityElement(WorldBuildingEntityElementType.Header)
        element = WorldBuildingEntityElement(WorldBuildingEntityElementType.Section, blocks=[
            header,
            WorldBuildingEntityElement(WorldBuildingEntityElementType.Text)
        ])
        if topic:
            element.ref = topic.id
            element.title = topic.text
            header.title = topic.text
            header.icon = topic.icon
        wdg = self.__initElementWidget(element, True)
        insert_before_the_end(self.wdgEditorMiddle, wdg)
        qtanim.fade_in(wdg, teardown=lambda: wdg.setGraphicsEffect(None))

        self._entity.elements.append(element)
        self.repo.update_world(self._novel)

    def _selectNewTopic(self):
        topics = TopicSelectionDialog.popup()
        # topics = dialog.display()
        if topics:
            for topic in topics:
                self._addNewSection(topic)

    def _removeSection(self, wdg: WorldBuildingEntityElementWidget):
        self._entity.elements.remove(wdg.element)
        fade_out_and_gc(self.wdgEditorMiddle, wdg)
        self.repo.update_world(self._novel)

    def _addNewSideBlock(self, type_: WorldBuildingEntityElementType):
        element = WorldBuildingEntityElement(type_)
        wdg = self.__initElementWidget(element, False)

        insert_before_the_end(self.wdgEditorSide, wdg, 2)
        qtanim.fade_in(wdg, teardown=lambda: wdg.setGraphicsEffect(None))

        self._entity.side_elements.append(element)
        self.repo.update_world(self._novel)

    def _removeSideBlock(self, wdg: WorldBuildingEntityElementWidget):
        self._entity.side_elements.remove(wdg.element)
        fade_out_and_gc(self.wdgEditorSide, wdg)
        self.repo.update_world(self._novel)

    def __initElementWidget(self, element: WorldBuildingEntityElement,
                            middle: bool) -> WorldBuildingEntityElementWidget:
        wdg = WorldBuildingEntityElementWidget.newWidget(self._novel, element)
        if middle and isinstance(wdg, WorldBuildingEntitySectionElementEditor):
            wdg.removed.connect(partial(self._removeSection, wdg))
        elif not middle:
            wdg.btnRemove.clicked.connect(partial(self._removeSideBlock, wdg))

        return wdg


class GlossaryModel(SelectionItemsModel):
    glossaryRemoved = pyqtSignal()

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._items = list(self._novel.world.glossary.values())

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self._items)

    @overrides
    def columnCount(self, parent: QModelIndex = None) -> int:
        return 4

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.FontRole:
            font = QApplication.font()
            font.setPointSize(13)
            if index.column() == self.ColName:
                font.setBold(True)
            return font
        if index.column() == self.ColName:
            if role == Qt.ItemDataRole.DisplayRole:
                return self._items[index.row()].key
            if role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignTop
        if index.column() == 3:
            if role == Qt.ItemDataRole.DisplayRole:
                return self._items[index.row()].text
        return super().data(index, role)

    def refresh(self):
        self._items = list(self._novel.world.glossary.values())
        self.modelReset.emit()

    @overrides
    def _newItem(self) -> QModelIndex:
        pass

    @overrides
    def _insertItem(self, row: int) -> QModelIndex:
        pass

    @overrides
    def item(self, index: QModelIndex) -> SelectionItem:
        return self._items[index.row()]

    @overrides
    def remove(self, index: QModelIndex):
        glossary = self._items[index.row()]
        self._novel.world.glossary.pop(glossary.key)
        self.refresh()
        self.glossaryRemoved.emit()


class GlossaryEditorDialog(PopupDialog):
    def __init__(self, glossary: Optional[GlossaryItem] = None, parent=None):
        super().__init__(parent)
        self._glossary = glossary

        self.lineKey = QLineEdit()
        self.lineKey.setProperty('white-bg', True)
        self.lineKey.setProperty('rounded', True)
        self.lineKey.setPlaceholderText('Term')
        self.lineKey.textChanged.connect(self._keyChanged)

        self.textDefinition = AutoAdjustableTextEdit(height=150)
        self.textDefinition.setProperty('white-bg', True)
        self.textDefinition.setProperty('rounded', True)
        self.textDefinition.setPlaceholderText('Define term')

        self.wdgTitle = QWidget()
        hbox(self.wdgTitle)
        self.wdgTitle.layout().addWidget(self.btnReset, alignment=Qt.AlignmentFlag.AlignRight)

        self.btnConfirm = push_btn(text='Confirm', properties=['base', 'positive'])
        sp(self.btnConfirm).h_exp()
        self.btnConfirm.clicked.connect(self.accept)
        self.btnConfirm.setDisabled(True)
        self.btnConfirm.installEventFilter(
            DisabledClickEventFilter(self.btnConfirm, lambda: qtanim.shake(self.lineKey)))

        if self._glossary:
            self.lineKey.setText(self._glossary.key)
            self.textDefinition.setText(self._glossary.text)

        self.frame.layout().addWidget(self.wdgTitle)
        self.frame.layout().addWidget(self.lineKey)
        self.frame.layout().addWidget(self.textDefinition)
        self.frame.layout().addWidget(self.btnConfirm)

    def display(self) -> GlossaryItem:
        result = self.exec()

        if result == QDialog.DialogCode.Accepted:
            if self._glossary is None:
                self._glossary = GlossaryItem('')
            self._glossary.key = self.lineKey.text()
            self._glossary.text = self.textDefinition.toMarkdown().strip()

            return self._glossary

    def _keyChanged(self, key: str):
        self.btnConfirm.setEnabled(len(key) > 0)

    @classmethod
    def edit(cls, glossary: Optional[GlossaryItem] = None) -> Optional[GlossaryItem]:
        return cls.popup(glossary)


class WorldBuildingGlossaryEditor(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        vbox(self)
        self.editor = ItemsEditorWidget()
        self.editor.setInlineEditionEnabled(False)
        self.editor.setInlineAdditionEnabled(False)
        self.editor.btnAdd.clicked.connect(self._addNew)
        self.editor.editRequested.connect(self._edit)
        self.glossaryModel = GlossaryModel(self._novel)
        self.editor.setModel(self.glossaryModel)
        self.editor.tableView.setColumnHidden(GlossaryModel.ColIcon, True)
        self.editor.tableView.setColumnWidth(GlossaryModel.ColName, 200)
        self.editor.tableView.setContentsMargins(10, 15, 10, 5)

        self.glossaryModel.modelReset.connect(self.editor.tableView.resizeRowsToContents)
        self.glossaryModel.glossaryRemoved.connect(self._save)

        self.editor.tableView.setStyleSheet('QTableView::item { border: 0px; padding: 5px; }')
        self.editor.tableView.resizeRowsToContents()
        self.editor.tableView.setAlternatingRowColors(True)
        self.editor.tableView.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        self.layout().addWidget(self.editor)
        self.repo = RepositoryPersistenceManager.instance()

    def _addNew(self):
        glossary = GlossaryEditorDialog.edit()
        if glossary:
            self._updateGlossary(glossary)

    def _edit(self, item: GlossaryItem):
        edited_glossary = GlossaryEditorDialog.edit(item)
        if edited_glossary:
            self._novel.world.glossary.pop(item.key)
            self._updateGlossary(edited_glossary)

    def _updateGlossary(self, glossary: GlossaryItem):
        self._novel.world.glossary[glossary.key] = glossary
        self.glossaryModel.refresh()
        self._save()

    def _save(self):
        self.repo.update_world(self._novel)
