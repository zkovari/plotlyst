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
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QWidget
from qthandy import vbox, vspacer

from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode


# class TopLevelWidget(ContainerNode):
#     selectionChanged = pyqtSignal(bool)
#
#     def __init__(self, title: str, icon: QIcon, parent=None):
#         super(TopLevelWidget, self).__init__(parent)
#         vbox(self)
#         self._selected: bool = False
#
#         self._wdgTitle = QWidget(self)
#         hbox(self._wdgTitle, 0, 2)
#
#         self._lblTitle = QLabel(title)
#         self._icon = Icon(self._wdgTitle)
#         self._icon.setIcon(icon)
#
#         self._wdgTitle.layout().addWidget(self._icon)
#         self._wdgTitle.layout().addWidget(self._lblTitle)
#
#         self.layout().addWidget(self._wdgTitle)
#
#         self._wdgTitle.installEventFilter(self)
#
#     @overrides
#     def eventFilter(self, watched: QObject, event: QEvent) -> bool:
#         if event.type() == QEvent.Type.Enter:
#             qtanim.glow(self._wdgTitle, radius=4, duration=100, color=Qt.GlobalColor.lightGray)
#         elif event.type() == QEvent.Type.MouseButtonRelease:
#             self._toggleSelection(not self._selected)
#             self.selectionChanged.emit(self._selected)
#         return super(TopLevelWidget, self).eventFilter(watched, event)
#
#     def select(self):
#         self._toggleSelection(True)
#
#     def deselect(self):
#         self._toggleSelection(False)
#
#     def _toggleSelection(self, selected: bool):
#         self._selected = selected
#         bold(self._lblTitle, self._selected)
#         self._reStyle()
#
#     def _reStyle(self):
#         if self._selected:
#             self._wdgTitle.setStyleSheet('''
#                     QWidget {
#                         background-color: #D8D5D5;
#                     }
#                 ''')
#         else:
#             self._wdgTitle.setStyleSheet('')


class ShelvesTreeView(TreeView):
    def __init__(self, parent=None):
        super(ShelvesTreeView, self).__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._centralWidget = QWidget(self)
        self.setWidget(self._centralWidget)
        vbox(self._centralWidget, spacing=0)

        self._wdgNovels = ContainerNode('Novels', IconRegistry.book_icon())
        self._wdgShortStories = ContainerNode('Short stories', IconRegistry.from_name('ph.file-text'))
        self._wdgIdeas = ContainerNode('Ideas', IconRegistry.decision_icon())
        self._wdgNotes = ContainerNode('Notes', IconRegistry.document_edition_icon())

        self._centralWidget.layout().addWidget(self._wdgNovels)
        self._centralWidget.layout().addWidget(self._wdgShortStories)
        self._centralWidget.layout().addWidget(self._wdgIdeas)
        self._centralWidget.layout().addWidget(self._wdgNotes)
        self._centralWidget.layout().addWidget(vspacer())
