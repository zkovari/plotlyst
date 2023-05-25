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
from typing import Optional

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QWidget
from qttour import TourManager, TourSequence, TourStep

from src.main.python.plotlyst.event.core import emit_event
from src.main.python.plotlyst.view.widget.tour import Tutorial
from src.main.python.plotlyst.view.widget.tour.core import LibraryTourEvent, COLOR_ON_NAVBAR


class TourService(QObject):
    def __init__(self, parent=None):
        super(TourService, self).__init__(parent)
        self._manager = TourManager.instance()
        self._manager.setCoachColor(COLOR_ON_NAVBAR)
        self._tutorial: Optional[Tutorial] = None

    def setTutorial(self, tutorial: Tutorial):
        self._tutorial = tutorial

    def start(self):
        self._manager.start()
        emit_event(LibraryTourEvent(self,
                                    message='Navigate first to your library panel. This is where you will find all your stories.'))

    def addWidget(self, widget: QWidget, message: str = ''):
        sequence = TourSequence()
        sequence.steps().append(TourStep(widget, message=message))
        self._manager.run(sequence)
