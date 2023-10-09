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

from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtGui import QFont
from overrides import overrides
from qthandy import retain_when_hidden, transparent, decr_icon
from qthandy.filter import OpacityEventFilter

from src.main.python.plotlyst.common import PLOTLYST_MAIN_COLOR
from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Document
from src.main.python.plotlyst.event.core import emit_global_event
from src.main.python.plotlyst.events import NovelUpdatedEvent, \
    SceneChangedEvent
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import ButtonPressResizeEventFilter, set_tab_icon
from src.main.python.plotlyst.view.dialog.novel import NovelEditionDialog, SynopsisEditorDialog
from src.main.python.plotlyst.view.generated.novel_view_ui import Ui_NovelView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.style.base import apply_border_image
from src.main.python.plotlyst.view.widget.button import SecondaryActionToolButton
from src.main.python.plotlyst.view.widget.plot import PlotEditor
from src.main.python.plotlyst.view.widget.settings import NovelSettingsWidget
from src.main.python.plotlyst.view.widget.story_map import EventsMindMapView


class NovelView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel, [SceneChangedEvent], global_event_types=[NovelUpdatedEvent])
        self.ui = Ui_NovelView()
        self.ui.setupUi(self.widget)

        set_tab_icon(self.ui.tabWidget, self.ui.tabEvents,
                     IconRegistry.from_name('ri.mind-map', color_on=PLOTLYST_MAIN_COLOR))
        set_tab_icon(self.ui.tabWidget, self.ui.tabStructure,
                     IconRegistry.story_structure_icon(color_on=PLOTLYST_MAIN_COLOR))
        set_tab_icon(self.ui.tabWidget, self.ui.tabPlot, IconRegistry.storylines_icon(color_on=PLOTLYST_MAIN_COLOR))
        set_tab_icon(self.ui.tabWidget, self.ui.tabSynopsis,
                     IconRegistry.from_name('fa5s.scroll', color_on=PLOTLYST_MAIN_COLOR))
        set_tab_icon(self.ui.tabWidget, self.ui.tabTags, IconRegistry.tags_icon(color_on=PLOTLYST_MAIN_COLOR))
        set_tab_icon(self.ui.tabWidget, self.ui.tabSettings, IconRegistry.cog_icon(color_on=PLOTLYST_MAIN_COLOR))

        self.ui.btnEditNovel.setIcon(IconRegistry.edit_icon(color_on='darkBlue'))
        self.ui.btnEditNovel.installEventFilter(OpacityEventFilter(parent=self.ui.btnEditNovel))
        self.ui.btnEditNovel.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnEditNovel))
        self.ui.btnEditNovel.clicked.connect(self._edit_novel)
        retain_when_hidden(self.ui.btnEditNovel)
        self.ui.wdgTitle.installEventFilter(self)
        self.ui.btnEditNovel.setHidden(True)

        self.ui.textPremise.textEdit.setPlaceholderText('Premise')
        font = self.ui.textPremise.textEdit.font()
        font.setFamily('Garamond')
        font.setPointSize(16)
        self.ui.textPremise.textEdit.setFont(font)
        self.ui.textPremise.textEdit.setAcceptRichText(False)
        self.ui.textPremise.textEdit.setSidebarEnabled(False)
        self.ui.textPremise.textEdit.setDocumentMargin(0)

        self._btnPremiseVariants = SecondaryActionToolButton()
        self._btnPremiseVariants.setToolTip('Premise variants')
        self._btnPremiseVariants.setIcon(IconRegistry.from_name('mdi.list-status'))
        self._btnPremiseVariants.installEventFilter(OpacityEventFilter(self._btnPremiseVariants, leaveOpacity=0.55))
        self._btnPremiseVariants.setDisabled(True)
        self._btnPremiseVariants.setHidden(True)
        self.ui.subtitlePremise.addWidget(self._btnPremiseVariants)

        self._btnSynopsisExtendEdit = SecondaryActionToolButton()
        self._btnSynopsisExtendEdit.setToolTip('Edit in full view')
        self._btnSynopsisExtendEdit.setIcon(IconRegistry.expand_icon())
        decr_icon(self._btnSynopsisExtendEdit, 3)
        self._btnSynopsisExtendEdit.installEventFilter(
            OpacityEventFilter(self._btnSynopsisExtendEdit, leaveOpacity=0.55))
        self.ui.subtitleSynopsis.addWidget(self._btnSynopsisExtendEdit)
        self._btnSynopsisExtendEdit.clicked.connect(self._expandSynopsisEditor)

        self.ui.lblTitle.setText(self.novel.title)
        self.ui.textPremise.textEdit.insertPlainText(self.novel.premise)
        self.ui.textPremise.textEdit.textChanged.connect(self._premise_changed)
        self._premise_changed()
        self.ui.textSynopsis.setPlaceholderText("Write down your story's main events")
        self.ui.textSynopsis.setMargins(0, 10, 0, 10)
        self.ui.textSynopsis.textEdit.setSidebarEnabled(False)
        self.ui.textSynopsis.textEdit.setTabChangesFocus(True)
        self.ui.textSynopsis.setGrammarCheckEnabled(True)
        self.ui.textPremise.setGrammarCheckEnabled(True)

        self.ui.textPremise.setToolbarVisible(False)
        self.ui.textPremise.setTitleVisible(False)
        self.ui.textSynopsis.setToolbarVisible(False)
        self.ui.textSynopsis.setTitleVisible(False)
        if self.novel.synopsis:
            json_client.load_document(self.novel, self.novel.synopsis)
            self.ui.textSynopsis.setText(self.novel.synopsis.content)
            self.ui.lblSynopsisWords.setWordCount(self.ui.textSynopsis.textEdit.statistics().word_count)
        self.ui.textSynopsis.textEdit.textChanged.connect(self._synopsis_changed)

        self._eventsMap = EventsMindMapView(self.novel)
        self.ui.wdgEventsMapParent.layout().addWidget(self._eventsMap)

        self.ui.wdgStructure.setNovel(self.novel)
        self.ui.wdgTitle.setFixedHeight(150)
        apply_border_image(self.ui.wdgTitle, resource_registry.frame1)

        self.plot_editor = PlotEditor(self.novel)
        self.ui.wdgPlotContainer.layout().addWidget(self.plot_editor)

        self.ui.wdgTagsContainer.setNovel(self.novel)
        self.ui.tabWidget.setCurrentWidget(self.ui.tabPlot)

        self._settings = NovelSettingsWidget(self.novel)
        self.ui.wdgSettings.layout().addWidget(self._settings)

        self.ui.tabWidget.setCurrentWidget(self.ui.tabSettings)

    @overrides
    def refresh(self):
        self.ui.lblTitle.setText(self.novel.title)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            self.ui.btnEditNovel.setVisible(True)
        elif event.type() == QEvent.Type.Leave:
            self.ui.btnEditNovel.setHidden(True)

        return super(NovelView, self).eventFilter(watched, event)

    def _edit_novel(self):
        title = NovelEditionDialog().display(self.novel)
        if title:
            self.novel.title = title
            self.repo.update_project_novel(self.novel)
            self.ui.lblTitle.setText(self.novel.title)
            emit_global_event(NovelUpdatedEvent(self, self.novel))

    def _premise_changed(self):
        text = self.ui.textPremise.textEdit.toPlainText()
        if not text:
            self.ui.textPremise.textEdit.setFontWeight(QFont.Weight.Bold)
            self.ui.textPremise.textEdit.setStyleSheet(
                'border: 1px dashed darkBlue; border-radius: 6px; background-color: rgba(0, 0, 0, 0);')
        elif not self.novel.premise:
            transparent(self.ui.textPremise.textEdit)

        self.novel.premise = text
        self.ui.lblLoglineWords.calculateWordCount(self.novel.premise)
        self.repo.update_novel(self.novel)

    def _expandSynopsisEditor(self):
        synopsis = SynopsisEditorDialog.display(self.novel)
        self.ui.textSynopsis.setText(synopsis)

    def _synopsis_changed(self):
        if self.novel.synopsis is None:
            self.novel.synopsis = Document('Synopsis')
            self.novel.synopsis.loaded = True
            self.repo.update_novel(self.novel)
        self.novel.synopsis.content = self.ui.textSynopsis.textEdit.toHtml()
        self.ui.lblSynopsisWords.setWordCount(self.ui.textSynopsis.textEdit.statistics().word_count)
        self.repo.update_doc(self.novel, self.novel.synopsis)
