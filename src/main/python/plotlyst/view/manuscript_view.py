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
import qtanim
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QInputDialog
from overrides import overrides
from qthandy import translucent, bold, margins, spacer, vline, transparent, vspacer, decr_icon
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget
from qttextedit.ops import TextEditorSettingsWidget, TextEditorSettingsSection

from src.main.python.plotlyst.common import PLOTLYST_MAIN_COLOR, RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Novel, Document, Chapter
from src.main.python.plotlyst.core.domain import Scene
from src.main.python.plotlyst.event.core import emit_global_event, emit_critical, emit_info, Event, emit_event
from src.main.python.plotlyst.events import NovelUpdatedEvent, SceneChangedEvent, OpenDistractionFreeMode, \
    ChapterChangedEvent, SceneDeletedEvent, ExitDistractionFreeMode, NovelSyncEvent, CloseNovelEvent
from src.main.python.plotlyst.resources import ResourceType
from src.main.python.plotlyst.service.grammar import language_tool_proxy
from src.main.python.plotlyst.service.persistence import flush_or_fail
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import tool_btn, ButtonPressResizeEventFilter, action, \
    ExclusiveOptionalButtonGroup, link_buttons_to_pages, icon_to_html_img
from src.main.python.plotlyst.view.generated.manuscript_view_ui import Ui_ManuscriptView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.style.base import apply_white_menu
from src.main.python.plotlyst.view.widget.display import Icon, ChartView
from src.main.python.plotlyst.view.widget.input import Toggle
from src.main.python.plotlyst.view.widget.manuscript import ManuscriptContextMenuWidget, \
    DistractionFreeManuscriptEditor, SprintWidget, ReadabilityWidget
from src.main.python.plotlyst.view.widget.progress import ProgressChart
from src.main.python.plotlyst.view.widget.scene.editor import SceneMiniEditor
from src.main.python.plotlyst.view.widget.scenes import SceneNotesEditor
from src.main.python.plotlyst.view.widget.tree import TreeSettings
from src.main.python.plotlyst.view.widget.utility import ask_for_resource


