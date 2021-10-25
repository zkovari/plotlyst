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
import pickle
from abc import abstractmethod
from typing import List, Set, Optional

import qtawesome
from PyQt5.QtCore import Qt, QObject, QEvent, QMimeData, QByteArray
from PyQt5.QtGui import QDrag, QMouseEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent
from PyQt5.QtWidgets import QSizePolicy, QWidget, QListView, QFrame, QToolButton, QVBoxLayout, QHBoxLayout, QHeaderView
from overrides import overrides

from src.main.python.plotlyst.core.domain import Scene, SelectionItem, Novel, SceneGoal, SceneType, \
    SceneStructureItemType, SceneStructureAgenda, SceneStructureItem, Conflict
from src.main.python.plotlyst.model.common import SelectionItemsModel
from src.main.python.plotlyst.model.novel import NovelPlotsModel, NovelTagsModel
from src.main.python.plotlyst.model.scenes_model import SceneGoalsModel, SceneConflictsModel
from src.main.python.plotlyst.view.generated.scene_filter_widget_ui import Ui_SceneFilterWidget
from src.main.python.plotlyst.view.generated.scene_structure_editor_widget_ui import Ui_SceneStructureWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterConflictWidget
from src.main.python.plotlyst.view.widget.input import AutoAdjustableTextEdit
from src.main.python.plotlyst.view.widget.labels import LabelsEditorWidget, GoalLabel, ConflictLabel


class SceneGoalsWidget(LabelsEditorWidget):

    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        self.novel = novel
        self.scene_structure_item = scene_structure_item
        super(SceneGoalsWidget, self).__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.setValue([x.text for x in self.scene_structure_item.goals])
        self.btnEdit.setIcon(IconRegistry.goal_icon())
        self.btnEdit.setText('Track goals')
        self._wdgLabels.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.setStyleSheet('SceneGoalsWidget {border: 0px;}')

    @overrides
    def _initModel(self) -> SelectionItemsModel:
        model = SceneGoalsModel(self.novel, self.scene_structure_item)
        model.setCheckable(True, SceneGoalsModel.ColName)
        return model

    @overrides
    def items(self) -> List[SelectionItem]:
        return self.novel.scene_goals

    @overrides
    def _addItems(self, items: Set[SceneGoal]):
        for item in items:
            self._wdgLabels.addLabel(GoalLabel(item))
        self.scene_structure_item.goals.clear()
        self.scene_structure_item.goals.extend(items)


class SceneConflictsWidget(LabelsEditorWidget):
    def __init__(self, novel: Novel, scene: Scene, scene_structure_item: SceneStructureItem, parent=None):
        self.novel = novel
        self.scene = scene
        self.scene_structure_item = scene_structure_item
        super(SceneConflictsWidget, self).__init__(parent=parent)
        self.setValue([x.text for x in self.scene_structure_item.conflicts])
        self.btnEdit.setIcon(IconRegistry.conflict_icon())
        self.btnEdit.setText('Track conflicts')
        self._wdgLabels.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.setStyleSheet('SceneConflictsWidget {border: 0px;}')

    @overrides
    def _initModel(self) -> SelectionItemsModel:
        return SceneConflictsModel(self.novel, self.scene, self.scene_structure_item)

    @overrides
    def _initPopupWidget(self) -> QWidget:
        widget = CharacterConflictWidget(self.novel, self.scene, self.scene_structure_item)
        widget.tblConflicts.setModel(self._model)
        widget.tblConflicts.horizontalHeader().setSectionResizeMode(SceneConflictsModel.ColIcon,
                                                                    QHeaderView.ResizeToContents)
        widget.tblConflicts.horizontalHeader().setSectionResizeMode(SceneConflictsModel.ColName,
                                                                    QHeaderView.Stretch)
        return widget

    @overrides
    def items(self) -> List[SelectionItem]:
        return [x for x in self.novel.conflicts if x.character_id == self.scene.pov.id]

    @overrides
    def _addItems(self, items: Set[Conflict]):
        for item in items:
            self._wdgLabels.addLabel(ConflictLabel(self.novel, item))
        self.scene_structure_item.conflicts.clear()
        self.scene_structure_item.conflicts.extend(items)


