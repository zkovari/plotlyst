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
from typing import Optional

from PyQt5.QtCore import QObject, QEvent, QPoint, pyqtSignal, Qt
from PyQt5.QtWidgets import QFrame, QMenu
from overrides import overrides

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel, Comment, Scene
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

        for scene in self.novel.scenes:
            for comment in scene.comments:
                self._addComment(comment, scene)

    @overrides
    def refresh(self):
        pass

    def _new_comment(self):
        self._addComment(Comment(''))

    def _addComment(self, comment: Comment, scene: Optional[Scene] = None):
        comment_wdg = CommentWidget(comment, scene)
        self.ui.wdgComments.layout().addWidget(comment_wdg)
        comment_wdg.removed.connect(self._comment_removed)

    def _comment_removed(self, comment_wdg: 'CommentWidget'):
        self.ui.wdgComments.layout().removeWidget(comment_wdg)
        if comment_wdg.scene:
            comment_wdg.scene.comments.remove(comment_wdg.comment)
            client.update_scene(comment_wdg.scene)
        comment_wdg.deleteLater()


class CommentWidget(QFrame, Ui_CommentWidget):
    removed = pyqtSignal(object)

    def __init__(self, comment: Comment, scene: Optional[Scene] = None, parent=None):
        super(CommentWidget, self).__init__(parent)
        self.setupUi(self)
        self.comment = comment
        self.scene: Optional[Scene] = scene

        self.setMinimumSize(200, 100)
        self.setMaximumSize(200, 100)

        self.btnResolve.setHidden(True)
        self.btnImportant.setHidden(True)
        self.btnMenu.setIcon(IconRegistry.from_name('mdi.dots-horizontal'))
        menu = _CommentsMenu(self.btnMenu)
        menu.addAction(IconRegistry.edit_icon(), '', self._edit)
        menu.addSeparator()
        menu.addAction(IconRegistry.trash_can_icon(), '', self._remove)
        self.btnMenu.setMenu(menu)
        self.btnMenu.setHidden(True)

        self.btnMenu.installEventFilter(self)

        self.textComment.setText(self.comment.text)
        self.textComment.setCursor(Qt.ArrowCursor)

        self.setStyleSheet('''
        QFrame[mainFrame=true] {
               border: 1px solid #3066be;
               border-radius: 15px;
               background-color: white;
           }''')

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

    def _edit(self):
        pass

    def _remove(self):
        self.removed.emit(self)


class _CommentsMenu(QMenu):

    def __init__(self, parent):
        super(_CommentsMenu, self).__init__(parent)
        self.setMaximumWidth(30)

    @overrides
    def event(self, event):
        if event.type() == QEvent.Show:
            # assure that the popup menu is always displayed above the toolbutton
            self.move(
                self.parent().mapToGlobal(QPoint(0, 0)) - QPoint(self.width() - self.parent().width() + 5, 0)
            )
        return super().event(event)
