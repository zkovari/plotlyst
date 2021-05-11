from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PyQt5.QtCore import pyqtSignal, QObject


class Severity(Enum):
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'


class EventAuthorizationType(Enum):
    ALLOWED = 'ALLOWED'
    REJECTED = 'REJECTED'
    CONFIRMATION_REQUESTED = 'CONFIRMATION_REQUESTED'


@dataclass(eq=True, frozen=True)
class EventAuthorization:
    type: EventAuthorizationType
    message: str
    severity: Severity = Severity.INFO

    @classmethod
    def ok(cls, status_message: str = '') -> 'EventAuthorization':
        return EventAuthorization(type=EventAuthorizationType.ALLOWED, message=status_message)

    @classmethod
    def reject(cls, status_message: str) -> 'EventAuthorization':
        return EventAuthorization(type=EventAuthorizationType.REJECTED, message=status_message)

    @classmethod
    def ask_confirmation(cls, confirmation_message: str, severity: Severity = Severity.INFO) -> 'EventAuthorization':
        return EventAuthorization(type=EventAuthorizationType.CONFIRMATION_REQUESTED, message=confirmation_message,
                                  severity=severity)


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


def emit_info(message: str, highlighted: bool = False, time=1000):
    """Emit a message through EventLogReporter's info signal"""
    event_log_reporter.info.emit(EventLog(message=message, highlighted=highlighted), time)


def emit_warning(message: str, highlighted: bool = False, time=5000):
    """Emit a message through EventLogReporter's warning signal"""
    event_log_reporter.warning.emit(EventLog(message=message, highlighted=highlighted), time)


def emit_error(message: str, details: Optional[str] = None, highlighted: bool = False, time=5000):
    """Emit a message through EventLogReporter's error signal"""
    event_log_reporter.error.emit(EventLog(message=message, details=details, highlighted=highlighted), time)


def emit_critical(message: str, details: Optional[str] = None, time=5000):
    """Emit a highlighted message through EventLogReporter's error signal"""
    event_log_reporter.error.emit(EventLog(message=message, details=details, highlighted=True), time)