class _SceneLabelsEditor(LabelsEditorWidget):

    def __init__(self, novel: Novel, parent=None):
        self.novel = novel
        super().__init__(parent=parent)

    @overrides
    def _initPopupWidget(self) -> QWidget:
        _view = QListView()
        _view.setModel(self._model)
        _view.setModelColumn(SelectionItemsModel.ColName)
        return _view

    @abstractmethod
    def _initModel(self) -> SelectionItemsModel:
        pass

    @abstractmethod
    def items(self) -> List[SelectionItem]:
        pass


class SceneDramaticQuestionsWidget(_SceneLabelsEditor):

    @overrides
    def _initModel(self) -> SelectionItemsModel:
        model = NovelPlotsModel(self.novel)
        model.setEditable(False)
        return model

    @overrides
    def items(self) -> List[SelectionItem]:
        return self.novel.plots


class SceneTagsWidget(_SceneLabelsEditor):

    def __init__(self, novel: Novel, parent=None):
        super(SceneTagsWidget, self).__init__(novel, parent)
        self.btnEdit.setIcon(IconRegistry.tag_plus_icon())

    @overrides
    def _initModel(self) -> SelectionItemsModel:
        model = NovelTagsModel(self.novel)
        model.setEditable(False)
        return model

    @overrides
    def items(self) -> List[SelectionItem]:
        return self.novel.tags


class SceneFilterWidget(QFrame, Ui_SceneFilterWidget):
    def __init__(self, novel: Novel, parent=None):
        super(SceneFilterWidget, self).__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.povFilter.setExclusive(False)
        self.povFilter.setCharacters(self.novel.pov_characters())

        self.tabWidget.setTabIcon(self.tabWidget.indexOf(self.tabPov), IconRegistry.character_icon())


class _PlaceHolder(QToolButton):
    def __init__(self):
        super(_PlaceHolder, self).__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setIcon(qtawesome.icon('ei.plus-sign', color='lightgrey'))
        self.setText('<Drop here>')
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setStyleSheet('''
                background-color: rgb(255, 255, 255);
                border: 0px;
                color: lightgrey;''')

    @overrides
    def parent(self) -> QWidget:
        return super(_PlaceHolder, self).parent()


def is_placeholder(widget: QWidget) -> bool:
    return isinstance(widget, _PlaceHolder)


class SceneStructureItemWidget(QWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, vertical: bool = True, parent=None):
        super(SceneStructureItemWidget, self).__init__(parent)
        self.novel = novel
        self.scene_structure_item = scene_structure_item

        if vertical:
            self._layout = QVBoxLayout()
        else:
            self._layout = QHBoxLayout()
        self._layout.setSpacing(3)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self._layout)

        self.text = AutoAdjustableTextEdit()
        self.text.setText(self.scene_structure_item.text)
        self._layout.addWidget(self.text)

    def sceneStructureItem(self) -> SceneStructureItem:
        self.scene_structure_item.text = self.text.toPlainText()
        return self.scene_structure_item


class SceneGoalItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneGoalItemWidget, self).__init__(novel, scene_structure_item, parent=parent)
        self._layout.insertWidget(0, SceneGoalsWidget(self.novel, self.scene_structure_item))
        self.text.setPlaceholderText('Goal')


class SceneConflictItemWidget(SceneStructureItemWidget):
    def __init__(self, novel: Novel, scene: Scene, scene_structure_item: SceneStructureItem, parent=None):
        super(SceneConflictItemWidget, self).__init__(novel, scene_structure_item, parent=parent)
        self._layout.insertWidget(0, SceneConflictsWidget(self.novel, scene, self.scene_structure_item))
        self.text.setPlaceholderText('Conflict')

        # action = QWidgetAction(self.btnAddConflict)
        # self._character_conflict_widget = CharacterConflictWidget(self.novel, self.scene)
        # self._character_conflict_widget.new_conflict_added.connect(self._new_conflict)
        # self._character_conflict_widget.conflict_selection_changed.connect(self._conflicts_changed)
        # action.setDefaultWidget(self._character_conflict_widget)
        # menu = QMenu(self.ui.btnAddConflict)
        # menu.addAction(action)
        # self.ui.btnAddConflict.setMenu(menu)
        # self._conflicts_changed()


