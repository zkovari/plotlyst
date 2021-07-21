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
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PyQt5.QtCore import pyqtSignal, QObject


class Severity(Enum):
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'


@dataclass(eq=True, frozen=True)
class EventLog:
    message: str
    highlighted: bool = False
    details: Optional[str] = None


class EventLogReporter(QObject):
    info = pyqtSignal(EventLog, int)
    warning = pyqtSignal(EventLog, int)
    error = pyqtSignal(EventLog, int)


event_log_reporter = EventLogReporter()


def emit_critical(message: str, details: Optional[str] = None, time=5000):
    """Emit a highlighted message through EventLogReporter's error signal"""
    event_log_reporter.error.emit(EventLog(message=message, details=details, highlighted=True), time)
