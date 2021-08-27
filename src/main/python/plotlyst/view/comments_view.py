"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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
from PyQt5.QtCore import QObject, QEvent
from PyQt5.QtWidgets import QFrame
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.generated.comment_widget_ui import Ui_CommentWidget
from src.main.python.plotlyst.view.generated.comments_view_ui import Ui_CommentsView
from src.main.python.plotlyst.view.icons import IconRegistry


class CommentsView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super(CommentsView, self).__init__(novel)
        self.ui = Ui_CommentsView()
        self.ui.setupUi(self.widget)
        self.ui.btnNewComment.setIcon(IconRegistry.from_name('mdi.comment-plus-outline', color='#726da8'))
        self.ui.btnNewComment.clicked.connect(self._new_comment)

    @overrides
    def refresh(self):
        pass

    def _new_comment(self):
        comment = CommentWidget()

        self.ui.wdgComments.layout().addWidget(comment)


class CommentWidget(QFrame, Ui_CommentWidget):
    def __init__(self, parent=None):
        super(CommentWidget, self).__init__(parent)
        self.setupUi(self)

        self.btnResolve.setHidden(True)
        self.btnImportant.setHidden(True)
        self.btnMenu.setIcon(IconRegistry.from_name('mdi.dots-horizontal'))
        self.btnMenu.setHidden(True)

        self.btnMenu.installEventFilter(self)

        self.setMinimumSize(200, 100)
        self.setMaximumSize(200, 100)

        self.setStyleSheet(f'''
        QFrame[mainFrame=true] {{
               border: 1px solid #3066be;
               border-radius: 15px;
               background-color: white;
           }}''')

    @overrides
    def enterEvent(self, event: QEvent) -> None:
        self.btnMenu.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        self.btnMenu.setHidden(True)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.HoverEnter:
            self.btnMenu.setIcon(IconRegistry.from_name('mdi.dots-horizontal', color='#541388', mdi_scale=1.4))
        elif event.type() == QEvent.HoverLeave:
            self.btnMenu.setIcon(IconRegistry.from_name('mdi.dots-horizontal'))
        return super(CommentWidget, self).eventFilter(watched, event)