class ManuscriptView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel, [NovelUpdatedEvent, SceneChangedEvent, ChapterChangedEvent, SceneDeletedEvent])
        self.ui = Ui_ManuscriptView()
        self.ui.setupUi(self.widget)
        self.ui.splitter.setSizes([150, 500])
        self.ui.splitterEditor.setSizes([400, 150])
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageOverview)

        self.ui.lblWc.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.ui.btnAdd.setIcon(IconRegistry.plus_icon('white'))

        bold(self.ui.lblTitle)
        self.ui.btnManuscript.setIcon(IconRegistry.manuscript_icon())

        self.ui.btnSceneInfo.setIcon(IconRegistry.scene_icon())
        self.ui.btnGoals.setIcon(IconRegistry.goal_icon('black', PLOTLYST_MAIN_COLOR))
        self.ui.btnReadability.setIcon(IconRegistry.from_name('fa5s.glasses', 'black', PLOTLYST_MAIN_COLOR))
        self.ui.btnLengthCharts.setIcon(IconRegistry.from_name('ri.bar-chart-2-fill', 'black', PLOTLYST_MAIN_COLOR))
        self.ui.btnLengthCharts.setHidden(True)
        self.ui.btnExport.setIcon(IconRegistry.from_name('ei.download-alt', 'black', PLOTLYST_MAIN_COLOR))

        self._btnGroupSideBar = ExclusiveOptionalButtonGroup()
        self._btnGroupSideBar.addButton(self.ui.btnSceneInfo)
        self._btnGroupSideBar.addButton(self.ui.btnGoals)
        self._btnGroupSideBar.addButton(self.ui.btnReadability)
        self._btnGroupSideBar.addButton(self.ui.btnLengthCharts)
        self._btnGroupSideBar.addButton(self.ui.btnExport)
        for btn in self._btnGroupSideBar.buttons():
            btn.installEventFilter(OpacityEventFilter(btn, leaveOpacity=0.5, ignoreCheckedButton=True))
            btn.installEventFilter(ButtonPressResizeEventFilter(btn))

        self._btnGroupSideBar.buttonToggled.connect(self._side_bar_toggled)
        link_buttons_to_pages(self.ui.stackSide,
                              [(self.ui.btnSceneInfo, self.ui.pageInfo), (self.ui.btnGoals, self.ui.pageGoal),
                               (self.ui.btnExport, self.ui.pageExport),
                               (self.ui.btnLengthCharts, self.ui.pageCharts),
                               (self.ui.btnReadability, self.ui.pageReadability)])

        bold(self.ui.lblWordCount)

        self._miniSceneEditor = SceneMiniEditor(self.novel)
        self.ui.pageInfo.layout().addWidget(self._miniSceneEditor)
        self.ui.pageInfo.layout().addWidget(vspacer())
        self.ui.textEdit.manuscriptTextEdit().sceneSeparatorClicked.connect(self._scene_separator_clicked)

        self._btnDistractionFree = tool_btn(IconRegistry.expand_icon(), 'Enter distraction-free mode', base=True)
        transparent(self._btnDistractionFree)
        decr_icon(self._btnDistractionFree)
        self._wdgSprint = SprintWidget()
        transparent(self._wdgSprint.btnTimer)
        decr_icon(self._wdgSprint.btnTimer)
        self._spellCheckIcon = Icon()
        self._spellCheckIcon.setIcon(IconRegistry.from_name('fa5s.spell-check'))
        self._spellCheckIcon.setToolTip('Spellcheck')
        self._cbSpellCheck = Toggle()
        self._cbSpellCheck.setToolTip('Toggle spellcheck')
        self._btnContext = tool_btn(IconRegistry.context_icon(), 'Manuscript settings')
        transparent(self._btnContext)

        self.ui.btnEditGoal.setIcon(IconRegistry.edit_icon())
        transparent(self.ui.btnEditGoal)
        decr_icon(self.ui.btnEditGoal, 2)
        self.ui.btnEditGoal.installEventFilter(OpacityEventFilter(self.ui.btnEditGoal))
        self.ui.btnEditGoal.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnEditGoal))
        self.ui.btnEditGoal.clicked.connect(self._edit_wc_goal)

        self._chartProgress = ProgressChart(maxValue=self.novel.manuscript_goals.target_wc,
                                            title_prefix=icon_to_html_img(IconRegistry.goal_icon(PLOTLYST_MAIN_COLOR)),
                                            color=PLOTLYST_MAIN_COLOR,
                                            titleColor=PLOTLYST_MAIN_COLOR,
                                            emptySliceColor=RELAXED_WHITE_COLOR)
        self._chartProgress.setBackgroundBrush(QColor(RELAXED_WHITE_COLOR))
        self._chartProgressView = ChartView()
        self._chartProgressView.setFixedSize(200, 200)
        self._chartProgressView.setChart(self._chartProgress)
        self.ui.pageGoal.layout().addWidget(self._chartProgressView, alignment=Qt.AlignmentFlag.AlignTop)
        self.ui.pageGoal.layout().addWidget(vspacer())

        self._wdgReadability = ReadabilityWidget()
        self.ui.pageReadability.layout().addWidget(self._wdgReadability, alignment=Qt.AlignmentFlag.AlignCenter)
        self.ui.pageReadability.layout().addWidget(vspacer())

        self._wdgToolbar = group(self._btnDistractionFree, self._wdgSprint, spacer(), self._spellCheckIcon,
                                 self._cbSpellCheck,
                                 vline(), self._btnContext)
        self.ui.wdgTop.layout().addWidget(self._wdgToolbar)
        margins(self._wdgToolbar, right=21)

        self._addSceneMenu = MenuWidget(self.ui.btnAdd)
        self._addSceneMenu.addAction(action('Add scene', IconRegistry.scene_icon(), self.ui.treeChapters.addScene))
        self._addSceneMenu.addAction(
            action('Add chapter', IconRegistry.chapter_icon(), self.ui.treeChapters.addChapter))

        self._langSelectionWidget = ManuscriptContextMenuWidget(novel, self.widget)
        self._contextMenuWidget = TextEditorSettingsWidget()
        self._contextMenuWidget.addTab(self._langSelectionWidget, IconRegistry.from_name('fa5s.spell-check'), '')
        menu = MenuWidget(self._btnContext)
        apply_white_menu(menu)
        menu.addWidget(self._contextMenuWidget)
        self._contextMenuWidget.setSectionVisible(TextEditorSettingsSection.WIDTH, False)
        self.ui.textEdit.attachSettingsWidget(self._contextMenuWidget)

        self._langSelectionWidget.languageChanged.connect(self._language_changed)
        self._cbSpellCheck.toggled.connect(self._spellcheck_toggled)
        self._cbSpellCheck.clicked.connect(self._spellcheck_clicked)
        self._wdgReadability.cbAdverbs.toggled.connect(self._adverb_highlight_toggled)
        self._spellcheck_toggled(self._cbSpellCheck.isChecked())

        self._dist_free_editor = DistractionFreeManuscriptEditor(self.ui.pageDistractionFree)
        self._dist_free_editor.exitRequested.connect(self._exit_distraction_free)
        self.ui.pageDistractionFree.layout().addWidget(self._dist_free_editor)

        self.ui.treeChapters.setSettings(TreeSettings(font_incr=2))
        self.ui.treeChapters.setNovel(self.novel, readOnly=self.novel.is_readonly())
        self.ui.treeChapters.sceneSelected.connect(self._editScene)
        self.ui.treeChapters.chapterSelected.connect(self._editChapter)
        self.ui.treeChapters.sceneAdded.connect(self._scene_added)
        self.ui.treeChapters.centralWidget().setProperty('bg', True)

        self.ui.wdgSide.setHidden(True)
        self.ui.wdgAddon.setHidden(True)

        self.notesEditor = SceneNotesEditor()
        self.ui.wdgAddon.layout().addWidget(self.notesEditor)

        self.ui.btnNotes.setIcon(IconRegistry.document_edition_icon())
        self.ui.btnNotes.setDisabled(True)
        self.ui.btnNotes.setHidden(True)
        # self.ui.btnNotes.toggled.connect(self.ui.wdgAddon.setVisible)

        self.ui.textEdit.setMargins(30, 30, 30, 30)
        self.ui.textEdit.textEdit.setPlaceholderText('Write your story...')
        self.ui.textEdit.textEdit.setSidebarEnabled(False)
        self.ui.textEdit.textEdit.setReadOnly(self.novel.is_readonly())
        self.ui.textEdit.textChanged.connect(self._text_changed)
        self.ui.textEdit.selectionChanged.connect(self._text_selection_changed)
        self.ui.textEdit.sceneTitleChanged.connect(self._scene_title_changed)
        self._btnDistractionFree.clicked.connect(self._enter_distraction_free)

        if self.novel.chapters:
            self.ui.treeChapters.selectChapter(self.novel.chapters[0])
            self._editChapter(self.novel.chapters[0])
        elif self.novel.scenes:
            self.ui.treeChapters.selectScene(self.novel.scenes[0])
            self._editScene(self.novel.scenes[0])

        self._update_story_goal()

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, NovelSyncEvent):
            self.ui.textEdit.refresh()
            self._text_changed()
        elif isinstance(event, SceneDeletedEvent):
            if event.scene in self.ui.textEdit.scenes():
                if len(self.ui.textEdit.scenes()) == 1:
                    self.ui.textEdit.clear()
                    self._empty_page()
                else:
                    self._editChapter(event.scene.chapter)
        super(ManuscriptView, self).event_received(event)

    @overrides
    def refresh(self):
        self.ui.treeChapters.refresh()

    def _enter_distraction_free(self):
        emit_global_event(OpenDistractionFreeMode(self))
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageDistractionFree)
        margins(self.widget, 0, 0, 0, 0)
        self.ui.wdgTitle.setHidden(True)
        self.ui.wdgLeftSide.setHidden(True)
        self._dist_free_editor.activate(self.ui.textEdit, self._wdgSprint.model())
        self._dist_free_editor.setWordDisplay(self.ui.lblWordCount)

    def _exit_distraction_free(self):
        emit_global_event(ExitDistractionFreeMode(self))
        self._dist_free_editor.deactivate()
        margins(self.widget, 4, 2, 2, 2)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageText)
        self.ui.wdgTitle.setVisible(True)
        self.ui.wdgLeftSide.setVisible(True)

        self.ui.wdgBottom.layout().insertWidget(1, self.ui.lblWordCount, alignment=Qt.AlignmentFlag.AlignCenter)
        self.ui.lblWordCount.setVisible(True)
        self.ui.splitterEditor.insertWidget(0, self.ui.textEdit)
        self._wdgReadability.cbAdverbs.setChecked(False)

    def _update_story_goal(self):
        wc = sum([x.manuscript.statistics.wc for x in self.novel.scenes if x.manuscript and x.manuscript.statistics])
        self.ui.lblWc.setText(f'{wc} word{"s" if wc > 1 else ""}')
        # self.ui.progressStory.setValue(int(wc / 80000 * 100))
        self._chartProgress.setValue(wc)
        self._chartProgress.refresh()

    def _editScene(self, scene: Scene):
        self.ui.textEdit.setGrammarCheckEnabled(False)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageText)

        if not scene.manuscript:
            scene.manuscript = Document('', scene_id=scene.id)
            self.repo.update_scene(scene)

        self.ui.textEdit.setScene(scene)
        self._miniSceneEditor.setScene(scene)

        # if scene.title:
        #     self.ui.lineSceneTitle.setText(scene.title)
        #     self.ui.lineSceneTitle.setPlaceholderText('Scene title')
        # else:
        #     self.ui.lineSceneTitle.clear()
        #     self.ui.lineSceneTitle.setPlaceholderText(scene.title_or_index(self.novel))

        # if scene.pov:
        #     self.ui.btnPov.setIcon(avatars.avatar(scene.pov))
        #     self.ui.btnPov.setVisible(True)
        # else:
        #     self.ui.btnPov.setHidden(True)
        # scene_type_icon = IconRegistry.scene_type_icon(scene)
        # if scene_type_icon:
        #     self.ui.btnSceneType.setIcon(scene_type_icon)
        #     self.ui.btnSceneType.setVisible(True)
        # else:
        #     self.ui.btnSceneType.setHidden(True)

        self.notesEditor.setScene(scene)
        self.ui.btnNotes.setEnabled(True)
        self.ui.btnStage.setEnabled(True)
        self.ui.btnStage.setScene(scene, self.novel)

        self._recheckDocument()

        self.ui.textEdit.setFocus()

    def _editChapter(self, chapter: Chapter):
        self.ui.textEdit.setGrammarCheckEnabled(False)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageText)

        scenes = self.novel.scenes_in_chapter(chapter)
        for scene in scenes:
            if not scene.manuscript:
                scene.manuscript = Document('', scene_id=scene.id)
                self.repo.update_scene(scene)
        if scenes:
            self.ui.textEdit.setChapterScenes(scenes, chapter.title_index(self.novel))
            self._miniSceneEditor.setScenes(scenes)
        else:
            self.ui.stackedWidget.setCurrentWidget(self.ui.pageEmpty)
            self._miniSceneEditor.reset()

        self.ui.btnNotes.setChecked(False)
        self.ui.btnNotes.setDisabled(True)
        self.ui.btnStage.setDisabled(True)

        self._recheckDocument()
        self.ui.textEdit.setFocus()

    def _scene_added(self, scene: Scene):
        if self._is_empty_page():
            self._editScene(scene)
            self.ui.treeChapters.selectScene(scene)

    def _recheckDocument(self):
        if self.ui.stackedWidget.currentWidget() == self.ui.pageText:
            self._text_changed()

            if self._cbSpellCheck.isChecked():
                self.ui.textEdit.setGrammarCheckEnabled(True)
                self.ui.textEdit.asyncCheckGrammer()
            if self.ui.btnReadability.isChecked():
                self._wdgReadability.checkTextDocument(self.ui.textEdit.document())

    def _text_changed(self):
        wc = self.ui.textEdit.statistics().word_count
        self.ui.lblWordCount.setWordCount(wc)
        self._update_story_goal()
        self._wdgReadability.setTextDocumentUpdated(self.ui.textEdit.document())

    def _text_selection_changed(self):
        if self.ui.textEdit.textEdit.textCursor().hasSelection():
            fragment = self.ui.textEdit.textEdit.textCursor().selection()
            self.ui.lblWordCount.calculateSecondaryWordCount(fragment.toPlainText())
        else:
            self.ui.lblWordCount.clearSecondaryWordCount()

    def _scene_title_changed(self, scene: Scene):
        self.repo.update_scene(scene)
        emit_event(self.novel, SceneChangedEvent(self, scene))

    def _edit_wc_goal(self):
        goal, changed = QInputDialog.getInt(self.ui.btnEditGoal, 'Word count goal', 'Edit word count target',
                                            value=self.novel.manuscript_goals.target_wc,
                                            min=1000, max=10000000, step=1000)
        if changed:
            self.novel.manuscript_goals.target_wc = goal
            self.repo.update_novel(self.novel)
            self._refresh_target_wc()

    def _refresh_target_wc(self):
        self.ui.lblGoal.setText(f'<html><b>{self.novel.manuscript_goals.target_wc}</b> words')
        self._chartProgress.setMaxValue(self.novel.manuscript_goals.target_wc)
        self._chartProgress.refresh()

    def _side_bar_toggled(self, _, toggled: bool):
        btn = self._btnGroupSideBar.checkedButton()
        if btn is None:
            qtanim.collapse(self.ui.wdgSide)
            return

        if toggled:
            qtanim.expand(self.ui.wdgSide)

        if btn is self.ui.btnReadability:
            self._analysis_clicked(self.ui.btnReadability.isChecked())
        elif btn is self.ui.btnGoals:
            self._refresh_target_wc()

    def _spellcheck_toggled(self, toggled: bool):
        translucent(self._spellCheckIcon, 1 if toggled else 0.4)

    def _spellcheck_clicked(self, checked: bool):
        if checked:
            if language_tool_proxy.is_failed():
                self._cbSpellCheck.setChecked(False)
                emit_critical(language_tool_proxy.error)
            else:
                # self._wdgReadability.cbAdverbs.setChecked(False)
                self.ui.textEdit.setGrammarCheckEnabled(True)
                QTimer.singleShot(50, self.ui.textEdit.asyncCheckGrammer)
        else:
            self.ui.textEdit.setGrammarCheckEnabled(False)
            self.ui.textEdit.checkGrammar()

    def _analysis_clicked(self, checked: bool):
        if not checked:
            return

        if not ask_for_resource(ResourceType.NLTK_PUNKT_TOKENIZER):
            self.ui.btnReadability.setChecked(False)
            return

        self._wdgReadability.checkTextDocument(self.ui.textEdit.document())

    def _adverb_highlight_toggled(self, toggled: bool):
        if toggled:
            if self._cbSpellCheck.isChecked():
                self._cbSpellCheck.setChecked(False)
                self.ui.textEdit.setGrammarCheckEnabled(False)
                self.ui.textEdit.checkGrammar()
        self.ui.textEdit.setWordTagHighlighterEnabled(toggled)

    def _scene_separator_clicked(self, scene: Scene):
        if not self.ui.btnSceneInfo.isChecked():
            self.ui.btnSceneInfo.setChecked(True)
        self._miniSceneEditor.selectScene(scene)

    def _language_changed(self, lang: str):
        emit_info('Novel is getting closed. Persist workspace...')
        self.novel.lang_settings.lang = lang
        self.repo.update_project_novel(self.novel)
        flush_or_fail()
        emit_global_event(CloseNovelEvent(self, self.novel))

    def _is_empty_page(self) -> bool:
        return self.ui.stackedWidget.currentWidget() == self.ui.pageEmpty

    def _empty_page(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageEmpty)
