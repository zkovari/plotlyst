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

import qtanim
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QWidget, QSlider, QHeaderView, QFrame
from overrides import overrides
from qthandy import hbox, gc
from qthandy.filter import OpacityEventFilter, DisabledClickEventFilter, InstantTooltipEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.core.domain import Conflict, ConflictReference, Novel, Scene, ConflictType, \
    SceneStructureAgenda
from src.main.python.plotlyst.event.core import emit_critical
from src.main.python.plotlyst.model.scenes_model import SceneConflictsModel
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import tool_btn
from src.main.python.plotlyst.view.generated.character_conflict_widget_ui import Ui_CharacterConflictWidget
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.widget.labels import ConflictLabel


class ConflictIntensityEditor(QWidget):
    intensityChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        hbox(self, 0)
        self._slider = QSlider()
        self._slider.setOrientation(Qt.Orientation.Horizontal)
        self._slider.setMinimum(0)
        self._slider.setMaximum(10)
        self._slider.setPageStep(1)
        self._slider.setValue(1)
        self._slider.setMinimumWidth(100)
        self._slider.setMaximumWidth(200)
        self._slider.valueChanged.connect(self._valueChanged)
        self._slider.setProperty('conflict', True)

        self._iconColor = '#f3a712'
        self._icon = tool_btn(IconRegistry.from_name('mdi.battery-charging-10', self._iconColor), transparent_=True)

        self.layout().addWidget(self._icon)
        self.layout().addWidget(self._slider)

    def value(self) -> int:
        return self._slider.value()

    def setValue(self, value: int) -> None:
        if value == 0:
            value = 1
        self._slider.setValue(value)

    def _valueChanged(self, value: int):
        if value == 0:
            self.setValue(1)
            return
        iconName = f'mdi.battery-charging-{value * 10}'
        self._icon.setIcon(IconRegistry.from_name(iconName, self._iconColor))
        self.intensityChanged.emit(value)


class CharacterConflictWidget(QFrame, Ui_CharacterConflictWidget):
    conflictSelectionChanged = pyqtSignal()

    def __init__(self, novel: Novel, scene: Scene, agenda: SceneStructureAgenda, parent=None):
        super(CharacterConflictWidget, self).__init__(parent)
        self.novel = novel
        self.scene = scene
        self.agenda = agenda
        self.setupUi(self)

        self.repo = RepositoryPersistenceManager.instance()

        self.btnCharacter.setIcon(IconRegistry.conflict_character_icon())
        self.btnCharacter.setToolTip('<b style="color:#c1666b">Character</b>')
        self.btnCharacter.installEventFilter(InstantTooltipEventFilter(parent=self.btnCharacter))
        self.btnSociety.setIcon(IconRegistry.conflict_society_icon())
        self.btnSociety.setToolTip('<b style="color:#69306d">Society</b>')
        self.btnSociety.installEventFilter(InstantTooltipEventFilter(parent=self.btnSociety))
        self.btnNature.setIcon(IconRegistry.conflict_nature_icon())
        self.btnNature.setToolTip('<b style="color:#157a6e">Nature</b>')
        self.btnNature.installEventFilter(InstantTooltipEventFilter(parent=self.btnNature))
        self.btnTechnology.setIcon(IconRegistry.conflict_technology_icon())
        self.btnTechnology.setToolTip('<b style="color:#4a5859">Technology</b>')
        self.btnTechnology.installEventFilter(InstantTooltipEventFilter(parent=self.btnTechnology))
        self.btnSupernatural.setIcon(IconRegistry.conflict_supernatural_icon())
        self.btnSupernatural.setToolTip('<b style="color:#ac7b84">Supernatural</b>')
        self.btnSupernatural.installEventFilter(InstantTooltipEventFilter(parent=self.btnSupernatural))
        self.btnSelf.setIcon(IconRegistry.conflict_self_icon())
        self.btnSelf.setToolTip('<b style="color:#94b0da">Self</b>')
        self.btnSelf.installEventFilter(InstantTooltipEventFilter(parent=self.btnSelf))

        self._model = SceneConflictsModel(self.novel, self.scene, self.agenda)
        self._model.setCheckable(True, SceneConflictsModel.ColName)
        self._model.selection_changed.connect(self._previousConflictSelected)
        self.tblConflicts.setModel(self._model)
        self.tblConflicts.horizontalHeader().hideSection(SceneConflictsModel.ColBgColor)
        self.tblConflicts.horizontalHeader().setSectionResizeMode(SceneConflictsModel.ColIcon,
                                                                  QHeaderView.ResizeMode.ResizeToContents)
        self.tblConflicts.horizontalHeader().setSectionResizeMode(SceneConflictsModel.ColName,
                                                                  QHeaderView.ResizeMode.Stretch)
        self._update_characters()
        self.btnAddNew.setIcon(IconRegistry.ok_icon())
        self.btnAddNew.installEventFilter(DisabledClickEventFilter(self, lambda: qtanim.shake(self.lineKey)))
        self.btnAddNew.setDisabled(True)

        self.lineKey.textChanged.connect(self._keyphrase_edited)

        self.btnGroupConflicts.buttonToggled.connect(self._type_toggled)
        self._type = ConflictType.CHARACTER
        self.btnCharacter.setChecked(True)

        self.btnAddNew.clicked.connect(self._add_new)

    def refresh(self):
        self.cbCharacter.clear()
        self._update_characters()
        self.tblConflicts.model().update()
        self.tblConflicts.model().modelReset.emit()

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        pass

    def _update_characters(self):
        for char in self.novel.characters:
            if self.agenda.character_id and char.id != self.agenda.character_id:
                self.cbCharacter.addItem(avatars.avatar(char), char.name, char)

    def _type_toggled(self):
        lbl_prefix = 'Character vs.'
        self.cbCharacter.setVisible(self.btnCharacter.isChecked())
        if self.btnCharacter.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} <b style="color:#c1666b">Character</b>')
            self._type = ConflictType.CHARACTER
        elif self.btnSociety.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} <b style="color:#69306d">Society</b>')
            self._type = ConflictType.SOCIETY
        elif self.btnNature.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} <b style="color:#157a6e">Nature</b>')
            self._type = ConflictType.NATURE
        elif self.btnTechnology.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} <b style="color:#4a5859">Technology</b>')
            self._type = ConflictType.TECHNOLOGY
        elif self.btnSupernatural.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} <b style="color:#ac7b84">Supernatural</b>')
            self._type = ConflictType.SUPERNATURAL
        elif self.btnSelf.isChecked():
            self.lblConflictType.setText(f'{lbl_prefix} <b style="color:#94b0da">Self</b>')
            self._type = ConflictType.SELF

    def _keyphrase_edited(self, text: str):
        self.btnAddNew.setEnabled(len(text) > 0)

    def _add_new(self):
        if not self.agenda.character_id:
            return emit_critical('Select agenda or POV character first')
        conflict = Conflict(self.lineKey.text(), self._type, character_id=self.agenda.character_id)
        if self._type == ConflictType.CHARACTER:
            conflict.conflicting_character_id = self.cbCharacter.currentData().id

        self.novel.conflicts.append(conflict)
        self.agenda.conflict_references.append(ConflictReference(conflict.id))
        self.repo.update_novel(self.novel)
        self.conflictSelectionChanged.emit()
        self.refresh()
        self.lineKey.clear()

    def _previousConflictSelected(self):
        conflicts = self._model.selections()
        conflict: Conflict = conflicts.pop()
        self.agenda.conflict_references.append(ConflictReference(conflict.id))
        self.conflictSelectionChanged.emit()


