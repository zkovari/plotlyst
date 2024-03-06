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
import random
from enum import Enum
from functools import partial
from typing import Optional, Tuple, List

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QSize, QObject, QEvent, QPoint, QRect, pyqtSignal, QThreadPool
from PyQt6.QtGui import QColor, QPixmap, QIcon, QPainter, QImage
from PyQt6.QtNetwork import QNetworkAccessManager
from PyQt6.QtWidgets import QDialog, QToolButton, QPushButton, QApplication
from overrides import overrides
from qthandy import hbox, FlowLayout, bold, underline
from qthandy.filter import InstantTooltipEventFilter

from plotlyst.env import app_env
from plotlyst.service.resource import JsonDownloadWorker, JsonDownloadResult, ImageDownloadResult, \
    ImagesDownloadWorker
from plotlyst.view.common import rounded_pixmap, open_url, calculate_resized_dimensions
from plotlyst.view.generated.artbreeder_picker_dialog_ui import Ui_ArtbreederPickerDialog
from plotlyst.view.generated.image_crop_dialog_ui import Ui_ImageCropDialog
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.utility import IconSelectorWidget


class IconSelectorDialog(QDialog):

    def __init__(self, parent=None):
        super(IconSelectorDialog, self).__init__(parent)
        self.setWindowTitle('Select icon')

        self.resize(500, 500)
        hbox(self, 1, 0)

        self._icon = ''
        self._color: Optional[QColor] = None
        self.selector = IconSelectorWidget(self)
        self.selector.iconSelected.connect(self._icon_selected)

        self.layout().addWidget(self.selector)

    def display(self, color: Optional[QColor] = None) -> Optional[Tuple[str, QColor]]:
        if color:
            self.selector.setColor(color)
        result = self.exec()
        if result == QDialog.DialogCode.Accepted and self._icon:
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
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._size = 128
        self.setIconSize(QSize(self._size, self._size))
        self.setIcon(QIcon(pixmap.scaled(self._size, self._size, Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation)))


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
        self.btnVisit.clicked.connect(lambda: open_url('https://www.artbreeder.com/'))

        self._threadpool = QThreadPool(self)
        self._runnables: List[ImagesDownloadWorker] = []

    def display(self) -> Optional[QPixmap]:
        self._step = 0
        self.fetch()
        result = self.exec()
        if self._threadpool.activeThreadCount() > 1:
            for runnable in self._runnables:
                runnable.stop()
        self._threadpool.clear()
        if result == QDialog.DialogCode.Accepted:
            return self._pixmap

    def fetch(self):
        def _listFetched(jsonResult):
            self.urls = jsonResult
            random.shuffle(self.urls)
            self._loadImages()

        result = JsonDownloadResult()
        result.finished.connect(_listFetched)
        runner = JsonDownloadWorker(
            'https://raw.githubusercontent.com/plotlyst/artbreeder-scraper/main/resources/artbreeder/portraits.json',
            result)
        runner.setAutoDelete(True)
        self._threadpool.start(runner)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QToolButton):
            if event.type() == QEvent.Type.Enter:
                watched.setStyleSheet('border: 2px dashed darkBlue;')
            elif event.type() == QEvent.Type.Leave:
                watched.setStyleSheet('border: 1px solid black;')

        return super(ArtbreederDialog, self).eventFilter(watched, event)

    def _loadImages(self):
        def downloadImages(urls_list: List[str]):
            result = ImageDownloadResult()
            result.downloaded.connect(self._imageDownloaded)
            runner = ImagesDownloadWorker(urls_list, result)
            runner.setAutoDelete(True)
            self._runnables.append(runner)
            self._threadpool.start(runner)

        if self._step + self._step_size >= len(self.urls):
            return

        self._runnables.clear()

        urls = self.urls[self._step:self._step + self._step_size]
        half = len(urls) // 2
        downloadImages(urls[:half])
        downloadImages(urls[half:])

        self._step += self._step_size

    def _imageDownloaded(self, image: QImage):
        pixmap = QPixmap.fromImage(image)
        btn = _AvatarButton(pixmap)
        btn.clicked.connect(partial(self._selected, btn))
        btn.installEventFilter(self)
        self.wdgPictures.layout().addWidget(btn)

    def _selected(self, btn: _AvatarButton):
        self._pixmap = btn.pixmap
        self.accept()

    def _scrolled(self, value: int):
        if value == self.scrollArea.verticalScrollBar().maximum():
            if self._threadpool.activeThreadCount() == 0:
                self._loadImages()


class Corner(Enum):
    TopLeft = 0
    TopRight = 1
    BottomRight = 2
    BottomLeft = 3


