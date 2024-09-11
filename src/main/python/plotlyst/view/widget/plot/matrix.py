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
from typing import Dict, Optional

import qtanim
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QShowEvent
from PyQt6.QtWidgets import QWidget, QTextEdit, QGridLayout, QStackedWidget
from overrides import overrides
from qthandy import vbox, clear_layout, vspacer, spacer, sp, grid, line, vline
from qthandy.filter import VisibilityToggleEventFilter, OpacityEventFilter
from qtmenu import MenuWidget, ActionTooltipDisplayMode

from plotlyst.core.domain import Novel, Plot, PlotType, StorylineLink, StorylineLinkType
from plotlyst.service.persistence import RepositoryPersistenceManager
from plotlyst.view.common import action, label, tool_btn, push_btn
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.display import Icon, IdleWidget


class StorylineHeaderWidget(QWidget):
    def __init__(self, storyline: Plot, parent=None):
        super().__init__(parent)
        self._storyline = storyline

        vbox(self, 5)
        self._icon = Icon()
        self._lbl = label(storyline.text, wordWrap=True)
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setMaximumWidth(220)

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        self._lbl.setText(self._storyline.text)
        self._icon.setIcon(IconRegistry.from_name(self._storyline.icon, self._storyline.icon_color))


class StorylinesConnectionWidget(QWidget):
    linked = pyqtSignal()
    linkChanged = pyqtSignal()
    unlinked = pyqtSignal()

    def __init__(self, source: Plot, target: Plot, parent=None):
        super().__init__(parent)
        self._source = source
        self._target = target
        self._link: Optional[StorylineLink] = None

        self.stack = QStackedWidget()
        self._wdgActive = QWidget()
        self._wdgDefault = QWidget()
        self.stack.addWidget(self._wdgActive)
        self.stack.addWidget(self._wdgDefault)

        self._btnLink = tool_btn(IconRegistry.from_name('fa5s.link'), transparent_=True)
        self._btnLink.setIconSize(QSize(32, 32))
        self._btnLink.installEventFilter(OpacityEventFilter(self._btnLink))
        self._btnLink.clicked.connect(self._linkClicked)
        self._btnLink.setHidden(True)
        vbox(self._wdgDefault)
        self._wdgDefault.layout().addWidget(self._btnLink, alignment=Qt.AlignmentFlag.AlignCenter)
        self._wdgDefault.installEventFilter(VisibilityToggleEventFilter(self._btnLink, self._wdgDefault))

        self._icon = push_btn(text='Connection', properties=['transparent'])
        self._text = QTextEdit()
        self._text.setProperty('rounded', True)
        self._text.setProperty('white-bg', True)
        self._text.setMinimumSize(175, 100)
        self._text.setMaximumSize(190, 120)
        self._text.verticalScrollBar().setVisible(False)
        self._text.textChanged.connect(self._textChanged)
        vbox(self._wdgActive)
        self._wdgActive.layout().addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignCenter)
        self._wdgActive.layout().addWidget(self._text, alignment=Qt.AlignmentFlag.AlignCenter)

        self._plotTypes = (PlotType.Main, PlotType.Subplot)

        self._menu = MenuWidget(self._icon)
        self._menu.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
        self._menu.addSection('Connection type')
        self._menu.addSeparator()
        self._addAction(StorylineLinkType.Catalyst)
        self._addAction(StorylineLinkType.Impact)
        self._addAction(StorylineLinkType.Contrast)

        if self._source.plot_type in self._plotTypes:
            if self._target.plot_type in self._plotTypes:
                self._addAction(StorylineLinkType.Compete)

        elif self._source.plot_type == PlotType.Internal:
            if self._target.plot_type in self._plotTypes:
                self._addAction(StorylineLinkType.Resolve)
            elif self._target.plot_type == PlotType.Relation:
                self._addAction(StorylineLinkType.Reveal)
        elif self._source.plot_type == PlotType.Relation:
            if self._target.plot_type == PlotType.Internal:
                self._addAction(StorylineLinkType.Reflect_character)
            elif self._target.plot_type != PlotType.Relation:
                self._addAction(StorylineLinkType.Reflect_plot)

        self._menu.addSeparator()
        self._menu.addAction(
            action('Remove', IconRegistry.trash_can_icon(), tooltip='Remove connection', slot=self._remove))

        self.stack.setCurrentWidget(self._wdgDefault)

        vbox(self, 0, 0)
        self.layout().addWidget(self.stack)

        sp(self).h_max().v_max()

    def activate(self):
        self._text.setFocus()

    def setLink(self, link: StorylineLink):
        self._link = None
        self._text.setText(link.text)
        self._link = link
        self._updateType()
        self.stack.setCurrentWidget(self._wdgActive)

    def _linkClicked(self):
        link = StorylineLink(self._source.id, self._target.id, StorylineLinkType.Connection)
        self._source.links.append(link)

        self.setLink(link)
        qtanim.fade_in(self._wdgActive, teardown=self.activate)

    def _typeChanged(self, type: StorylineLinkType):
        self._link.type = type
        self._updateType()
        self.linkChanged.emit()

    def _textChanged(self):
        if self._link:
            self._link.text = self._text.toPlainText()
            self.linkChanged.emit()

    def _updateType(self):
        self._icon.setIcon(IconRegistry.from_name(self._link.type.icon()))
        self._icon.setText(self._link.type.display_name())
        self._icon.setToolTip(self._link.type.desc())
        self._text.setPlaceholderText(self._link.type.desc())

    def _remove(self):
        self._source.links.remove(self._link)
        self._link = None
        self._text.clear()
        self.stack.setCurrentWidget(self._wdgDefault)
        self.unlinked.emit()

    def _addAction(self, type: StorylineLinkType):
        self._menu.addAction(action(type.name.replace('_', ' '), IconRegistry.from_name(type.icon())
                                    , tooltip=type.desc(), slot=partial(self._typeChanged, type)))


