"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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
from typing import List, Set, Dict, Optional

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QFileDialog, QDialog, QWidget, QStackedWidget, QButtonGroup, QLineEdit, QLabel
from overrides import overrides
from qthandy import vspacer, sp, hbox, vbox, line, incr_font, spacer
from qthandy.filter import OpacityEventFilter

from plotlyst.common import PLOTLYST_MAIN_COLOR, MAXIMUM_SIZE, RELAXED_WHITE_COLOR
from plotlyst.core.domain import NovelDescriptor, Novel
from plotlyst.core.scrivener import ScrivenerParser
from plotlyst.env import app_env
from plotlyst.resources import ResourceType, resource_registry
from plotlyst.service.manuscript import import_docx
from plotlyst.service.resource import ask_for_resource
from plotlyst.view.common import push_btn, link_buttons_to_pages, tool_btn, label
from plotlyst.view.icons import IconRegistry
from plotlyst.view.layout import group
from plotlyst.view.widget.display import PopupDialog, Subtitle
from plotlyst.view.widget.input import Toggle
from plotlyst.view.widget.novel import NovelCustomizationWizard, ImportedNovelOverview
from plotlyst.view.widget.tree import TreeView, ContainerNode, TreeSettings


class NovelNode(ContainerNode):
    def __init__(self, novel: NovelDescriptor, parent=None, settings: Optional[TreeSettings] = None):
        super(NovelNode, self).__init__(novel.title, parent=parent, settings=settings)
        self._novel = novel
        self.setPlusButtonEnabled(False)
        self.setTranslucentIconEnabled(True)
        self._actionChangeIcon.setVisible(True)
        self.refresh()

    def novel(self) -> NovelDescriptor:
        return self._novel

    def refresh(self):
        self._lblTitle.setText(self._novel.title)
        if self._novel.icon:
            self._icon.setIcon(IconRegistry.from_name(self._novel.icon, self._novel.icon_color))
        else:
            self._icon.setIcon(IconRegistry.book_icon('black', 'black'))
        self._icon.setVisible(True)

    @overrides
    def _iconChanged(self, iconName: str, iconColor: str):
        self._novel.icon = iconName
        self._novel.icon_color = iconColor


class ShelveNode(ContainerNode):
    newNovelRequested = pyqtSignal()

    def __init__(self, title: str, icon: Optional[QIcon] = None, parent=None, settings: Optional[TreeSettings] = None):
        super(ShelveNode, self).__init__(title, icon, parent, settings=settings)
        self.setMenuEnabled(False)
        sp(self._lblTitle).h_min()
        self._btnAdd.setIcon(IconRegistry.plus_icon(PLOTLYST_MAIN_COLOR))
        self._btnAdd.clicked.connect(self.newNovelRequested.emit)


class SeriesNode(ContainerNode):
    pass


