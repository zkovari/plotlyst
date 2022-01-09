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

from PyQt5.QtCore import Qt, QEvent, QObject
from PyQt5.QtWidgets import QWidget, QPushButton, QSizePolicy, QFrame
from overrides import overrides

from src.main.python.plotlyst.core.domain import StoryStructure, default_story_structures, Novel, StoryBeat
from src.main.python.plotlyst.view.common import set_opacity, OpacityEventFilter, transparent
from src.main.python.plotlyst.view.generated.beat_widget_ui import Ui_BeatWidget
from src.main.python.plotlyst.view.generated.story_structure_settings_ui import Ui_StoryStructureSettings
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import FlowLayout


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
    def __init__(self, beat: StoryBeat, parent=None):
        super(BeatWidget, self).__init__(parent)
        self.setupUi(self)
        self.beat = beat
        self.lblTitle.setText(self.beat.text)
        self.lblDescription.setText(f'Description of this beat {self.beat.text}')
        transparent(self.lblTitle)
        transparent(self.lblDescription)
        transparent(self.btnIcon)
        self.btnIcon.setAttribute(Qt.WA_TranslucentBackground)
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
        elif event.type() == QEvent.Leave:
            self.cbToggle.setHidden(True)
            self.setStyleSheet('.BeatWidget {background-color: white;}')

        return super(BeatWidget, self).eventFilter(watched, event)


class StoryStructureEditor(QWidget, Ui_StoryStructureSettings):
    def __init__(self, parent=None):
        super(StoryStructureEditor, self).__init__(parent)
        self.setupUi(self)
        self.wdgTemplates.setLayout(FlowLayout(2, 3))

        for structure in default_story_structures:
            self.wdgTemplates.layout().addWidget(_StoryStructureButton(structure))

        self.novel: Optional[Novel] = None

    def setNovel(self, novel: Novel):
        self.novel = novel
        self.wdgPreview.setNovel(self.novel)

        for i, beat in enumerate(self.novel.story_structure.beats):
            wdg = BeatWidget(beat, self)
            self.beats.layout().addWidget(wdg, i // 2, i % 2)