class StorylinesImpactMatrix(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._refreshOnShown = True

        self._grid: QGridLayout = grid(self)
        self.repo = RepositoryPersistenceManager.instance()

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        if self._refreshOnShown:
            self._refreshMatrix()
            self._refreshOnShown = False

    def refresh(self):
        if self.isVisible():
            self._refreshMatrix()
        else:
            self._refreshOnShown = True

    def _refreshMatrix(self):
        clear_layout(self)

        for i, storyline in enumerate(self._novel.plots):
            refs: Dict[str, StorylineLink] = {}
            for ref in storyline.links:
                refs[str(ref.target_id)] = ref

            header = StorylineHeaderWidget(storyline)
            self._grid.addWidget(header, 0, i + 1, alignment=Qt.AlignmentFlag.AlignCenter)

            row = StorylineHeaderWidget(storyline)
            row.setMinimumHeight(70)
            self._grid.addWidget(row, i + 1, 0, alignment=Qt.AlignmentFlag.AlignVCenter)

            self._grid.addWidget(self._emptyCellWidget(), i + 1, i + 1)

            for j, ref_storyline in enumerate(self._novel.plots):
                if storyline is ref_storyline:
                    continue
                wdg = StorylinesConnectionWidget(storyline, ref_storyline)
                wdg.linked.connect(self._save)
                wdg.linkChanged.connect(self._save)
                wdg.unlinked.connect(self._save)
                if str(ref_storyline.id) in refs.keys():
                    wdg.setLink(refs[str(ref_storyline.id)])
                self._grid.addWidget(wdg, i + 1, j + 1)

        self._grid.addWidget(line(), 0, 1, 1, len(self._novel.plots), alignment=Qt.AlignmentFlag.AlignBottom)
        self._grid.addWidget(vline(), 1, 0, len(self._novel.plots), 1, alignment=Qt.AlignmentFlag.AlignRight)
        self._grid.addWidget(spacer(), 0, len(self._novel.plots) + 1)

        self._grid.addWidget(vspacer(), len(self._novel.plots) + 1, 0)

    def _emptyCellWidget(self) -> QWidget:
        wdg = IdleWidget()
        wdg.setMinimumSize(50, 50)

        return wdg

    def _save(self):
        self.repo.update_novel(self._novel)
