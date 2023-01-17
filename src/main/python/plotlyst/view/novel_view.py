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

from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtGui import QFont
from overrides import overrides
from qthandy import retain_when_hidden, transparent
from qthandy.filter import OpacityEventFilter, InstantTooltipEventFilter

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Document
from src.main.python.plotlyst.event.core import emit_event
from src.main.python.plotlyst.events import NovelUpdatedEvent, \
    SceneChangedEvent
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import link_buttons_to_pages
from src.main.python.plotlyst.view.dialog.novel import NovelEditionDialog, SynopsisEditorDialog
from src.main.python.plotlyst.view.generated.novel_view_ui import Ui_NovelView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import SecondaryActionToolButton
from src.main.python.plotlyst.view.widget.plot import PlotEditor


class NovelView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel, [NovelUpdatedEvent, SceneChangedEvent])
        self.ui = Ui_NovelView()
        self.ui.setupUi(self.widget)

        self.ui.btnStructure.setIcon(IconRegistry.story_structure_icon(color='white'))
        self.ui.btnPlot.setIcon(IconRegistry.plot_icon(color='white'))
        self.ui.btnSynopsis.setIcon(IconRegistry.from_name('fa5s.scroll', 'white'))
        self.ui.btnTags.setIcon(IconRegistry.tags_icon('white'))
        self.ui.btnSettings.setIcon(IconRegistry.cog_icon('white'))
        self.ui.btnSettings.setToolTip('Novel settings are not available yet')
        self.ui.btnSettings.installEventFilter(InstantTooltipEventFilter(self.ui.btnSettings))
        self.setNavigableButtonGroup(self.ui.buttonGroup)

        self.ui.btnEditNovel.setIcon(IconRegistry.edit_icon(color_on='darkBlue'))
        self.ui.btnEditNovel.installEventFilter(OpacityEventFilter(parent=self.ui.btnEditNovel))
        self.ui.btnEditNovel.clicked.connect(self._edit_novel)
        retain_when_hidden(self.ui.btnEditNovel)
        self.ui.wdgTitle.installEventFilter(self)
        self.ui.btnEditNovel.setHidden(True)

        transparent(self.ui.textPremise.textEdit)
        self.ui.textPremise.textEdit.setPlaceholderText('Premise')
        font = self.ui.textPremise.textEdit.font()
        font.setFamily('Helvetica')
        font.setBold(True)
        font.setPointSize(16)
        self.ui.textPremise.textEdit.setFont(font)
        self.ui.textPremise.textEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ui.textPremise.textEdit.setAcceptRichText(False)

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

        self.ui.wdgStructure.setNovel(self.novel)
        self.ui.wdgTitle.setFixedHeight(150)
        self.ui.wdgTitle.setStyleSheet(
            f'#wdgTitle {{border-image: url({resource_registry.frame1}) 0 0 0 0 stretch stretch;}}')

        self.plot_editor = PlotEditor(self.novel)
        self.ui.wdgPlotContainer.layout().addWidget(self.plot_editor)

        self.ui.wdgTagsContainer.setNovel(self.novel)

        link_buttons_to_pages(self.ui.stackedWidget, [(self.ui.btnStructure, self.ui.pageStructure),
                                                      (self.ui.btnPlot, self.ui.pagePlot),
                                                      (self.ui.btnSynopsis, self.ui.pageSynopsis),
                                                      (self.ui.btnTags, self.ui.pageTags),
                                                      (self.ui.btnSettings, self.ui.pageSettings)])
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
            QPushButton:disabled {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 lightGray);
                border: 2px solid grey;
                color: grey;
                opacity: 0.45;
            }
            QPushButton:checked {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #014f86);
                border: 2px solid #013a63;
            }
            ''')
            btn.installEventFilter(OpacityEventFilter(parent=btn, leaveOpacity=0.7, ignoreCheckedButton=True))

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
            emit_event(NovelUpdatedEvent(self, self.novel))

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