class ShelvesTreeView(TreeView):
    novelSelected = pyqtSignal(NovelDescriptor)
    novelChanged = pyqtSignal(NovelDescriptor)
    novelDeletionRequested = pyqtSignal(NovelDescriptor)
    novelOpenRequested = pyqtSignal(NovelDescriptor)
    novelsShelveSelected = pyqtSignal()
    newNovelRequested = pyqtSignal()

    def __init__(self, parent=None, settings: Optional[TreeSettings] = None):
        super(ShelvesTreeView, self).__init__(parent)
        self._settings = settings
        self._centralWidget.setProperty('bg', True)

        self._selectedNovels: Set[NovelDescriptor] = set()
        self._novels: Dict[NovelDescriptor, NovelNode] = {}

        self._wdgNovels = ShelveNode('Novels', IconRegistry.from_name('mdi.bookshelf'), settings=self._settings)
        self._wdgNovels.selectionChanged.connect(self._novelsShelveSelectionChanged)
        self._wdgNovels.newNovelRequested.connect(self.newNovelRequested)
        # self._wdgShortStories = ShelveNode('Short stories', IconRegistry.from_name('ph.file-text'),
        #                                    settings=self._settings)
        # self._wdgIdeas = ShelveNode('Ideas', IconRegistry.decision_icon(), settings=self._settings)
        # self._wdgNotes = ShelveNode('Notes', IconRegistry.document_edition_icon(), settings=self._settings)

        # self._wdgShortStories.setDisabled(True)
        # self._wdgIdeas.setDisabled(True)
        # self._wdgNotes.setDisabled(True)

        self._centralWidget.layout().addWidget(self._wdgNovels)
        # self._centralWidget.layout().addWidget(self._wdgShortStories)
        # self._centralWidget.layout().addWidget(self._wdgIdeas)
        # self._centralWidget.layout().addWidget(self._wdgNotes)
        self._centralWidget.layout().addWidget(vspacer())

    def setSettings(self, settings: TreeSettings):
        self._settings = settings

    def novels(self) -> List[NovelDescriptor]:
        return list(self._novels.keys())

    def setNovels(self, novels: List[NovelDescriptor]):
        self.clearSelection()
        self._novels.clear()

        self._wdgNovels.clearChildren()
        for novel in novels:
            node = NovelNode(novel, settings=self._settings)
            self._wdgNovels.addChild(node)
            self._novels[novel] = node
            node.selectionChanged.connect(partial(self._novelSelectionChanged, node))
            node.iconChanged.connect(partial(self.novelChanged.emit, novel))
            node.deleted.connect(partial(self.novelDeletionRequested.emit, novel))
            node.doubleClicked.connect(partial(self.novelOpenRequested.emit, novel))

    def updateNovel(self, novel: NovelDescriptor):
        self._novels[novel].refresh()

    def selectNovel(self, novel: NovelDescriptor):
        self._wdgNovels.deselect()
        self._novels[novel].select()
        self._selectedNovels.add(novel)
        self.novelSelected.emit(novel)

    def clearSelection(self):
        for novel in self._selectedNovels:
            self._novels[novel].deselect()
        self._selectedNovels.clear()

    def _novelSelectionChanged(self, novelNode: NovelNode, selected: bool):
        if selected:
            self.clearSelection()
            self._wdgNovels.deselect()
            self._selectedNovels.add(novelNode.novel())
            self.novelSelected.emit(novelNode.novel())

    def _novelsShelveSelectionChanged(self, selected: bool):
        if selected:
            self.clearSelection()
            self.novelsShelveSelected.emit()