class ImageCropDialog(QDialog, Ui_ImageCropDialog):
    def __init__(self, parent=None):
        super(ImageCropDialog, self).__init__(parent)
        self.setupUi(self)

        bold(self.lblPreviewTitle)
        underline(self.lblPreviewTitle)
        self.frame = self.CropFrame(self.lblImage)
        self.frame.cropped.connect(self._updatePreview)
        self.scaled = None
        self.cropped = None

    def display(self, pixmap: QPixmap) -> Optional[QPixmap]:
        w, h = calculate_resized_dimensions(pixmap.width(), pixmap.height(), max_size=512)

        self.frame.setFixedSize(min(w, h), min(w, h))
        self.scaled = pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
        self.lblImage.setPixmap(self.scaled)
        self._updatePreview()
        result = self.exec()
        QApplication.restoreOverrideCursor()
        if result == QDialog.DialogCode.Accepted:
            return self.cropped

    def _updatePreview(self):
        self.cropped = QPixmap(self.frame.width(), self.frame.height())

        painter = QPainter(self.cropped)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cropped_rect = self.scaled.rect()
        cropped_rect.setX(self.frame.pos().x())
        cropped_rect.setY(self.frame.pos().y())
        cropped_rect.setWidth(self.cropped.width())
        cropped_rect.setHeight(self.cropped.height())
        painter.drawPixmap(self.cropped.rect(), self.scaled, cropped_rect)
        painter.end()

        self.lblPreview.setPixmap(
            rounded_pixmap(self.cropped.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation)))

    class CropFrame(QPushButton):
        cropped = pyqtSignal()
        cornerRange: int = 15

        def __init__(self, parent):
            super().__init__(parent)
            self.setStyleSheet('QPushButton {border: 3px dashed red;}')
            self.setMouseTracking(True)
            self._pressedPoint: Optional[QPoint] = None
            self._resizeCorner: Optional[Corner] = None
            self._originalSize: QRect = self.geometry()

        @overrides
        def enterEvent(self, event: QEvent) -> None:
            if not QApplication.overrideCursor():
                QApplication.setOverrideCursor(Qt.CursorShape.SizeAllCursor)

        @overrides
        def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
            if self._pressedPoint:
                x_diff = event.pos().x() - self._pressedPoint.x()
                y_diff = event.pos().y() - self._pressedPoint.y()
                if self._resizeCorner == Corner.TopLeft:
                    self.setGeometry(self.geometry().x() + x_diff, self.geometry().y() + y_diff, self.width(),
                                     self.height())
                    self.setFixedSize(self.geometry().width() - x_diff, self.geometry().height() - y_diff)
                elif self._resizeCorner == Corner.TopRight:
                    self.setGeometry(self.geometry().x(), self.geometry().y() + y_diff, self.width(), self.height())
                    self.setFixedSize(self._originalSize.width() + x_diff, self.geometry().height() - y_diff)
                elif self._resizeCorner == Corner.BottomRight:
                    self.setFixedSize(self._originalSize.width() + x_diff, self._originalSize.height() + y_diff)
                elif self._resizeCorner == Corner.BottomLeft:
                    self.setGeometry(self.geometry().x() + x_diff, self.geometry().y(), self.width(), self.height())
                    self.setFixedSize(self.geometry().width() - x_diff, self._originalSize.height() + y_diff)
                else:
                    if self._xMovementAllowed(x_diff):
                        self.setGeometry(self.geometry().x() + x_diff, self.geometry().y(), self.width(), self.height())
                    if self._yMovementAllowed(y_diff):
                        self.setGeometry(self.geometry().x(), self.geometry().y() + y_diff, self.width(), self.height())

            else:
                self._resizeCorner = None
                if event.pos().x() < self.cornerRange and event.pos().y() < self.cornerRange:
                    self._resizeCorner = Corner.TopLeft
                    QApplication.changeOverrideCursor(Qt.CursorShape.SizeFDiagCursor)
                elif event.pos().x() > self.width() - self.cornerRange \
                        and event.pos().y() > self.height() - self.cornerRange:
                    self._resizeCorner = Corner.BottomRight
                    QApplication.changeOverrideCursor(Qt.CursorShape.SizeFDiagCursor)
                elif event.pos().x() > self.width() - self.cornerRange and event.pos().y() < self.cornerRange:
                    self._resizeCorner = Corner.TopRight
                    QApplication.changeOverrideCursor(Qt.CursorShape.SizeBDiagCursor)
                elif event.pos().x() < self.cornerRange and event.pos().y() > self.height() - self.cornerRange:
                    self._resizeCorner = Corner.BottomLeft
                    QApplication.changeOverrideCursor(Qt.CursorShape.SizeBDiagCursor)
                else:
                    QApplication.changeOverrideCursor(Qt.CursorShape.SizeAllCursor)

        def _xMovementAllowed(self, diff: int) -> bool:
            return 0 < self.geometry().x() + diff \
                and self.geometry().x() + diff + self.width() < self.parent().width()

        def _yMovementAllowed(self, diff: int) -> bool:
            return 0 < self.geometry().y() + diff \
                and self.geometry().y() + diff + self.height() < self.parent().height()

        @overrides
        def leaveEvent(self, event: QEvent) -> None:
            QApplication.restoreOverrideCursor()
            self._pressedPoint = None

        @overrides
        def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
            self._pressedPoint = event.pos()
            self._originalSize = self.geometry()

        @overrides
        def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
            self._pressedPoint = None
            self.cropped.emit()
