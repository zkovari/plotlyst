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
from functools import partial
from typing import Optional

from PyQt5.QtCore import Qt, QEvent, QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QPushButton, QSizePolicy, QFrame, QButtonGroup
from overrides import overrides

from src.main.python.plotlyst.core.domain import StoryStructure, default_story_structures, Novel, StoryBeat
from src.main.python.plotlyst.view.common import set_opacity, OpacityEventFilter, transparent, spacer_widget
from src.main.python.plotlyst.view.generated.beat_widget_ui import Ui_BeatWidget
from src.main.python.plotlyst.view.generated.story_structure_settings_ui import Ui_StoryStructureSettings
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import FlowLayout, clear_layout
from src.main.python.plotlyst.view.widget.scenes import SceneStoryStructureWidget


class _StoryStructureButton(QPushButton):
    def __init__(self, structure: StoryStructure, parent=None):
        super(_StoryStructureButton, self).__init__(parent)
        self._structure = structure
        self.setText(structure.title)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
        if self._structure.icon:
            self.setIcon(IconRegistry.from_name(self._structure.icon, self._structure.icon_color))

        self.setStyleSheet('''
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 0,
                                      stop: 0 #f8edeb);
                border: 2px solid #fec89a;
                border-radius: 6px;
                padding: 2px;
            }
            QPushButton:checked {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 0,
                                      stop: 0 #ffd7ba);
                border: 3px solid #FD9235;
                padding: 1px;
            }
            ''')
        self._toggled(self.isChecked())
        self.installEventFilter(OpacityEventFilter(0.7, 0.5, self, ignoreCheckedButton=True))
        self.toggled.connect(self._toggled)

    def structure(self) -> StoryStructure:
        return self._structure

    def _toggled(self, toggled: bool):
        set_opacity(self, 1.0 if toggled else 0.5)
        font = self.font()
        font.setBold(toggled)
        self.setFont(font)


class BeatWidget(QFrame, Ui_BeatWidget):
    beatHighlighted = pyqtSignal(StoryBeat)

    def __init__(self, beat: StoryBeat, parent=None):
        super(BeatWidget, self).__init__(parent)
        self.setupUi(self)
        self.beat = beat
        self.lblTitle.setText(self.beat.text)
        self.lblDescription.setText(f'Description of this beat {self.beat.text}')
        transparent(self.lblTitle)
        transparent(self.lblDescription)
        transparent(self.btnIcon)
        if beat.icon:
            self.btnIcon.setIcon(IconRegistry.from_name(beat.icon, beat.icon_color))
        self.lblTitle.setStyleSheet(f'color: {beat.icon_color};')

        self.cbToggle.setHidden(True)
        self.installEventFilter(self)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Enter:
            self.cbToggle.setVisible(True)
            self.setStyleSheet('.BeatWidget {background-color: #DBF5FA;}')
            self.beatHighlighted.emit(self.beat)
        elif event.type() == QEvent.Leave:
            self.cbToggle.setHidden(True)
            self.setStyleSheet('.BeatWidget {background-color: white;}')

        return super(BeatWidget, self).eventFilter(watched, event)


class StoryStructureEditor(QWidget, Ui_StoryStructureSettings):
    def __init__(self, parent=None):
        super(StoryStructureEditor, self).__init__(parent)
        self.setupUi(self)
        self.wdgTemplates.setLayout(FlowLayout(2, 3))

        self._btnGroupStructure = QButtonGroup()
        self._btnGroupStructure.setExclusive(True)

        self.novel: Optional[Novel] = None
        self.beats.installEventFilter(self)

    def setNovel(self, novel: Novel):
        self.novel = novel
        for structure in default_story_structures:
            btn = _StoryStructureButton(structure)
            btn.toggled.connect(partial(self._structureToggled, structure))
            self._btnGroupStructure.addButton(btn)
            self.wdgTemplates.layout().addWidget(btn)

            if structure == self.novel.story_structure:
                btn.setChecked(True)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Leave:
            self.wdgPreview.unhighlightBeats()

        return super(StoryStructureEditor, self).eventFilter(watched, event)

    def _structureToggled(self, structure: StoryStructure, toggled: bool):
        if not toggled:
            return
        clear_layout(self.beats.layout())
        self.novel.story_structure = structure

        if self.wdgPreview.novel is not None:
            item = self.layout().takeAt(1)
            item.widget().deleteLater()
            self.wdgPreview = SceneStoryStructureWidget(self)
            self.layout().insertWidget(1, self.wdgPreview)
        self.wdgPreview.setNovel(self.novel, checkOccupiedBeats=False)
        row = 0
        col = 0
        for beat in structure.beats:
            wdg = BeatWidget(beat)
            if beat.act - 1 > col:  # new act
                self.beats.layout().addWidget(spacer_widget(vertical=True), row + 1, col)
                col = beat.act - 1
                row = 0
            self.beats.layout().addWidget(wdg, row, col)
            row += 1
            wdg.beatHighlighted.connect(self.wdgPreview.highlightBeat)
