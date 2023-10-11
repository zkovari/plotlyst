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

import qtanim
import qtawesome
from PyQt6.QtCore import Qt, QThreadPool, QEvent, QMimeData, QTimer
from PyQt6.QtGui import QCloseEvent, QPalette, QColor, QKeyEvent, QResizeEvent, QDrag, QWindowStateChangeEvent, QAction
from PyQt6.QtWidgets import QMainWindow, QWidget, QApplication, QLineEdit, QTextEdit, QToolButton, QButtonGroup, \
    QProgressDialog, QAbstractButton
from fbs_runtime import platform
from overrides import overrides
from qthandy import spacer, busy, gc
from qthandy.filter import InstantTooltipEventFilter, OpacityEventFilter
from qttextedit.ops import DEFAULT_FONT_FAMILIES
from textstat import textstat

from src.main.python.plotlyst.common import EXIT_CODE_RESTART, NAV_BAR_BUTTON_DEFAULT_COLOR, \
    NAV_BAR_BUTTON_CHECKED_COLOR, PLOTLYST_MAIN_COLOR
from src.main.python.plotlyst.core.client import client, json_client
from src.main.python.plotlyst.core.domain import Novel, NovelPanel, ScenesView, NovelSetting
from src.main.python.plotlyst.core.text import sentence_count
from src.main.python.plotlyst.env import app_env, open_location
from src.main.python.plotlyst.event.core import event_log_reporter, EventListener, Event, global_event_sender, \
    emit_info, event_senders, EventSender
from src.main.python.plotlyst.event.handler import EventLogHandler, global_event_dispatcher, event_dispatchers, \
    EventDispatcher
from src.main.python.plotlyst.events import NovelDeletedEvent, \
    NovelUpdatedEvent, OpenDistractionFreeMode, ExitDistractionFreeMode, CloseNovelEvent, NovelPanelCustomizationEvent, \
    NovelWorldBuildingToggleEvent, NovelCharactersToggleEvent, NovelScenesToggleEvent, NovelDocumentsToggleEvent, \
    NovelManagementToggleEvent, NovelManuscriptToggleEvent
from src.main.python.plotlyst.resources import resource_manager, ResourceType, ResourceDownloadedEvent
from src.main.python.plotlyst.service.cache import acts_registry
from src.main.python.plotlyst.service.dir import select_new_project_directory
from src.main.python.plotlyst.service.grammar import LanguageToolServerSetupWorker, dictionary, language_tool_proxy
from src.main.python.plotlyst.service.importer import ScrivenerSyncImporter
from src.main.python.plotlyst.service.manuscript import export_manuscript_to_docx
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.service.resource import download_resource, download_nltk_resources
from src.main.python.plotlyst.service.tour import TourService
from src.main.python.plotlyst.settings import settings
from src.main.python.plotlyst.view._view import AbstractView
from src.main.python.plotlyst.view.board_view import BoardView
from src.main.python.plotlyst.view.characters_view import CharactersView
from src.main.python.plotlyst.view.comments_view import CommentsView
from src.main.python.plotlyst.view.common import TooltipPositionEventFilter
from src.main.python.plotlyst.view.dialog.about import AboutDialog
from src.main.python.plotlyst.view.dialog.manuscript import ManuscriptPreviewDialog
from src.main.python.plotlyst.view.dialog.template import customize_character_profile
from src.main.python.plotlyst.view.docs_view import DocumentsView
from src.main.python.plotlyst.view.generated.main_window_ui import Ui_MainWindow
from src.main.python.plotlyst.view.home_view import HomeView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.manuscript_view import ManuscriptView
from src.main.python.plotlyst.view.novel_view import NovelView
from src.main.python.plotlyst.view.reports_view import ReportsView
from src.main.python.plotlyst.view.scenes_view import ScenesOutlineView
from src.main.python.plotlyst.view.widget.button import ToolbarButton, NovelSyncButton
from src.main.python.plotlyst.view.widget.hint import reset_hints
from src.main.python.plotlyst.view.widget.input import CapitalizationEventFilter
from src.main.python.plotlyst.view.widget.settings import NovelQuickPanelCustomizationButton, panel_events
from src.main.python.plotlyst.view.widget.tour.core import TutorialNovelOpenTourEvent, tutorial_novel, \
    TutorialNovelCloseTourEvent, NovelTopLevelButtonTourEvent, HomeTopLevelButtonTourEvent, NovelEditorDisplayTourEvent, \
    AllNovelViewsTourEvent, GeneralNovelViewTourEvent, CharacterViewTourEvent, ScenesViewTourEvent, \
    DocumentsViewTourEvent, ManuscriptViewTourEvent, AnalysisViewTourEvent, BoardViewTourEvent, BaseNovelViewTourEvent
