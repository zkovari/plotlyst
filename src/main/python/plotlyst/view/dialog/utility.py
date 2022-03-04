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

import json
import logging
import random
from functools import partial
from typing import Optional

from PyQt5 import QtGui
from PyQt5.QtCore import QUrl, Qt, QSize, QObject, QEvent, QPoint
from PyQt5.QtGui import QColor, QPixmap, QIcon, QDesktopServices
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWidgets import QDialog, QToolButton, QPushButton, QApplication
from overrides import overrides
from qthandy import hbox, FlowLayout
from qthandy.filter import InstantTooltipEventFilter

from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.view.generated.artbreeder_picker_dialog_ui import Ui_ArtbreederPickerDialog
from src.main.python.plotlyst.view.generated.image_crop_dialog_ui import Ui_ImageCropDialog
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.utility import IconSelectorWidget


class IconSelectorDialog(QDialog):

    def __init__(self, parent=None):
        super(IconSelectorDialog, self).__init__(parent)
        self.setWindowTitle('Select icon')

        self.resize(500, 500)
        hbox(self, 1, 0)

        self._icon = ''
        self._color = None
        self.selector = IconSelectorWidget(self)
        self.selector.iconSelected.connect(self._icon_selected)

        self.layout().addWidget(self.selector)

    def display(self):
        result = self.exec()
        if result == QDialog.Accepted and self._icon:
            return self._icon, self._color

    @overrides
    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        self.selector.lstIcons.model().modelReset.emit()
        self.selector.lstIcons.update()

    def _icon_selected(self, icon_alias: str, color: QColor):
        self._icon = icon_alias
        self._color = color

        self.accept()


class _AvatarButton(QToolButton):
    def __init__(self, pixmap: QPixmap, parent=None):
        super(_AvatarButton, self).__init__(parent)
        self.pixmap = pixmap
        self.setCursor(Qt.PointingHandCursor)
        self._size = 128
        self.setIconSize(QSize(self._size, self._size))
        self.setIcon(QIcon(pixmap.scaled(self._size, self._size, Qt.KeepAspectRatio, Qt.SmoothTransformation)))


class ArtbreederDialog(QDialog, Ui_ArtbreederPickerDialog):

    def __init__(self, parent=None):
        super(ArtbreederDialog, self).__init__(parent)
        self.setupUi(self)
        self.wdgPictures.setLayout(FlowLayout(spacing=4))
        self.btnLicense.setIcon(IconRegistry.from_name('fa5b.creative-commons'))
        self.btnLicense.installEventFilter(InstantTooltipEventFilter(self.btnLicense))
        self._pixmap: Optional[QPixmap] = None
        self._step = 0
        self._step_size: int = 10 if app_env.test_env() else 50
        self.urls = []
        self.manager = QNetworkAccessManager()
        self.resize(740, 500)
        self.setMinimumSize(250, 250)
        self.scrollArea.verticalScrollBar().valueChanged.connect(self._scrolled)
        self.btnVisit.setIcon(IconRegistry.from_name('fa5s.external-link-alt', 'white'))
        self.btnVisit.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://www.artbreeder.com/')))

    def display(self) -> Optional[QPixmap]:
        self._step = 0
        self.fetch()
        result = self.exec()
        if result == QDialog.Accepted:
            return self._pixmap

    def fetch(self):
        urls_request = QNetworkRequest(QUrl(
            'https://raw.githubusercontent.com/plotlyst/artbreeder-scraper/main/resources/artbreeder/portraits.json'))

        self.manager.finished.connect(self._finished)
        self.manager.get(urls_request)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QToolButton):
            if event.type() == QEvent.Enter:
                watched.setStyleSheet('border: 2px dashed darkBlue;')
            elif event.type() == QEvent.Leave:
                watched.setStyleSheet('border: 1px solid black;')

        return super(ArtbreederDialog, self).eventFilter(watched, event)

    def _loadImages(self):
        if self._step + self._step_size >= len(self.urls):
            return
        for url in self.urls[self._step:self._step + self._step_size]:
            request = QNetworkRequest(QUrl(url))
            self.manager.get(request)
        self._step += self._step_size

    def _finished(self, reply: QNetworkReply):
        if reply.error():
            logging.error(reply.errorString())
        if reply.url().path().startswith('/plotlyst'):  # main json resource
            urls_json = reply.readAll()
            self.urls = json.loads(urls_json.data())
            random.shuffle(self.urls)
            self._loadImages()
        else:  # image
            jpegData = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(jpegData)

            btn = _AvatarButton(pixmap)
            btn.clicked.connect(partial(self._selected, btn))
            btn.installEventFilter(self)
            self.wdgPictures.layout().addWidget(btn)

    def _selected(self, btn: _AvatarButton):
        self._pixmap = btn.pixmap
        self.accept()

    def _scrolled(self, value: int):
        if value == self.scrollArea.verticalScrollBar().maximum():
            self._loadImages()


