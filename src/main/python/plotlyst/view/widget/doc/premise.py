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
from PyQt6.QtWidgets import QWidget

from plotlyst.core.domain import Document
from plotlyst.view.generated.premise_builder_widget_ui import Ui_PremiseBuilderWidget
from plotlyst.view.icons import IconRegistry


class PremiseBuilderWidget(QWidget, Ui_PremiseBuilderWidget):
    def __init__(self, doc: Document, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._doc = doc

        self.btnSeed.setIcon(IconRegistry.from_name('fa5s.seedling'))
        self.btnConcept.setIcon(IconRegistry.from_name('fa5s.question-circle'))
        self.btnPremise.setIcon(IconRegistry.from_name('fa5s.scroll'))