class SceneStructureWidget(QWidget, Ui_SceneStructureWidget):
    MimeType: str = 'application/structure-item'

    def __init__(self, parent=None):
        super(SceneStructureWidget, self).__init__(parent)
        self.setupUi(self)
        self._dragged: Optional[QToolButton] = None
        self._target_to_drop: Optional[QWidget] = None

        self.novel: Optional[Novel] = None
        self.scene: Optional[Scene] = None

        self.btnInventory.setIcon(IconRegistry.from_name('mdi.file-tree-outline'))

        self.rbScene.setIcon(IconRegistry.action_scene_icon())
        self.rbSequel.setIcon(IconRegistry.reaction_scene_icon())
        self.rbCustom.setIcon(IconRegistry.from_name('mdi.arrow-decision'))

        self.btnSceneIcon.setIcon(IconRegistry.action_scene_icon())
        self.btnSequelIcon.setIcon(IconRegistry.reaction_scene_icon())
        self.btnGoal.setIcon(IconRegistry.goal_icon())
        self.btnConflict.setIcon(IconRegistry.conflict_icon())
        self.btnOutcome.setIcon(IconRegistry.disaster_icon())
        self.btnBeginningIcon.setIcon(IconRegistry.cause_icon())
        self.btnMiddleIcon.setIcon(IconRegistry.from_name('mdi.ray-vertex'))
        self.btnEndIcon.setIcon(IconRegistry.from_name('mdi.ray-end'))

        self.btnReaction.setIcon(IconRegistry.reaction_icon())
        self.btnDilemma.setIcon(IconRegistry.dilemma_icon())
        self.btnDecision.setIcon(IconRegistry.decision_icon())

        self._addPlaceholder(self.wdgBeginning)
        self._addPlaceholder(self.wdgMiddle)
        self._addPlaceholder(self.wdgEnd)

        self.btnGoal.installEventFilter(self)
        self.btnConflict.installEventFilter(self)
        self.btnOutcome.installEventFilter(self)
        self.btnReaction.installEventFilter(self)
        self.btnDilemma.installEventFilter(self)
        self.btnDecision.installEventFilter(self)

    def setScene(self, novel: Novel, scene: Scene):
        self.novel = novel
        self.scene = scene

        self.clear()
        self.btnInventory.setChecked(False)

        if self.scene.type == SceneType.ACTION:
            self.rbScene.setChecked(True)
        elif self.scene.type == SceneType.REACTION:
            self.rbSequel.setChecked(True)
        else:
            self.btnInventory.setChecked(True)
            self.rbCustom.setChecked(True)

        if scene.agendas and scene.agendas[0].items:
            widgets_per_parts = {1: self.wdgBeginning, 2: self.wdgMiddle, 3: self.wdgEnd}

            for item in scene.agendas[0].items:
                if item.type == SceneStructureItemType.GOAL:
                    widget = SceneGoalItemWidget(self.novel, item)
                elif item.type == SceneStructureItemType.CONFLICT:
                    widget = SceneConflictItemWidget(self.novel, self.scene, item)
                else:
                    widget = SceneStructureItemWidget(self.novel, item)
                widgets_per_parts.get(item.part, self.wdgEnd).layout().addWidget(widget)

        if not self.wdgBeginning.layout().count():
            self._addPlaceholder(self.wdgBeginning)
        if not self.wdgMiddle.layout().count():
            self._addPlaceholder(self.wdgMiddle)
        if not self.wdgEnd.layout().count():
            self._addPlaceholder(self.wdgEnd)

        self.btnGroupType.buttonClicked.connect(self._type_changed)

    def clear(self):
        for widget in [self.wdgBeginning, self.wdgMiddle, self.wdgEnd]:
            while widget.layout().count():
                item = widget.layout().takeAt(0)
                if item:
                    item.widget().deleteLater()

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        self._dragged = watched
        if event.type() == QEvent.MouseButtonPress:
            self.mousePressEvent(event)
        elif event.type() == QEvent.MouseMove:
            self.mouseMoveEvent(event)
        elif event.type() == QEvent.MouseButtonRelease:
            self.mouseReleaseEvent(event)
        elif event.type() == QEvent.DragEnter:
            self._target_to_drop = watched
            self.dragMoveEvent(event)
        elif event.type() == QEvent.Drop:
            self.dropEvent(event)
            self._target_to_drop = None
        return super().eventFilter(watched, event)

    @overrides
    def mousePressEvent(self, event: QMouseEvent):
        self._dragged = None

    @overrides
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton and self._dragged and self._dragged.isEnabled():
            drag = QDrag(self._dragged)
            pix = self._dragged.grab()
            mimedata = QMimeData()
            mimedata.setData(self.MimeType, QByteArray(pickle.dumps(self._buttonType(self._dragged))))
            drag.setMimeData(mimedata)
            drag.setPixmap(pix)
            drag.setHotSpot(event.pos())
            drag.destroyed.connect(self._dragDestroyed)
            drag.exec_()

    def agendas(self) -> List[SceneStructureAgenda]:
        agenda = SceneStructureAgenda()
        self._collect_agenda_items(agenda, self.wdgBeginning, 1)
        self._collect_agenda_items(agenda, self.wdgMiddle, 2)
        self._collect_agenda_items(agenda, self.wdgEnd, 3)
        return [agenda]

    def _collect_agenda_items(self, agenda: SceneStructureAgenda, widget: QWidget, part: int):
        for i in range(widget.layout().count()):
            item = widget.layout().itemAt(i)
            if isinstance(item.widget(), SceneStructureItemWidget):
                structure_item: SceneStructureItem = item.widget().sceneStructureItem()
                structure_item.part = part
                agenda.items.append(structure_item)

    def _buttonType(self, dragged: QToolButton) -> SceneStructureItemType:
        if dragged is self.btnGoal:
            return SceneStructureItemType.GOAL
        if dragged is self.btnConflict:
            return SceneStructureItemType.CONFLICT
        if dragged is self.btnOutcome:
            return SceneStructureItemType.OUTCOME
        if dragged is self.btnReaction:
            return SceneStructureItemType.REACTION
        if dragged is self.btnDilemma:
            return SceneStructureItemType.DILEMMA
        if dragged is self.btnOutcome:
            return SceneStructureItemType.OUTCOME

    @overrides
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat(self.MimeType):
            event.accept()
        else:
            event.ignore()

    @overrides
    def dragMoveEvent(self, event: QDragMoveEvent):
        if not self._target_to_drop:
            event.ignore()
            return
        if is_placeholder(self._target_to_drop):
            event.accept()
        else:
            event.ignore()

    @overrides
    def dropEvent(self, event: QDropEvent):
        if not self._target_to_drop:
            event.ignore()
            return

        if is_placeholder(self._target_to_drop):
            placeholder = self._target_to_drop
        else:
            event.ignore()
            return
        data: SceneStructureItemType = pickle.loads(event.mimeData().data(self.MimeType))

        if data == SceneStructureItemType.GOAL:
            widget = SceneGoalItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.GOAL))
        elif data == SceneStructureItemType.CONFLICT:
            widget = SceneConflictItemWidget(self.novel, SceneStructureItem(SceneStructureItemType.CONFLICT))
        else:
            widget = AutoAdjustableTextEdit()

        self._addPlaceholder(placeholder.parent())
        layout: QHBoxLayout = placeholder.parent().layout()
        index = layout.indexOf(placeholder)
        layout.takeAt(index)
        placeholder.deleteLater()
        layout.insertWidget(index, widget)

        event.accept()

    def _addPlaceholder(self, widget: QWidget):
        _placeholder = _PlaceHolder()
        widget.layout().addWidget(_placeholder)
        _placeholder.setAcceptDrops(True)
        _placeholder.installEventFilter(self)

    def _type_changed(self):
        if self.rbScene.isChecked():
            self.scene.type = SceneType.ACTION
        elif self.rbSequel.isChecked():
            self.scene.type = SceneType.REACTION
        else:
            self.scene.type = SceneType.MIXED

    def _dragDestroyed(self):
        self._dragged = None
