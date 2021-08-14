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
import pickle
from typing import Optional

import qtawesome
from PyQt5.QtCore import Qt, QMimeData, QObject, QEvent, QByteArray
from PyQt5.QtGui import QDrag, QMouseEvent
from PyQt5.QtWidgets import QDialog, QToolButton
from overrides import overrides

from src.main.python.plotlyst.core.domain import age_field, gender_field, \
    enneagram_field, TemplateField, TemplateFieldType, ProfileTemplate
from src.main.python.plotlyst.view.generated.character_profile_editor_dialog_ui import Ui_CharacterProfileEditorDialog
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.template import ProfileTemplateEditor


class CharacterProfileEditorDialog(Ui_CharacterProfileEditorDialog, QDialog):
    MimeType: str = 'application/template-field'

    def __init__(self, profile: ProfileTemplate, parent=None):
        super().__init__(parent)

        self.setupUi(self)
        self.wdgFieldProperties.setVisible(False)
        self.profile = profile

        self.btnAge.setIcon(qtawesome.icon('mdi.numeric', options=[{'scale_factor': 1.4}]))
        self.btnGender.setIcon(qtawesome.icon('mdi.gender-female', color='#fface4', options=[{'scale_factor': 1.4}]))
        self.btnFear.setIcon(qtawesome.icon('mdi.spider-thread', options=[{'scale_factor': 1.2}]))
        self.btnGoal.setIcon(IconRegistry.goal_icon())
        self.btnEnneagram.setIcon(qtawesome.icon('mdi.numeric-9-box-outline', options=[{'scale_factor': 1.2}]))
        self.btnMbti.setIcon(qtawesome.icon('fa.group'))
        self.btnDesire.setIcon(qtawesome.icon('fa5s.coins', color='#e1bc29'))
        self.btnMisbelief.setIcon(IconRegistry.error_icon())
        self.profile_editor = ProfileTemplateEditor(self.profile)
        self.wdgEditor.layout().addWidget(self.profile_editor)

        for w in self.profile_editor.widgets:
            self._field_added(w.field)

        self._selected_field: Optional[TemplateField] = None

        self.lineName.setText(self.profile.title)

        self.profile_editor.fieldAdded.connect(self._field_added)
        self.profile_editor.fieldSelected.connect(self._field_selected)
        self.btnRemove.setIcon(IconRegistry.minus_icon())
        self.btnRemove.clicked.connect(self._remove_field)

        self.btnAge.installEventFilter(self)
        self.btnGender.installEventFilter(self)
        self.btnFear.installEventFilter(self)
        self.btnGoal.installEventFilter(self)
        self.btnEnneagram.installEventFilter(self)
        self.btnMbti.installEventFilter(self)
        self.btnDesire.installEventFilter(self)
        self.btnMisbelief.installEventFilter(self)

        self._dragged: Optional[QToolButton] = None

        self.btnCancel.clicked.connect(self.reject)
        self.btnSave.clicked.connect(self.accept)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        self._dragged = watched
        if event.type() == QEvent.MouseButtonPress:
            self.mousePressEvent(event)
        elif event.type() == QEvent.MouseMove:
            self.mouseMoveEvent(event)
        elif event.type() == QEvent.MouseButtonRelease:
            self.mouseReleaseEvent(event)
        return super().eventFilter(watched, event)

    @overrides
    def mousePressEvent(self, event: QMouseEvent):
        self._dragged = None

    @overrides
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton and self._dragged and self._dragged.isEnabled():
            drag = QDrag(self._dragged)
            pix = self._dragged.grab()
            if self._dragged is self.btnAge:
                field = age_field
            elif self._dragged is self.btnGender:
                field = gender_field
            elif self._dragged is self.btnEnneagram:
                field = enneagram_field
            else:
                field = TemplateField(name=self._dragged.text(), type=TemplateFieldType.TEXT)
            mimedata = QMimeData()
            mimedata.setData(self.MimeType, QByteArray(pickle.dumps(field)))
            drag.setMimeData(mimedata)
            drag.setPixmap(pix)
            drag.setHotSpot(event.pos())
            drag.destroyed.connect(self._dragDestroyed)
            drag.exec_()

    def display(self) -> Optional[ProfileTemplate]:
        result = self.exec()

        if result == QDialog.Rejected:
            return None

        return self.profile_editor.profile()

    def _dragDestroyed(self):
        self._dragged = None

    def _field_added(self, field: TemplateField):
        self._enable_in_inventory(field, False)

    def _enable_in_inventory(self, field: TemplateField, enabled: bool):
        if field.id == age_field.id:
            self.btnAge.setEnabled(enabled)
        if field.id == gender_field.id:
            self.btnGender.setEnabled(enabled)
        if field.id == enneagram_field.id:
            self.btnEnneagram.setEnabled(enabled)

    def _field_selected(self, field: TemplateField):
        self._selected_field = field
        self.btnRemove.setEnabled(True)

    def _remove_field(self):
        self._enable_in_inventory(self._selected_field, True)
        self.profile_editor.removeSelected()
        self._selected_field = None
        self.btnRemove.setDisabled(True)
