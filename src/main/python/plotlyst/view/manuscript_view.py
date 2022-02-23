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

from typing import Optional

from PyQt5.QtCore import QModelIndex, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QHeaderView, QApplication
from overrides import overrides
from qthandy import opaque, incr_font, bold, btn_popup

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Document, DocumentStatistics, Scene
from src.main.python.plotlyst.event.core import emit_event, emit_critical, emit_info
from src.main.python.plotlyst.events import NovelUpdatedEvent, SceneChangedEvent, OpenDistractionFreeMode, \
    ChapterChangedEvent
from src.main.python.plotlyst.model.chapters_model import ChaptersTreeModel, SceneNode, ChapterNode
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import OpacityEventFilter
from src.main.python.plotlyst.view.generated.manuscript_view_ui import Ui_ManuscriptView
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.widget.manuscript import ManuscriptContextMenuWidget, ManuscriptTextEditor
from src.main.python.plotlyst.worker.grammar import language_tool_proxy
from src.main.python.plotlyst.worker.persistence import flush_or_fail


class ManuscriptView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel, [NovelUpdatedEvent, SceneChangedEvent, ChapterChangedEvent])
        self.ui = Ui_ManuscriptView()
        self.ui.setupUi(self.widget)
        self._current_scene: Optional[Scene] = None
        self._current_doc: Optional[Document] = None
        self.ui.splitter.setSizes([100, 500])
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageEmpty)

        self.ui.textEdit.setTitleVisible(False)
        self.ui.textEdit.setToolbarVisible(False)

        self.ui.lblTitle.setText(self.novel.title)
        self.ui.btnStoryGoal.setText('80,000')

        bold(self.ui.lblSceneTitle)
        incr_font(self.ui.lblSceneTitle)

        self.ui.btnDistractionFree.setIcon(IconRegistry.from_name('fa5s.expand-alt'))
        self.ui.btnSpellCheckIcon.setIcon(IconRegistry.from_name('fa5s.spell-check'))
        self.ui.btnAnalysisIcon.setIcon(IconRegistry.from_name('fa5s.glasses'))
        self.ui.btnContext.setIcon(IconRegistry.context_icon())
        self.ui.btnContext.installEventFilter(OpacityEventFilter(leaveOpacity=0.7, parent=self.ui.btnContext))
        self._contextMenuWidget = ManuscriptContextMenuWidget(novel, self.widget)
        btn_popup(self.ui.btnContext, self._contextMenuWidget)
        self._contextMenuWidget.languageChanged.connect(self._language_changed)
        self.ui.cbSpellCheck.toggled.connect(self._spellcheck_toggled)
        self.ui.cbSpellCheck.clicked.connect(self._spellcheck_clicked)
        self.ui.btnAnalysis.toggled.connect(self._analysis_toggled)
        self.ui.btnAnalysis.clicked.connect(self._analysis_clicked)
        self._spellcheck_toggled(self.ui.btnSpellCheckIcon.isChecked())
        self._analysis_toggled(self.ui.btnAnalysis.isChecked())

        self.chaptersModel = ChaptersTreeModel(self.novel)
        self.ui.treeChapters.setModel(self.chaptersModel)
        self.ui.treeChapters.expandAll()
        self.chaptersModel.modelReset.connect(self.ui.treeChapters.expandAll)
        self.ui.treeChapters.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.treeChapters.setColumnWidth(ChaptersTreeModel.ColPlus, 24)
        self.ui.treeChapters.clicked.connect(self._edit)

        self.ui.wdgTopAnalysis.setHidden(True)
        self.ui.wdgSideAnalysis.setHidden(True)

        self.ui.textEdit.textEdit.textChanged.connect(self._save)
        self.ui.btnDistractionFree.clicked.connect(
            lambda: emit_event(OpenDistractionFreeMode(self, self.ui.textEdit, self.ui.wdgSprint.model())))

        self._update_story_goal()

    @overrides
    def refresh(self):
        self.chaptersModel.update()
        self.chaptersModel.modelReset.emit()

    def restore_editor(self, editor: ManuscriptTextEditor):
        self.ui.wdgEditor.layout().insertWidget(0, editor)

    def _update_story_goal(self):
        wc = sum([x.manuscript.statistics.wc for x in self.novel.scenes if x.manuscript and x.manuscript.statistics])
        self.ui.btnStoryGoal.setText(f'{wc} word{"s" if wc > 1 else ""}')
        self.ui.progressStory.setValue(int(wc / 80000 * 100))

    def _edit(self, index: QModelIndex):
        def text_changed():
            wc = self.ui.textEdit.statistics().word_count
            self.ui.lblWordCount.setWordCount(wc)
            if self._current_doc.statistics is None:
                self._current_doc.statistics = DocumentStatistics()

            if self._current_doc.statistics.wc != wc:
                self._current_doc.statistics.wc = wc
                self.repo.update_scene(self._current_scene)
                self._update_story_goal()
            self.ui.wdgReadability.setTextDocumentUpdated(self.ui.textEdit.textEdit.document())

        node = index.data(ChaptersTreeModel.NodeRole)
        if isinstance(node, SceneNode):
            if not node.scene.manuscript:
                node.scene.manuscript = Document('', scene_id=node.scene.id)
                self.repo.update_scene(node.scene)
            self._current_scene = node.scene
            self._current_doc = node.scene.manuscript

            if not self._current_doc.loaded:
                json_client.load_document(self.novel, self._current_doc)

            self.ui.stackedWidget.setCurrentWidget(self.ui.pageText)
            self.ui.textEdit.setGrammarCheckEnabled(False)
            self.ui.textEdit.setText(self._current_doc.content, self._current_doc.title)

            self.ui.textEdit.setMargins(30, 30, 30, 30)
            self.ui.textEdit.textEdit.setFormat(130, textIndent=20)
            self.ui.textEdit.textEdit.setFontPointSize(16)
            text_changed()
            self.ui.textEdit.textEdit.textChanged.connect(text_changed)

            if self.ui.cbSpellCheck.isChecked():
                self.ui.textEdit.setGrammarCheckEnabled(True)
                self.ui.textEdit.asyncCheckGrammer()

            self.ui.lblSceneTitle.setText(node.scene.title_or_index(self.novel))
            if node.scene.pov:
                self.ui.btnPov.setIcon(QIcon(avatars.pixmap(node.scene.pov)))
                self.ui.btnPov.setVisible(True)
            else:
                self.ui.btnPov.setHidden(True)
            scene_type_icon = IconRegistry.scene_type_icon(node.scene)
            if scene_type_icon:
                self.ui.btnSceneType.setIcon(scene_type_icon)
                self.ui.btnSceneType.setVisible(True)
            else:
                self.ui.btnSceneType.setHidden(True)

            if self.ui.btnAnalysis.isChecked():
                self.ui.wdgReadability.checkTextDocument(self.ui.textEdit.textEdit.document())

        elif isinstance(node, ChapterNode):
            self._current_scene = None
            self._current_doc = None
            self.ui.stackedWidget.setCurrentWidget(self.ui.pageEmpty)

    def _save(self):
        if not self._current_doc:
            return
        self._current_doc.content = self.ui.textEdit.textEdit.toHtml()
        self.repo.update_doc(self.novel, self._current_doc)

    def _spellcheck_toggled(self, toggled: bool):
        opaque(self.ui.btnSpellCheckIcon, 1 if toggled else 0.4)

    def _spellcheck_clicked(self, checked: bool):
        if checked:
            if language_tool_proxy.is_failed():
                self.ui.cbSpellCheck.setChecked(False)
                emit_critical(language_tool_proxy.error)
            else:
                self.ui.textEdit.setGrammarCheckEnabled(True)
                self.ui.textEdit.asyncCheckGrammer()
        else:
            self.ui.textEdit.setGrammarCheckEnabled(False)
            self.ui.textEdit.checkGrammar()

    def _analysis_toggled(self, toggled: bool):
        opaque(self.ui.btnAnalysisIcon, 1 if toggled else 0.4)

    def _analysis_clicked(self, checked: bool):
        if not checked:
            return

        self.ui.wdgReadability.checkTextDocument(self.ui.textEdit.textEdit.document())

    def _language_changed(self, lang: str):
        emit_info('Application is shutting down. Persist workspace...')
        self.novel.lang_settings.lang = lang
        self.repo.update_project_novel(self.novel)
        flush_or_fail()
        QTimer.singleShot(1000, QApplication.exit)
