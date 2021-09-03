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
import json
import logging
import random

from PyQt5 import QtGui
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel
from overrides import overrides

from src.main.python.plotlyst.view.generated.artbreeder_picker_dialog_ui import Ui_ArtbreederPickerDialog
from src.main.python.plotlyst.view.layout import FlowLayout
from src.main.python.plotlyst.view.widget.utility import IconSelectorWidget


class IconSelectorDialog(QDialog):

    def __init__(self, parent=None):
        super(IconSelectorDialog, self).__init__(parent)

        self.resize(300, 300)
        self.setLayout(QHBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(1, 1, 1, 1)

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


class ArtbreederDialog(QDialog, Ui_ArtbreederPickerDialog):
    PortraitsUrl: str = 'https://raw.githubusercontent.com/zkovari/plotlyst/automated/artbreeder/resources/artbreeder/portraits.json'

    def __init__(self, parent=None):
        super(ArtbreederDialog, self).__init__(parent)
        self.setupUi(self)
        self.wdgPictures.setLayout(FlowLayout())
        self.urls = []
        self.manager = QNetworkAccessManager()
        self.resize(500, 500)

    def display(self):
        urls = ['https://artbreeder.b-cdn.net/imgs/928eb51a042331a7bb0a7cecd445_small.jpeg',
                'https://artbreeder.b-cdn.net/imgs/98acca7d98f34476c67836b0c1e9_small.jpeg',
                'https://artbreeder.b-cdn.net/imgs/c4b3a0b4a26e13adaaadc6c4f30c_small.jpeg',
                'https://artbreeder.b-cdn.net/imgs/284d85d2908bc1fa77d1f2ba9d81_small.jpeg',
                'https://artbreeder.b-cdn.net/imgs/4f0b0dd5fcb40efaadf73e75d797_small.jpeg',
                'https://artbreeder.b-cdn.net/imgs/095288bb59ae0ccd01936ce87d82_small.jpeg',
                'https://artbreeder.b-cdn.net/imgs/8f4897226ca3b78ff319c61c6cb5_small.jpeg',
                'https://artbreeder.b-cdn.net/imgs/3555793c93083342b30a4c54592b_small.jpeg']

        urls_request = QNetworkRequest(QUrl(
            self.PortraitsUrl))
        print(len(urls))
        random.shuffle(urls)

        self.manager.finished.connect(self._finished)
        self.manager.get(urls_request)
        # for url in urls[0:100]:
        #     request = QNetworkRequest(QUrl(url))
        #     manager.get(request)

        self.exec()

    def _loadImages(self):
        random.shuffle(self.urls)
        for url in self.urls[0:100]:
            request = QNetworkRequest(QUrl(url))
            self.manager.get(request)

    def _finished(self, reply: QNetworkReply):
        if reply.error():
            logging.error(reply.errorString())
        if reply.url().path().startswith('/zkovari'):
            urls_json = reply.readAll()
            self.urls = json.loads(urls_json.data())
            self._loadImages()
        else:
            jpegData = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(jpegData)

            # print(f'{self.scrollArea.verticalScrollBar().value()} - {self.scrollArea.verticalScrollBar().maximum()}')

            label = QLabel()
            label.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.wdgPictures.layout().addWidget(label)