class CharacterConflictSelector(QWidget):
    conflictSelected = pyqtSignal()

    def __init__(self, novel: Novel, scene: Scene, parent=None):
        super().__init__(parent)
        self.novel = novel
        self.scene = scene
        self.conflict: Optional[Conflict] = None
        self.conflict_ref: Optional[ConflictReference] = None
        hbox(self)

        self.label: Optional[ConflictLabel] = None

        self.btnLinkConflict = tool_btn(IconRegistry.conflict_icon())
        self.layout().addWidget(self.btnLinkConflict)
        self.btnLinkConflict.setIcon(IconRegistry.conflict_icon())
        self.btnLinkConflict.setStyleSheet('''
                        QPushButton::menu-indicator {
                            width: 0px;
                        }
                        QPushButton {
                            border: 2px dotted grey;
                            border-radius: 6px;
                            font: italic;
                        }
                        QPushButton:hover {
                            border: 2px dotted orange;
                            color: orange;
                            font: normal;
                        }
                        QPushButton:pressed {
                            border: 2px solid white;
                        }
                    ''')

        self.btnLinkConflict.installEventFilter(OpacityEventFilter(parent=self.btnLinkConflict))
        self.selectorWidget = CharacterConflictWidget(self.novel, self.scene, self.scene.agendas[0])
        self._menu = MenuWidget(self.btnLinkConflict)
        self._menu.addWidget(self.selectorWidget)

        self.selectorWidget.conflictSelectionChanged.connect(self._conflictSelected)

    def setConflict(self, conflict: Conflict, conflict_ref: ConflictReference):
        self.conflict = conflict
        self.conflict_ref = conflict_ref
        self.label = ConflictLabel(self.novel, self.conflict)
        self.label.removalRequested.connect(self._remove)
        self.label.clicked.connect(self._conflictRefClicked)
        self.layout().addWidget(self.label)
        self.btnLinkConflict.setHidden(True)

    def _conflictSelected(self):
        self._menu.hide()
        new_conflict = self.scene.agendas[0].conflicts(self.novel)[-1]
        new_conflict_ref = self.scene.agendas[0].conflict_references[-1]
        # self.btnLinkConflict.menu().hide()
        self.setConflict(new_conflict, new_conflict_ref)

        self.conflictSelected.emit()

    def _conflictRefClicked(self):
        pass

    def _remove(self):
        if self.parent():
            anim = qtanim.fade_out(self, duration=150)
            anim.finished.connect(self.__destroy)

    def __destroy(self):
        self.scene.agendas[0].remove_conflict(self.conflict)
        self.parent().layout().removeWidget(self)
        gc(self)
