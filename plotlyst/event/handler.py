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
import logging
import traceback
from asyncio import Event
from typing import Optional, List

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QMessageBox, QWidget, QStatusBar, QApplication

from plotlyst.event.core import EventAuthorization, EventAuthorizationType, EventLog, Severity, \
    emit_warning, emit_critical
from plotlyst.view.common import ask_confirmation
from plotlyst.view.dialog.error import ErrorMessageBox


class EventAuthorizationHandler:
    parent: Optional[QWidget] = None

    @classmethod
    def handle(cls, event_auth: EventAuthorization) -> bool:
        if event_auth.type == EventAuthorizationType.REJECTED:
            emit_warning(event_auth.message, highlighted=True)
            return False
        if event_auth.type == EventAuthorizationType.ALLOWED:
            return True
        if event_auth.type == EventAuthorizationType.CONFIRMATION_REQUESTED:
            return ask_confirmation(event_auth.message, cls.parent)
        return False


class EventLogHandler:
    parent: Optional[QWidget] = None

    def __init__(self, statusbar: QStatusBar):
        self.statusbar = statusbar
        self._error_event = Event()

    def on_warning_event(self, event: EventLog, time: int) -> None:
        if not event.highlighted:
            self.statusbar.showMessage(event.message, time)
            self.statusbar.setStyleSheet('color: red')
        self._handle_highlighted_event(event, Severity.WARNING)

        QTimer.singleShot(time, self._reset_statusbar_color)

    def on_error_event(self, event: EventLog, time: int) -> None:
        if not self._error_event.is_set():
            if not event.highlighted:
                self.statusbar.showMessage(event.message, time)
                self.statusbar.setStyleSheet('color: red')
            self._handle_highlighted_event(event, Severity.ERROR)
            if event.details:
                logging.error(event.details)
            else:
                logging.error(event.message)
            self._error_event.set()

            QTimer.singleShot(50, self._error_event.clear)
            QTimer.singleShot(50, self._reset_statusbar_color)

    def on_info_event(self, event: EventLog, time: int) -> None:
        if not event.highlighted:
            self.statusbar.showMessage(event.message, time)
            self.statusbar.setStyleSheet('color: blue')
        self._handle_highlighted_event(event, Severity.INFO)

    def _handle_highlighted_event(self, event: EventLog, severity: Severity):
        if not event.highlighted:
            return
        QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
        if severity == Severity.INFO:
            QMessageBox.information(self.parent, 'Information', event.message)
        if severity == Severity.WARNING:
            ErrorMessageBox(msg=event.message, warning=True, parent=self.parent).display()
        if severity == Severity.ERROR:
            ErrorMessageBox(msg=event.message, details=event.details, parent=self.parent).display()

        QApplication.restoreOverrideCursor()

    def _reset_statusbar_color(self) -> None:
        self.statusbar.setStyleSheet('color: black')


def exception_handler(exception_type, exception_value: Exception, exception_traceback):
    msg = ''.join(exception_value.args)

    details: List[str] = traceback.format_exception(exception_type, exception_value, exception_traceback)
    emit_critical(msg, ''.join(details))