from src.main.python.plotlyst.view.widget.utility import ResourceManagerDialog
from src.main.python.plotlyst.view.world_building_view import WorldBuildingView

textstat.sentence_count = sentence_count


class MainWindow(QMainWindow, Ui_MainWindow, EventListener):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.resize(1000, 630)
        if app_env.is_dev():
            self.resize(1200, 830)
        if app_env.is_prod():
            self.setWindowState(Qt.WindowState.WindowMaximized)

        palette = QApplication.palette()
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, QColor('#040406'))
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, QColor('#040406'))
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, QColor('#040406'))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(PLOTLYST_MAIN_COLOR))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor('#8E9AAF'))
        palette.setColor(QPalette.ColorRole.Window, QColor('#EFEFF4'))
        QApplication.setPalette(palette)

        if app_env.is_mac():
            DEFAULT_FONT_FAMILIES.insert(0, 'Palatino')
        elif app_env.is_linux():
            DEFAULT_FONT_FAMILIES.insert(0, 'Noto Sans Mono')
            DEFAULT_FONT_FAMILIES.insert(3 if len(DEFAULT_FONT_FAMILIES) > 5 else -1, 'Calibri')

        self.novel = None
        self._current_text_widget = None
        self._actionScrivener: Optional[QAction] = None
        self._actionSettings: Optional[QAction] = None
        last_novel_id = settings.last_novel_id()
        if last_novel_id is not None:
            has_novel = client.has_novel(last_novel_id)
            if has_novel:
                self.novel = client.fetch_novel(last_novel_id)

        if self.novel:
            acts_registry.set_novel(self.novel)
            dictionary.set_novel(self.novel)
            app_env.novel = self.novel

        self.home_view = HomeView()
        self.pageHome.layout().addWidget(self.home_view.widget)
        self.home_view.loadNovel.connect(self._load_new_novel)

        self._init_menubar()
        self._init_toolbar()
        self._init_statusbar()

        self.btnBoard.setIcon(IconRegistry.board_icon(NAV_BAR_BUTTON_DEFAULT_COLOR, NAV_BAR_BUTTON_CHECKED_COLOR))
        self.btnNovel.setIcon(IconRegistry.book_icon(NAV_BAR_BUTTON_DEFAULT_COLOR, NAV_BAR_BUTTON_CHECKED_COLOR))
        self.btnCharacters.setIcon(
            IconRegistry.character_icon(NAV_BAR_BUTTON_DEFAULT_COLOR, NAV_BAR_BUTTON_CHECKED_COLOR))
        self.btnScenes.setIcon(IconRegistry.scene_icon(NAV_BAR_BUTTON_DEFAULT_COLOR, NAV_BAR_BUTTON_CHECKED_COLOR))
        self.btnWorld.setIcon(
            IconRegistry.world_building_icon(NAV_BAR_BUTTON_DEFAULT_COLOR, NAV_BAR_BUTTON_CHECKED_COLOR))
        self.btnNotes.setIcon(
            IconRegistry.document_edition_icon(NAV_BAR_BUTTON_DEFAULT_COLOR, NAV_BAR_BUTTON_CHECKED_COLOR))
        self.btnManuscript.setIcon(
            IconRegistry.manuscript_icon(NAV_BAR_BUTTON_DEFAULT_COLOR, NAV_BAR_BUTTON_CHECKED_COLOR))
        self.btnReports.setIcon(IconRegistry.reports_icon(NAV_BAR_BUTTON_DEFAULT_COLOR, NAV_BAR_BUTTON_CHECKED_COLOR))

        for btn in self.buttonGroup.buttons():
            btn.installEventFilter(OpacityEventFilter(btn, leaveOpacity=0.7, ignoreCheckedButton=True))
            btn.installEventFilter(TooltipPositionEventFilter(btn))

        self.event_log_handler = EventLogHandler(self.statusBar())
        event_log_reporter.info.connect(self.event_log_handler.on_info_event)
        event_log_reporter.error.connect(self.event_log_handler.on_error_event)
        global_event_sender.send.connect(global_event_dispatcher.dispatch)
        QApplication.instance().focusChanged.connect(self._focus_changed)
        global_event_dispatcher.register(self, NovelDeletedEvent, NovelUpdatedEvent, OpenDistractionFreeMode,
                                         ExitDistractionFreeMode, ResourceDownloadedEvent, TutorialNovelOpenTourEvent,
                                         TutorialNovelCloseTourEvent, NovelTopLevelButtonTourEvent,
                                         HomeTopLevelButtonTourEvent, NovelEditorDisplayTourEvent,
                                         AllNovelViewsTourEvent,
                                         GeneralNovelViewTourEvent,
                                         CharacterViewTourEvent, ScenesViewTourEvent, DocumentsViewTourEvent,
                                         ManuscriptViewTourEvent, AnalysisViewTourEvent, BoardViewTourEvent,
                                         CloseNovelEvent)

        self._init_views()

        self._tour_service = TourService.instance()
        self.repo = RepositoryPersistenceManager.instance()

        self._threadpool = QThreadPool()
        self._language_tool_setup_worker = LanguageToolServerSetupWorker()
        if not app_env.test_env():
            download_nltk_resources()
            download_resource(ResourceType.JRE_8)
            download_resource(ResourceType.PANDOC)

        if self.novel:
            self._language_tool_setup_worker.lang = self.novel.lang_settings.lang
        if not app_env.test_env():
            if resource_manager.has_resource(ResourceType.JRE_8):
                emit_info('Start initializing grammar checker...')
                self._threadpool.start(self._language_tool_setup_worker)

            QApplication.instance().installEventFilter(CapitalizationEventFilter(self))

    @overrides
    def closeEvent(self, event: QCloseEvent) -> None:
        if language_tool_proxy.is_set():
            language_tool_proxy.tool.close()

        if self.novel:
            self._persist_last_novel_state()

        if self._threadpool.activeThreadCount():
            max_ = self._threadpool.activeThreadCount()
            progress = QProgressDialog('Wait until background tasks are finished...', 'Shut down anyway', 0,
                                       self._threadpool.activeThreadCount(), parent=self.centralwidget)
            progress.forceShow()
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            while True:
                self._threadpool.waitForDone(500)
                count = self._threadpool.activeThreadCount()
                progress.setValue(max_ - count)
                if count == 0:
                    break
                if progress.wasCanceled():
                    break

            if language_tool_proxy.is_set():
                language_tool_proxy.tool.close()

    @overrides
    def keyPressEvent(self, event: QKeyEvent) -> None:
        def modifier() -> Qt.KeyboardModifier:
            if app_env.is_mac():
                return Qt.KeyboardModifier.AltModifier
            else:
                return Qt.KeyboardModifier.ControlModifier

        if event.key() == Qt.Key.Key_Tab and event.modifiers() & modifier():
            if self._current_view is not None:
                self._current_view.jumpToNext()
        elif event.key() == Qt.Key.Key_Backtab and event.modifiers() & modifier():
            if self._current_view is not None:
                self._current_view.jumpToPrevious()
        else:
            super(MainWindow, self).keyPressEvent(event)
            return

        event.ignore()

    @overrides
    def event(self, event: QEvent) -> bool:
        def fake_drag():
            drag = QDrag(self)
            mimedate = QMimeData()
            mimedate.setText('')
            drag.setMimeData(mimedate)
            QTimer.singleShot(100, lambda: gc(drag))
            drag.exec()

        if isinstance(event, QWindowStateChangeEvent):
            if app_env.is_mac() and self.windowState() == Qt.WindowState.WindowFullScreen:
                QTimer.singleShot(100, fake_drag)

        return super(MainWindow, self).event(event)

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        if app_env.is_dev():
            emit_info(f'Size: {event.size().width()}:{event.size().height()}')

    @overrides
    def event_received(self, event: Event):
        def handle_novel_navbar_tour_event(event_: BaseNovelViewTourEvent, btn: QAbstractButton):
            if event_.click_before:
                btn.click()
            self._tour_service.addWidget(btn, event_)

        if isinstance(event, (NovelDeletedEvent, CloseNovelEvent)):
            if self.novel and event.novel.id == self.novel.id:
                self.close_novel()
        elif isinstance(event, NovelUpdatedEvent):
            if self.novel and event.novel.id == self.novel.id:
                self.novel.title = event.novel.title
                self.outline_mode.setText(self.novel.title)
        elif isinstance(event, OpenDistractionFreeMode):
            self.btnComments.setChecked(False)
            self._toggle_fullscreen(on=True)
        elif isinstance(event, ExitDistractionFreeMode):
            self._toggle_fullscreen(on=False)
        elif isinstance(event, ResourceDownloadedEvent):
            if event.type == ResourceType.JRE_8:
                emit_info('Start initializing grammar checker...')
                self._threadpool.start(self._language_tool_setup_worker)
        elif isinstance(event, TutorialNovelOpenTourEvent):
            self._load_new_novel(tutorial_novel)
            self._tour_service.next()
        elif isinstance(event, TutorialNovelCloseTourEvent):
            if self.novel and self.novel.tutorial:
                self.close_novel()
        elif isinstance(event, NovelPanelCustomizationEvent):
            self._handle_customization_event(event)
        elif isinstance(event, NovelEditorDisplayTourEvent):
            self._tour_service.addWidget(self.pageOutline, event)
        elif isinstance(event, NovelTopLevelButtonTourEvent):
            self._tour_service.addWidget(self.outline_mode, event)
        elif isinstance(event, HomeTopLevelButtonTourEvent):
            self._tour_service.addWidget(self.home_mode, event)
        elif isinstance(event, AllNovelViewsTourEvent):
            self._tour_service.addWidget(self.wdgNavBar, event)
        elif isinstance(event, GeneralNovelViewTourEvent):
            handle_novel_navbar_tour_event(event, self.btnNovel)
        elif isinstance(event, CharacterViewTourEvent):
            handle_novel_navbar_tour_event(event, self.btnCharacters)
        elif isinstance(event, ScenesViewTourEvent):
            handle_novel_navbar_tour_event(event, self.btnScenes)
        elif isinstance(event, DocumentsViewTourEvent):
            handle_novel_navbar_tour_event(event, self.btnNotes)
        elif isinstance(event, ManuscriptViewTourEvent):
            handle_novel_navbar_tour_event(event, self.btnManuscript)
        elif isinstance(event, AnalysisViewTourEvent):
            handle_novel_navbar_tour_event(event, self.btnReports)
        elif isinstance(event, BoardViewTourEvent):
            handle_novel_navbar_tour_event(event, self.btnBoard)

    def close_novel(self):
        self.novel = None
        self._clear_novel()
        self.home_mode.setChecked(True)

    def _toggle_fullscreen(self, on: bool):
        self.wdgNavBar.setHidden(on)
        self.statusbar.setHidden(on)
        self.toolBar.setHidden(on)
        if not platform.is_mac():
            self.menubar.setHidden(on)
            if not on:
                self.showMaximized()
        if not self.isFullScreen():
            if on:
                self.showFullScreen()

    @busy
    def _init_views(self):
        self.buttonGroup.buttonToggled.connect(self._on_view_changed)

        if not self.novel:
            for btn in self.buttonGroup.buttons():
                btn.setHidden(True)
            self._actionSettings.setVisible(False)
            return

        sender: EventSender = event_senders.instance(self.novel)
        dispatcher: EventDispatcher = event_dispatchers.instance(self.novel)
        sender.send.connect(dispatcher.dispatch)
        dispatcher.register(self, *panel_events)

        for btn in self.buttonGroup.buttons():
            btn.setVisible(True)

        self._actionSettings.setVisible(True)
        self.btnSettings.setNovel(self.novel)
        self.outline_mode.setEnabled(True)
        self.outline_mode.setVisible(True)

        if self.novel and self.novel.is_scrivener_sync():
            self._actionScrivener.setVisible(True)
            self.btnScrivener.setImporter(ScrivenerSyncImporter(), self.novel)
        else:
            self._actionScrivener.setVisible(False)
            self.btnScrivener.clear()

        self._current_view: Optional[AbstractView] = None
        self.novel_view = NovelView(self.novel)
        self.characters_view = CharactersView(self.novel)
        self.scenes_outline_view = ScenesOutlineView(self.novel)
        self.world_building_view = WorldBuildingView(self.novel)
        self.notes_view = DocumentsView(self.novel)
        self.board_view = BoardView(self.novel)
        self.manuscript_view = ManuscriptView(self.novel)
        self.reports_view = ReportsView(self.novel)
        self.comments_view = CommentsView(self.novel)
        self.pageComments.layout().addWidget(self.comments_view.widget)
        self.wdgSidebar.setCurrentWidget(self.pageComments)

        self.pageNovel.layout().addWidget(self.novel_view.widget)
        self.pageCharacters.layout().addWidget(self.characters_view.widget)
        self.pageScenes.layout().addWidget(self.scenes_outline_view.widget)
        self.pageWorld.layout().addWidget(self.world_building_view.widget)
        self.pageNotes.layout().addWidget(self.notes_view.widget)
        self.pageBoard.layout().addWidget(self.board_view.widget)
        self.pageManuscript.layout().addWidget(self.manuscript_view.widget)
        self.pageAnalysis.layout().addWidget(self.reports_view.widget)

        if self.novel.prefs.panels.scenes_view == ScenesView.NOVEL:
            self.btnNovel.setChecked(True)
        elif self.novel.prefs.panels.scenes_view == ScenesView.CHARACTERS:
            self.btnCharacters.setChecked(True)
        elif self.novel.prefs.panels.scenes_view == ScenesView.WORLD_BUILDING:
            self.btnWorld.setChecked(True)
        elif self.novel.prefs.panels.scenes_view == ScenesView.DOCS:
            self.btnNotes.setChecked(True)
        elif self.novel.prefs.panels.scenes_view == ScenesView.BOARD:
            self.btnBoard.setChecked(True)
        elif self.novel.prefs.panels.scenes_view == ScenesView.MANUSCRIPT:
            self.btnManuscript.setChecked(True)
        elif self.novel.prefs.panels.scenes_view == ScenesView.REPORTS:
            self.btnReports.setChecked(True)
        elif self.novel.prefs.panels.scenes_view == ScenesView.SCENES:
            self.btnScenes.setChecked(True)
        else:
            self.btnNovel.setChecked(True)

        self.btnCharacters.setVisible(self.novel.prefs.settings.get(NovelSetting.Characters.value, True))
        self.btnScenes.setVisible(self.novel.prefs.settings.get(NovelSetting.Scenes.value, True))
        self.btnWorld.setVisible(self.novel.prefs.settings.get(NovelSetting.World_building.value, True))
        self.btnNotes.setVisible(self.novel.prefs.settings.get(NovelSetting.Documents.value, True))
        self.btnManuscript.setVisible(self.novel.prefs.settings.get(NovelSetting.Manuscript.value, True))
        self.btnBoard.setVisible(self.novel.prefs.settings.get(NovelSetting.Management.value, True))

    def _on_view_changed(self, btn=None, checked: bool = True):
        if not checked:
            return

        if self.btnBoard.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageBoard)
            self._current_view = self.board_view
        elif self.btnNovel.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageNovel)
            self.novel_view.activate()
            self._current_view = self.novel_view
        elif self.btnCharacters.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageCharacters)
            self.characters_view.activate()
            self._current_view = self.characters_view
        elif self.btnScenes.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageScenes)
            self.scenes_outline_view.activate()
            self._current_view = self.scenes_outline_view
        elif self.btnWorld.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageWorld)
            self._current_view = self.world_building_view
        elif self.btnNotes.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageNotes)
            self.notes_view.activate()
            self._current_view = self.notes_view
        elif self.btnManuscript.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageManuscript)
            self.manuscript_view.activate()
            self._current_view = self.manuscript_view
        elif self.btnReports.isChecked():
            self.stackedWidget.setCurrentWidget(self.pageAnalysis)
        else:
            self._current_view = None

    def _init_menubar(self):
        self.menubar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        if app_env.is_prod():
            self.menuFile.removeAction(self.actionRestart)
        else:
            self.actionRestart.setIcon(qtawesome.icon('mdi.restart'))
            self.actionRestart.triggered.connect(self._restart)

        self.actionResetHints.triggered.connect(lambda: reset_hints())
        self.actionAbout.triggered.connect(lambda: AboutDialog().exec())
        self.actionIncreaseFontSize.setIcon(IconRegistry.increase_font_size_icon())
        self.actionIncreaseFontSize.setDisabled(True)
        self.actionDecreaseFontSize.setIcon(IconRegistry.decrease_font_size_icon())
        self.actionDecreaseFontSize.setDisabled(True)
        self.actionPreview.triggered.connect(lambda: ManuscriptPreviewDialog().display(app_env.novel))
        self.actionCut.setIcon(IconRegistry.cut_icon())
        self.actionCut.triggered.connect(self._cut_text)
        self.actionCopy.setIcon(IconRegistry.copy_icon())
        self.actionCopy.triggered.connect(self._copy_text)
        self.actionPaste.setIcon(IconRegistry.paste_icon())
        self.actionPaste.triggered.connect(self._paste_text)

        self.actionResourceManager.triggered.connect(lambda: ResourceManagerDialog().display())

        self.actionDirPlaceholder.setText(settings.workspace())
        self.actionOpenProjectDir.setIcon(IconRegistry.from_name('fa5s.external-link-alt'))
        self.actionOpenProjectDir.triggered.connect(lambda: open_location(settings.workspace()))
        self.actionChangeDir.setIcon(IconRegistry.from_name('fa5s.folder-open'))
        self.actionChangeDir.triggered.connect(self._change_project_dir)

        self.actionExportToDocx.setIcon(IconRegistry.docx_icon())
        self.actionExportToDocx.triggered.connect(lambda: export_manuscript_to_docx(self.novel))

        self.actionCharacterTemplateEditor.triggered.connect(lambda: customize_character_profile(self.novel, 0, self))

    def _init_toolbar(self):
        self.toolBar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)

        self.home_mode = ToolbarButton(self.toolBar)
        self.home_mode.setText('Home')
        self.home_mode.setIcon(IconRegistry.home_icon(color_on='#240046'))

        self.outline_mode = ToolbarButton(self.toolBar)
        self.outline_mode.setMinimumWidth(80)
        self.outline_mode.setText('My novel')
        self.outline_mode.setIcon(IconRegistry.book_icon(color_on='#240046'))

        self._mode_btn_group = QButtonGroup()
        self._mode_btn_group.addButton(self.home_mode)
        self._mode_btn_group.addButton(self.outline_mode)
        self._mode_btn_group.setExclusive(True)
        self._mode_btn_group.buttonToggled.connect(self._panel_toggled)

        self.btnSettings = NovelQuickPanelCustomizationButton()

        self.btnComments = QToolButton(self.toolBar)
        self.btnComments.setIcon(IconRegistry.from_name('mdi.comment-outline', color='#2e86ab'))
        self.btnComments.setMinimumWidth(50)
        self.btnComments.setCheckable(True)
        self.btnComments.toggled.connect(self.wdgSidebar.setVisible)
        self.btnComments.setDisabled(True)
        self.btnComments.setToolTip('Comments are not available yet')
        self.btnComments.installEventFilter(InstantTooltipEventFilter(self.btnComments))

        self.btnScrivener = NovelSyncButton()

        self.toolBar.addWidget(spacer(5))
        self.toolBar.addWidget(self.home_mode)
        self.toolBar.addWidget(spacer(5))
        self.toolBar.addSeparator()
        self.toolBar.addWidget(spacer(5))
        self.toolBar.addWidget(self.outline_mode)
        self.toolBar.addWidget(spacer())
        self._actionScrivener = self.toolBar.addWidget(self.btnScrivener)
        self._actionSettings = self.toolBar.addWidget(self.btnSettings)
        self.toolBar.addWidget(self.btnComments)

        self.wdgSidebar.setHidden(True)
        self.wdgDocs.setHidden(True)

        if self.novel:
            self.outline_mode.setChecked(True)
            self.outline_mode.setText(self.novel.title)
        else:
            self.home_mode.setChecked(True)
            self.outline_mode.setDisabled(True)
            self.outline_mode.setText('')

    def _init_statusbar(self):
        pass
        # self.statusbar.addPermanentWidget(self._tasks_widget)

    def _panel_toggled(self):
        if self.home_mode.isChecked():
            self.stackMainPanels.setCurrentWidget(self.pageHome)
        if self.outline_mode.isChecked():
            self.stackMainPanels.setCurrentWidget(self.pageOutline)
            self._on_view_changed()

    def _change_project_dir(self):
        workspace = select_new_project_directory()
        if workspace:
            self.home_mode.setChecked(True)
            settings.set_workspace(workspace)
            if self.novel:
                self.close_novel()

            json_client.init(workspace)
            self.home_view.refresh()
            self.actionDirPlaceholder.setText(settings.workspace())

    def _increase_font_size(self):
        current_font = QApplication.font()
        self._set_font_size(current_font.pointSize() + 1)

    def decrease_font_size(self):
        current_font = QApplication.font()
        self._set_font_size(current_font.pointSize() - 1)

    def _set_font_size(self, value: int):
        current_font = QApplication.font()
        current_font.setPointSizeF(value)
        QApplication.instance().setFont(current_font)

        for widget in QApplication.allWidgets():
            if widget is self.menubar:
                continue
            font = widget.font()
            font.setPointSizeF(value)
            widget.setFont(font)

    @busy
    def _load_new_novel(self, novel: Novel):
        if self.novel and self.novel.id == novel.id:
            self.outline_mode.setChecked(True)
            return

        self.repo.flush(sync=True)
        if self.novel:
            self._clear_novel()

        if novel.tutorial:
            self.novel = novel
        else:
            self.novel = client.fetch_novel(novel.id)
        self.repo.set_persistence_enabled(not novel.tutorial)
        acts_registry.set_novel(self.novel)
        dictionary.set_novel(self.novel)
        app_env.novel = self.novel

        if language_tool_proxy.is_set():
            language_tool_proxy.tool.language = self.novel.lang_settings.lang

        self._init_views()
        if not novel.tutorial:
            settings.set_last_novel_id(self.novel.id)

        self.outline_mode.setEnabled(True)
        self.outline_mode.setVisible(True)
        self.outline_mode.setText(self.novel.title)
        self.outline_mode.setChecked(True)

        self.menuExport.setEnabled(True)
        self.actionPreview.setEnabled(True)

    def _clear_novel(self):
        event_senders.pop(self.novel)
        event_dispatchers.pop(self.novel)

        self.pageNovel.layout().removeWidget(self.novel_view.widget)
        gc(self.novel_view.widget)
        gc(self.novel_view)
        self.novel_view = None

        self.pageCharacters.layout().removeWidget(self.characters_view.widget)
        gc(self.characters_view.widget)
        gc(self.characters_view)
        self.characters_view = None

        self.pageScenes.layout().removeWidget(self.scenes_outline_view.widget)
        gc(self.scenes_outline_view.widget)
        gc(self.scenes_outline_view)
        self.scenes_outline_view = None

        self.pageNotes.layout().removeWidget(self.notes_view.widget)
        gc(self.notes_view.widget)
        gc(self.notes_view)
        self.notes_view = None

        self.pageWorld.layout().removeWidget(self.world_building_view.widget)
        gc(self.world_building_view.widget)
        gc(self.world_building_view)
        self.world_building_view = None

        self.pageBoard.layout().removeWidget(self.board_view.widget)
        gc(self.board_view.widget)
        gc(self.board_view)
        self.board_view = None

        self.pageBoard.layout().removeWidget(self.reports_view.widget)
        gc(self.reports_view.widget)
        gc(self.reports_view)
        self.reports_view = None

        self.pageManuscript.layout().removeWidget(self.manuscript_view.widget)
        gc(self.manuscript_view.widget)
        gc(self.manuscript_view)
        self.manuscript_view = None

        self.pageComments.layout().removeWidget(self.comments_view.widget)
        gc(self.comments_view.widget)
        gc(self.comments_view)
        self.comments_view = None

        self._actionSettings.setVisible(False)

        self.outline_mode.setDisabled(True)
        self.outline_mode.setText('')

        self.menuExport.setDisabled(True)
        self.actionPreview.setDisabled(True)

    def _focus_changed(self, old_widget: QWidget, current_widget: QWidget):
        if isinstance(current_widget, (QLineEdit, QTextEdit)):
            text_actions_enabled = True
            self._current_text_widget = current_widget
        else:
            text_actions_enabled = False
            self._current_text_widget = None
        self.actionCut.setEnabled(text_actions_enabled)
        self.actionCopy.setEnabled(text_actions_enabled)
        self.actionPaste.setEnabled(text_actions_enabled)

    def _cut_text(self):
        if self._current_text_widget:
            self._current_text_widget.cut()

    def _copy_text(self):
        if self._current_text_widget:
            self._current_text_widget.copy()

    def _paste_text(self):
        if self._current_text_widget:
            self._current_text_widget.paste()

    def _restart(self):
        if self.novel:
            self._persist_last_novel_state()
        if language_tool_proxy.is_set():
            language_tool_proxy.tool.close()
        QApplication.instance().exit(EXIT_CODE_RESTART)

    def _persist_last_novel_state(self):
        if not self.novel:
            return

        self.novel.prefs.panels.panel = NovelPanel.OUTLINE

        if self.stackedWidget.currentWidget() == self.pageNovel:
            scenes_view = ScenesView.NOVEL
        elif self.stackedWidget.currentWidget() == self.pageCharacters:
            scenes_view = ScenesView.CHARACTERS
        elif self.stackedWidget.currentWidget() == self.pageScenes:
            scenes_view = ScenesView.SCENES
        elif self.stackedWidget.currentWidget() == self.pageWorld:
            scenes_view = ScenesView.WORLD_BUILDING
        elif self.stackedWidget.currentWidget() == self.pageNotes:
            scenes_view = ScenesView.DOCS
        elif self.stackedWidget.currentWidget() == self.pageBoard:
            scenes_view = ScenesView.BOARD
        elif self.stackedWidget.currentWidget() == self.pageManuscript:
            scenes_view = ScenesView.MANUSCRIPT
        elif self.stackedWidget.currentWidget() == self.pageAnalysis:
            scenes_view = ScenesView.REPORTS
        else:
            scenes_view = None
        self.novel.prefs.panels.scenes_view = scenes_view

        self.repo.update_novel(self.novel)

    def _handle_customization_event(self, event: NovelPanelCustomizationEvent):
        func = qtanim.fade_in if event.toggled else qtanim.fade_out
        if isinstance(event, NovelWorldBuildingToggleEvent):
            func(self.btnWorld)
        elif isinstance(event, NovelCharactersToggleEvent):
            func(self.btnCharacters)
        elif isinstance(event, NovelScenesToggleEvent):
            func(self.btnScenes)
        elif isinstance(event, NovelDocumentsToggleEvent):
            func(self.btnNotes)
        elif isinstance(event, NovelManuscriptToggleEvent):
            func(self.btnManuscript)
        elif isinstance(event, NovelManagementToggleEvent):
            func(self.btnBoard)

        if not self.buttonGroup.checkedButton().isVisible():
            self.btnNovel.setChecked(True)
