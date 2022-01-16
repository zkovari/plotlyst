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
from typing import List, Optional

from PyQt5.QtWidgets import QHBoxLayout, QWidget, QHeaderView
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel, SelectionItem, Plot
from src.main.python.plotlyst.events import NovelUpdatedEvent, \
    SceneChangedEvent
from src.main.python.plotlyst.model.common import SelectionItemsModel
from src.main.python.plotlyst.model.novel import NovelPlotsModel, NovelTagsModel, NovelConflictsModel
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import ask_confirmation, link_buttons_to_pages, OpacityEventFilter
from src.main.python.plotlyst.view.delegates import TextItemDelegate
from src.main.python.plotlyst.view.dialog.novel import PlotEditorDialog, PlotEditionResult
from src.main.python.plotlyst.view.generated.novel_view_ui import Ui_NovelView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.items_editor import ItemsEditorWidget
from src.main.python.plotlyst.view.widget.labels import LabelsEditorWidget


class NovelView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel, [NovelUpdatedEvent, SceneChangedEvent])
        self.ui = Ui_NovelView()
        self.ui.setupUi(self.widget)

        self.ui.lblTitle.setText(self.novel.title)

        self.ui.btnGoalIcon.setIcon(IconRegistry.goal_icon())
        self.ui.btnConflictIcon.setIcon(IconRegistry.conflict_icon())

        self.ui.wdgStructure.setNovel(self.novel)
        self.ui.wdgTitle.setFixedHeight(150)
        self.ui.wdgTitle.setStyleSheet(
            f'#wdgTitle {{border-image: url({resource_registry.frame1}) 0 0 0 0 stretch stretch;}}')

        self.story_lines_model = NovelPlotsModel(self.novel)
        self.ui.wdgDramaticQuestions.tableView.horizontalHeader().setStretchLastSection(False)
        self.ui.wdgDramaticQuestions.setModel(self.story_lines_model)
        self.ui.wdgDramaticQuestions.setInlineEditionEnabled(False)
        self.ui.wdgDramaticQuestions.editRequested.connect(self._edit_plot)

        self.ui.wdgDramaticQuestions.tableView.horizontalHeader().show()
        self.ui.wdgDramaticQuestions.tableView.setColumnWidth(NovelPlotsModel.ColName, 250)
        self.ui.wdgDramaticQuestions.tableView.setColumnWidth(NovelPlotsModel.ColPlotType, 100)
        self.ui.wdgDramaticQuestions.tableView.setColumnWidth(NovelPlotsModel.ColCharacter, 155)
        self.ui.wdgDramaticQuestions.tableView.setColumnWidth(NovelPlotsModel.ColValueType, 60)
        self.ui.wdgDramaticQuestions.setAskRemovalConfirmation(True)
        self.ui.wdgDramaticQuestions.setBgColorFieldEnabled(True)

        self.ui.btnEdit.setIcon(IconRegistry.edit_icon())
        self.ui.btnRemove.setIcon(IconRegistry.minus_icon())

        self.conflict_model = NovelConflictsModel(self.novel)
        self.ui.tblConflicts.setModel(self.conflict_model)
        self.ui.tblConflicts.horizontalHeader().setSectionResizeMode(NovelConflictsModel.ColPov,
                                                                     QHeaderView.ResizeToContents)
        self.ui.tblConflicts.horizontalHeader().setSectionResizeMode(NovelConflictsModel.ColType,
                                                                     QHeaderView.ResizeToContents)
        self.ui.tblConflicts.horizontalHeader().setSectionResizeMode(NovelConflictsModel.ColPhrase,
                                                                     QHeaderView.Stretch)
        self.ui.tblConflicts.selectionModel().selectionChanged.connect(self._conflict_selected)
        self.ui.tblConflicts.setItemDelegateForColumn(NovelConflictsModel.ColPhrase, TextItemDelegate())
        self.ui.btnEdit.clicked.connect(self._edit_conflict)
        self.ui.btnRemove.clicked.connect(self._delete_conflict)

        tags_editor = NovelTagsEditor(self.novel)
        _layout = QHBoxLayout()
        _layout.setSpacing(0)
        _layout.setContentsMargins(0, 0, 0, 0)
        self.ui.wdgTagsContainer.setLayout(_layout)
        self.ui.wdgTagsContainer.layout().addWidget(tags_editor)

        self.ui.btnStructure.setIcon(IconRegistry.from_name('fa5s.theater-masks', 'white'))
        self.ui.btnPlot.setIcon(IconRegistry.from_name('mdi.chart-bell-curve-cumulative', 'white'))
        self.ui.btnSynopsis.setIcon(IconRegistry.from_name('fa5s.scroll', 'white'))
        self.ui.btnGoals.setIcon(IconRegistry.goal_icon('white'))
        self.ui.btnTags.setIcon(IconRegistry.tags_icon('white'))

        link_buttons_to_pages(self.ui.stackedWidget, [(self.ui.btnStructure, self.ui.pageStructure),
                                                      (self.ui.btnPlot, self.ui.pagePlot),
                                                      (self.ui.btnGoals, self.ui.pageGoals),
                                                      (self.ui.btnSynopsis, self.ui.pageSynopsis),
                                                      (self.ui.btnTags, self.ui.pageTags)])
        self.ui.btnStructure.setChecked(True)

        for btn in self.ui.buttonGroup.buttons():
            btn.setStyleSheet('''
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #89c2d9);
                border: 2px solid #2c7da0;
                border-radius: 6px;
                color: white;
                padding: 2px;
                font: bold;
            }
            QPushButton:checked {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #014f86);
                border: 2px solid #013a63;
            }
            ''')
            btn.installEventFilter(OpacityEventFilter(leaveOpacity=0.7, parent=btn, ignoreCheckedButton=True))

    @overrides
    def refresh(self):
        self.ui.lblTitle.setText(self.novel.title)
        self.story_lines_model.modelReset.emit()
        self.conflict_model.modelReset.emit()
        self._conflict_selected()

    def _edit_plot(self, plot: Plot):
        edited_plot: Optional[PlotEditionResult] = PlotEditorDialog(self.novel, plot).display()
        if edited_plot is None:
            return

        plot.text = edited_plot.text
        plot.plot_type = edited_plot.plot_type
        plot.set_character(edited_plot.character)

        self.story_lines_model.modelReset.emit()
        self.repo.update_novel(self.novel)

    def _conflict_selected(self):
        selection = bool(self.ui.tblConflicts.selectedIndexes())
        self.ui.btnEdit.setEnabled(selection)
        self.ui.btnRemove.setEnabled(selection)

    def _edit_conflict(self):
        indexes = self.ui.tblConflicts.selectedIndexes()
        if not indexes:
            return
        self.ui.tblConflicts.edit(self.conflict_model.index(indexes[0].row(), NovelConflictsModel.ColPhrase))

    def _delete_conflict(self):
        indexes = self.ui.tblConflicts.selectedIndexes()
        if not indexes:
            return

        conflict = indexes[0].data(NovelConflictsModel.ConflictRole)
        if ask_confirmation(f'Delete conflict "{conflict.text}"'):
            for scene in self.novel.scenes:
                if conflict in scene.conflicts:
                    scene.conflicts.remove(conflict)
                    self.repo.update_scene(scene)
            self.novel.conflicts.remove(conflict)
            self.repo.update_novel(self.novel)


class NovelTagsEditor(LabelsEditorWidget):

    def __init__(self, novel: Novel, parent=None):
        self.novel = novel
        super(NovelTagsEditor, self).__init__(checkable=False, parent=parent)
        self.btnEdit.setIcon(IconRegistry.tag_plus_icon())
        self.editor.model.item_edited.connect(self._updateTags)
        self._updateTags()

    @overrides
    def _initPopupWidget(self) -> QWidget:
        self.editor: ItemsEditorWidget = super(NovelTagsEditor, self)._initPopupWidget()
        self.editor.setBgColorFieldEnabled(True)
        return self.editor

    @overrides
    def _initModel(self) -> SelectionItemsModel:
        return NovelTagsModel(self.novel)

    @overrides
    def items(self) -> List[SelectionItem]:
        return self.novel.tags

    def _updateTags(self):
        self._wdgLabels.clear()
        self._addItems(self.novel.tags)
