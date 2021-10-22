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
from PyQt5.QtWidgets import QSizePolicy, QWidget, QListView, QFrame, QToolButton
from overrides import overrides

from src.main.python.plotlyst.core.domain import Scene, SelectionItem, Novel, SceneGoal
from src.main.python.plotlyst.model.common import SelectionItemsModel
from src.main.python.plotlyst.model.novel import NovelPlotsModel, NovelTagsModel
from src.main.python.plotlyst.model.scenes_model import SceneGoalsModel
from src.main.python.plotlyst.view.generated.scene_filter_widget_ui import Ui_SceneFilterWidget
from src.main.python.plotlyst.view.generated.scene_structure_editor_widget_ui import Ui_SceneStructureWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.input import AutoAdjustableTextEdit
from src.main.python.plotlyst.view.widget.labels import LabelsEditorWidget, GoalLabel


class SceneGoalsWidget(LabelsEditorWidget):

    def __init__(self, novel: Novel, scene: Scene, parent=None):
        self.novel = novel
        self.scene = scene
        super(SceneGoalsWidget, self).__init__(alignment=Qt.Horizontal, parent=parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.setValue([x.text for x in self.scene.goals])
        self.btnEdit.setIcon(IconRegistry.goal_icon())
        self.setStyleSheet('SceneGoalsWidget {border: 0px;}')

    @overrides
    def _initModel(self) -> SelectionItemsModel:
        return SceneGoalsModel(self.novel, self.scene)

    @overrides
    def items(self) -> List[SelectionItem]:
        return self.novel.scene_goals

    @overrides
    def _addItems(self, items: Set[SceneGoal]):
        for item in items:
            self._wdgLabels.addLabel(GoalLabel(item))
        self.scene.goals.clear()
        self.scene.goals.extend(items)


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


class SceneStructureWidget(QWidget, Ui_SceneStructureWidget):
    MimeType: str = 'application/structure-item'

    def __init__(self, parent=None):
        super(SceneStructureWidget, self).__init__(parent)
        self.setupUi(self)
        self._dragged: Optional[QToolButton] = None
        self._target_to_drop: Optional[QWidget] = None

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
            mimedata.setData(self.MimeType, QByteArray(pickle.dumps(self._dragged.objectName())))
            drag.setMimeData(mimedata)
            drag.setPixmap(pix)
            drag.setHotSpot(event.pos())
            drag.destroyed.connect(self._dragDestroyed)
            drag.exec_()

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
        data = pickle.loads(event.mimeData().data(self.MimeType))
        text_edit = AutoAdjustableTextEdit()
        text_edit.setPlaceholderText(data)
        self._addPlaceholder(placeholder.parent())
        placeholder.parent().layout().replaceWidget(placeholder, text_edit)
        # widget_to_drop = TemplateFieldWidget(field)
        # widget_to_drop.setEnabled(False)
        # pos = self.gridLayout.getItemPosition(index)
        # item: QLayoutItem = self.gridLayout.takeAt(index)
        # item.widget().deleteLater()
        # self.gridLayout.addWidget(widget_to_drop, *pos)
        # self._installEventFilter(widget_to_drop)
        #
        # self.widgets.append(widget_to_drop)
        #
        # self.fieldAdded.emit(field)
        # self._select(widget_to_drop)
        #
        # if pos[0] == self.gridLayout.rowCount() - 1:
        #     self._addPlaceholder(pos[0] + 1, 0)
        #     self._addPlaceholder(pos[0] + 1, 1)
        #     self.gridLayout.update()

        event.accept()

    def _addPlaceholder(self, widget: QWidget):
        _placeholder = _PlaceHolder()
        widget.layout().addWidget(_placeholder)
        _placeholder.setAcceptDrops(True)
        _placeholder.installEventFilter(self)

    def _dragDestroyed(self):
        self._dragged = None