class StoryCreationDialog(PopupDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._importedNovel: Optional[Novel] = None
        self._wizardNovel: Optional[Novel] = None
        self._wizard: Optional[NovelCustomizationWizard] = None

        self.frame.layout().setSpacing(0)

        self.wdgBanner = QWidget()
        self.wdgBanner.setProperty('banner-bg', True)
        self.lblBanner = QLabel()
        hbox(self.wdgBanner, 0, 0).addWidget(self.lblBanner, alignment=Qt.AlignmentFlag.AlignCenter)
        self.lblBanner.setPixmap(QPixmap(resource_registry.banner))

        self.btnFinish = push_btn(icon=IconRegistry.book_icon(RELAXED_WHITE_COLOR), text='Finish',
                                  properties=['confirm', 'positive'])
        sp(self.btnFinish).h_exp()
        self.btnFinish.clicked.connect(self.accept)
        self.btnFinish.setVisible(False)
        self.btnNext = push_btn(icon=IconRegistry.book_icon(RELAXED_WHITE_COLOR), text='Create',
                                properties=['confirm', 'positive'])
        self.btnNext.clicked.connect(self._nextClicked)
        self.btnCancel = push_btn(icon=IconRegistry.close_icon('grey'), text='Cancel', properties=['confirm', 'cancel'])
        self.btnCancel.clicked.connect(self.reject)

        self.wdgCenter = QWidget()
        hbox(self.wdgCenter)

        self.wdgTypesContainer = QWidget()
        self.wdgTypesContainer.setProperty('bg', True)
        vbox(self.wdgTypesContainer)
        self.btnNewStory = push_btn(IconRegistry.book_icon(color_on=RELAXED_WHITE_COLOR), 'Create a new story',
                                    checkable=True)
        self.btnNewStory.setChecked(True)
        self.btnNewStory.setProperty("main-side-nav", True)
        self.btnScrivener = push_btn(IconRegistry.from_name('mdi.alpha-s-circle-outline', color_on=RELAXED_WHITE_COLOR),
                                     'Import from Scrivener', checkable=True)
        self.btnScrivener.setProperty("main-side-nav", True)
        self.btnDocx = push_btn(IconRegistry.from_name('fa5.file-word', color_on=RELAXED_WHITE_COLOR),
                                'Import from docx', checkable=True)
        self.btnDocx.setProperty("main-side-nav", True)

        self.buttonGroup = QButtonGroup()
        self.buttonGroup.addButton(self.btnNewStory)
        self.buttonGroup.addButton(self.btnScrivener)
        self.buttonGroup.addButton(self.btnDocx)
        for btn in self.buttonGroup.buttons():
            incr_font(btn)
            btn.installEventFilter(OpacityEventFilter(parent=btn, leaveOpacity=0.7, ignoreCheckedButton=True))

        self.wdgTypesContainer.layout().addWidget(self.btnNewStory)
        self.wdgTypesContainer.layout().addWidget(line())
        self.wdgTypesContainer.layout().addWidget(self.btnScrivener)
        self.wdgTypesContainer.layout().addWidget(self.btnDocx)
        self.wdgTypesContainer.layout().addWidget(vspacer())

        self.stackedWidget = QStackedWidget()
        self.wdgRight = QWidget()
        vbox(self.wdgRight).addWidget(self.stackedWidget)
        self.wdgCenter.layout().addWidget(self.wdgTypesContainer)
        self.wdgCenter.layout().addWidget(self.wdgRight)

        self.pageNewStory = QWidget()
        vbox(self.pageNewStory, margin=25, spacing=8)
        self.pageScrivener = QWidget()
        vbox(self.pageScrivener, margin=25, spacing=8)
        self.pageDocx = QWidget()
        vbox(self.pageDocx, margin=25, spacing=8)
        self.pageWizard = QWidget()
        vbox(self.pageWizard)
        self.pageImportedPreview = QWidget()
        self.stackedWidget.addWidget(self.pageNewStory)
        self.stackedWidget.addWidget(self.pageScrivener)
        self.stackedWidget.addWidget(self.pageDocx)
        self.stackedWidget.addWidget(self.pageImportedPreview)
        self.stackedWidget.addWidget(self.pageWizard)

        link_buttons_to_pages(self.stackedWidget,
                              [(self.btnNewStory, self.pageNewStory), (self.btnScrivener, self.pageScrivener),
                               (self.btnDocx, self.pageDocx)])
        self.stackedWidget.currentChanged.connect(self._pageChanged)
        self.stackedWidget.setCurrentWidget(self.pageNewStory)

        self.lineTitle = QLineEdit()
        self.lineTitle.setPlaceholderText("Title (Default: 'My new novel')")
        self.lineTitle.setProperty('rounded', True)
        self.lineTitle.setProperty('white-bg', True)
        incr_font(self.lineTitle, 2)
        self.toggleWizard = Toggle()
        self.toggleWizard.toggled.connect(self._wizardToggled)
        self.toggleWizard.setChecked(True)
        self.wdgWizardSubtitle = Subtitle(title="Personalization wizard",
                                          description="Launch a wizard to customize your writing or outlining experience (recommended)",
                                          icon='ph.magic-wand')
        self.wdgWizardSubtitle.addWidget(self.toggleWizard)

        self.pageNewStory.layout().addWidget(Subtitle(title="What's your story's title?", icon='fa5s.book-open'))
        self.pageNewStory.layout().addWidget(self.lineTitle)
        self.pageNewStory.layout().addWidget(self.wdgWizardSubtitle)
        self.pageNewStory.layout().addWidget(vspacer())

        self.wdgImportDetails = ImportedNovelOverview(self.pageImportedPreview)
        self.wdgImportDetails.setHidden(True)

        self.btnLoadScrivener = push_btn(IconRegistry.from_name('mdi6.application-import', color=RELAXED_WHITE_COLOR),
                                         text='Select a Scrivener project', properties=['positive', 'confirm'])
        self.btnLoadScrivener.clicked.connect(self._loadFromScrivener)
        self.pageScrivener.layout().addWidget(Subtitle(title='Import project from Scrivener',
                                                       description="Select your Scrivener project to import your binder's content into Plotlyst.",
                                                       icon='mdi6.application-import'))
        self.pageScrivener.layout().addWidget(self.btnLoadScrivener, alignment=Qt.AlignmentFlag.AlignRight)
        self.pageScrivener.layout().addWidget(vspacer())

        self.btnLoadDocx = push_btn(IconRegistry.from_name('mdi6.application-import', color=RELAXED_WHITE_COLOR),
                                    text='Select a docx file', properties=['positive', 'confirm'])
        self.btnLoadDocx.clicked.connect(self._loadFromDocx)

        self.chapterH1 = tool_btn(IconRegistry.from_name('mdi.format-header-1', color_on=PLOTLYST_MAIN_COLOR),
                                  transparent_=True, checkable=True)
        self.chapterH2 = tool_btn(IconRegistry.from_name('mdi.format-header-2', color_on=PLOTLYST_MAIN_COLOR),
                                  transparent_=True, checkable=True)
        self.chapterH3 = tool_btn(IconRegistry.from_name('mdi.format-header-3', color_on=PLOTLYST_MAIN_COLOR),
                                  transparent_=True, checkable=True)
        self.chapterH2.setChecked(True)
        self.buttonGroupDocxHeadings = QButtonGroup()
        self.buttonGroupDocxHeadings.addButton(self.chapterH1)
        self.buttonGroupDocxHeadings.addButton(self.chapterH2)
        self.buttonGroupDocxHeadings.addButton(self.chapterH3)
        for btn in self.buttonGroupDocxHeadings.buttons():
            btn.installEventFilter(OpacityEventFilter(btn, ignoreCheckedButton=True))

        self.btnInheritSceneTitle = Toggle()

        self.pageDocx.layout().addWidget(Subtitle(title="Import manuscript from docx",
                                                  description='Chapter titles are expected to be under the following heading',
                                                  icon='fa5.file-word'))
        self.pageDocx.layout().addWidget(group(self.chapterH1, self.chapterH2, self.chapterH3, margin=0),
                                         alignment=Qt.AlignmentFlag.AlignCenter)
        self.pageDocx.layout().addWidget(
            group(label('Scene titles will inherit chapter titles', description=True), self.btnInheritSceneTitle,
                  spacer(), margin_left=23))
        self.pageDocx.layout().addWidget(self.btnLoadDocx, alignment=Qt.AlignmentFlag.AlignRight)
        self.pageDocx.layout().addWidget(vspacer())

        self.frame.layout().addWidget(self.wdgBanner)
        self.frame.layout().addWidget(self.wdgCenter)
        self.wdgRight.layout().addWidget(group(self.btnCancel, self.btnFinish, self.btnNext, margin_top=20),
                                         alignment=Qt.AlignmentFlag.AlignRight)

        self.resize(700, 550)

    def display(self) -> Optional[Novel]:
        self._importedNovel = None

        self.lineTitle.setFocus()

        result = self.exec()

        if result == QDialog.DialogCode.Rejected:
            return None

        if self.stackedWidget.currentWidget() == self.pageNewStory:
            return self.__newNovel()
        elif self.stackedWidget.currentWidget() == self.pageWizard:
            return self._wizardNovel
        elif self._importedNovel is not None:
            return self._importedNovel

        return None

    def _pageChanged(self):
        if self.stackedWidget.currentWidget() == self.pageNewStory:
            self.lineTitle.setFocus()
            self.btnNext.setVisible(True)
            self.btnFinish.setVisible(False)
        elif self.stackedWidget.currentWidget() == self.pageScrivener:
            self.btnNext.setVisible(False)
            self.btnFinish.setVisible(False)
        elif self.stackedWidget.currentWidget() == self.pageDocx:
            self.btnNext.setVisible(False)
            self.btnFinish.setVisible(False)
        elif self.stackedWidget.currentWidget() == self.pageImportedPreview:
            self.btnNext.setVisible(False)
            self.btnFinish.setVisible(True)

    def _wizardToggled(self, toggled: bool):
        self.btnNext.setText('Start wizard' if toggled else 'Create')
        if toggled:
            icon = IconRegistry.from_name('ph.magic-wand', 'white', 'white')
        else:
            icon = IconRegistry.book_icon('white', 'white')
        self.btnNext.setIcon(icon)

    def _nextClicked(self):
        if self.stackedWidget.currentWidget() == self.pageNewStory and self.toggleWizard.isChecked():
            self._wizardNovel = self.__newNovel()
            self._wizard = NovelCustomizationWizard(self._wizardNovel)
            self._wizard.stack.currentChanged.connect(self._wizardPageChanged)
            self._wizard.finished.connect(self.accept)
            self.pageWizard.layout().addWidget(self._wizard)
            self.wdgBanner.setHidden(True)
            self.wdgTypesContainer.setHidden(True)
            self.btnNext.setVisible(True)
            self.btnNext.setText('Next')
            self.btnNext.setIcon(IconRegistry.from_name('fa5s.chevron-circle-right', RELAXED_WHITE_COLOR))
            self.btnFinish.setVisible(False)
            self.stackedWidget.setCurrentWidget(self.pageWizard)
        elif self.stackedWidget.currentWidget() == self.pageWizard:
            self._wizard.next()
        else:
            self.accept()

    def _wizardPageChanged(self):
        if not self._wizard.hasMore():
            self.btnNext.setVisible(False)
            self.btnFinish.setVisible(True)

    def _loadFromScrivener(self):
        if not ask_for_resource(ResourceType.PANDOC):
            return
        if app_env.is_dev():
            default_path = 'resources/scrivener/v3/'
        else:
            default_path = None
        if app_env.is_mac():
            project = QFileDialog.getOpenFileName(self, 'Choose a Scrivener project directory', default_path)
            if project:
                project = project[0]
        else:
            project = QFileDialog.getExistingDirectory(self, 'Choose a Scrivener project directory', default_path)
        if not project:
            return

        parser = ScrivenerParser()
        self._importedNovel = parser.parse_project(project)

        self._showImportedPreview()

    def _loadFromDocx(self):
        if not ask_for_resource(ResourceType.PANDOC):
            return

        docxpath = QFileDialog.getOpenFileName(self, 'Open a docx file')
        if not docxpath or not docxpath[0]:
            return

        if self.chapterH1.isChecked():
            heading = 1
        elif self.chapterH2.isChecked():
            heading = 2
        else:
            heading = 3
        self._importedNovel = import_docx(docxpath[0], chapter_heading_level=heading,
                                          infer_scene_titles=self.btnInheritSceneTitle.isChecked())

        self.wdgImportDetails.wdgScrivenerTop.setHidden(True)
        self._showImportedPreview()

    def _showImportedPreview(self):
        self.stackedWidget.setCurrentWidget(self.pageImportedPreview)
        self.wdgBanner.setHidden(True)
        self.wdgTypesContainer.setHidden(True)
        self.setMaximumWidth(MAXIMUM_SIZE)
        self.wdgImportDetails.setVisible(True)
        self.wdgImportDetails.setNovel(self._importedNovel)

    def __newNovel(self) -> Novel:
        return Novel.new_novel(self.lineTitle.text() if self.lineTitle.text() else 'My new novel')