class ImageCropDialog(QDialog, Ui_ImageCropDialog):
    def __init__(self, parent=None):
        super(ImageCropDialog, self).__init__(parent)
        self.setupUi(self)

        self.frame = self.CropFrame(self.lblImage)

    def display(self, pixmap: QPixmap) -> Optional[QPixmap]:
        print(f'original size, w: {pixmap.width()}, h: {pixmap.height()}')
        ratio = pixmap.width() / pixmap.height()

        if max(pixmap.width(), pixmap.height()) > 512:
            if pixmap.width() > pixmap.height():
                w = 512
                h = 512 / ratio
            elif pixmap.width() < pixmap.height():
                h = 512
                w = 512 * ratio
            else:
                h = w = 512
        else:
            w = pixmap.width()
            h = pixmap.height()

        print(f'modified w: {w} h: {h}')
        self.frame.setFixedSize(min(w, h), min(w, h))
        self.lblImage.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        result = self.exec()
        QApplication.restoreOverrideCursor()
        if result == QDialog.Accepted:
            return pixmap

    class CropFrame(QPushButton):
        cornerRange: int = 15

        def __init__(self, parent):
            super().__init__(parent)
            self.setStyleSheet('QPushButton {border: 3px dashed red;}')
            self.setMouseTracking(True)
            self._pressedPoint: Optional[QPoint] = None
            self._resize: bool = False

        @overrides
        def enterEvent(self, event: QEvent) -> None:
            if not QApplication.overrideCursor():
                QApplication.setOverrideCursor(Qt.SizeAllCursor)

        @overrides
        def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
            if self._pressedPoint:
                x_diff = event.pos().x() - self._pressedPoint.x()
                y_diff = event.pos().y() - self._pressedPoint.y()
                # print(f' x diff {x_diff}, y diff {y_diff}')
                if self._resize:
                    self.setGeometry(self.geometry().x() + x_diff, self.geometry().y() + y_diff,
                                     self.width(),
                                     self.height())
                    self.setFixedSize(self.geometry().width() - x_diff, self.geometry().height() - y_diff)
                    # print(self.geometry())
                elif 0 < self.geometry().x() + x_diff \
                        and self.geometry().x() + x_diff + self.width() < self.parent().width() \
                        and 0 < self.geometry().y() + y_diff \
                        and self.geometry().y() + y_diff + self.height() < self.parent().height():
                    self.setGeometry(self.geometry().x() + x_diff, self.geometry().y() + y_diff, self.width(),
                                     self.height())

            else:
                if (event.pos().x() < self.cornerRange and event.pos().y() < self.cornerRange) or (
                        event.pos().x() > self.width() - self.cornerRange and event.pos().y() > self.height() - self.cornerRange):
                    self._resize = True
                    QApplication.changeOverrideCursor(Qt.SizeFDiagCursor)
                elif (event.pos().x() > self.width() - self.cornerRange and event.pos().y() < self.cornerRange) or (
                        event.pos().x() < self.cornerRange and event.pos().y() > self.height() - self.cornerRange):
                    self._resize = True
                    QApplication.changeOverrideCursor(Qt.SizeBDiagCursor)
                else:
                    self._resize = False
                    QApplication.changeOverrideCursor(Qt.SizeAllCursor)

        @overrides
        def leaveEvent(self, event: QEvent) -> None:
            QApplication.restoreOverrideCursor()
            self._pressedPoint = None

        @overrides
        def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
            self._pressedPoint = event.pos()
            # print(f'press {self._pressedPoint}')

        @overrides
        def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
            self._pressedPoint = None
