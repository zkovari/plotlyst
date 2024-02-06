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
import threading
from typing import Optional

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QWidget, QDialog
from qttour import TourManager, TourSequence, TourStep

from plotlyst.event.core import emit_global_event
from plotlyst.service.persistence import RepositoryPersistenceManager
from plotlyst.view.widget.tour import Tutorial
from plotlyst.view.widget.tour.core import COLOR_ON_NAVBAR, tour_events, TourEvent, tour_teardowns, \
    TutorialNovelCloseTourEvent


class TourService(QObject):
    __instance = None
    __lock = threading.Lock()

    def __init__(self, parent=None):
        super(TourService, self).__init__(parent)
        self._manager = TourManager.instance()
        self._manager.setCoachColor(COLOR_ON_NAVBAR)
        self._manager.tourFinished.connect(self._tourFinished)
        self._tutorial: Optional[Tutorial] = None
        self._events_iter = None

    @classmethod
    def instance(cls):
        if not cls.__instance:
            with cls.__lock:
                if not cls.__instance:
                    cls.__instance = TourService()
        return cls.__instance

    def setTutorial(self, tutorial: Tutorial):
        self._tutorial = tutorial
        self._events_iter = None

    def start(self):
        self._manager.start()
        self._events_iter = iter(tour_events(self._tutorial, self))
        self._nextEvent()

    def addWidget(self, widget: QWidget, event: TourEvent):
        step = TourStep(widget, message=event.message, delegateClick=event.delegate_click, action=event.action)
        self._run(step)

    def addDialogWidget(self, dialog: QDialog, widget: QWidget, event: TourEvent):
        step = TourStep(widget, message=event.message, delegateClick=event.delegate_click, action=event.action,
                        dialog=dialog)
        self._run(step)

    def next(self):
        self._nextEvent()

    def _run(self, step: TourStep):
        sequence = TourSequence()
        step.finished.connect(self._nextEvent)
        sequence.steps().append(step)
        self._manager.run(sequence, finishTour=False)

    def _nextEvent(self):
        event = next(self._events_iter, None)
        if event is not None:
            emit_global_event(event)
        else:
            self._manager.finish()

    def _tourFinished(self):
        teardown = tour_teardowns.get(self._tutorial, TutorialNovelCloseTourEvent)
        if teardown:
            emit_global_event(teardown(self))

        RepositoryPersistenceManager.instance().set_persistence_enabled(True)
