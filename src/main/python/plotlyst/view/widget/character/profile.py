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
from abc import abstractmethod
from functools import partial
from typing import Optional, List, Dict, Any

import emoji
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QResizeEvent, QWheelEvent
from PyQt6.QtWidgets import QWidget, QLabel, QSizePolicy, QSlider
from overrides import overrides
from qthandy import vbox, clear_layout, hbox, bold, underline, spacer, vspacer, margins, pointy

from plotlyst.core.domain import Character, CharacterProfileSectionReference, CharacterProfileFieldReference, \
    CharacterProfileFieldType
from plotlyst.core.template import TemplateField, iq_field, eq_field, rationalism_field, willpower_field, \
    creativity_field, traits_field, values_field
from plotlyst.env import app_env
from plotlyst.view.common import tool_btn, wrap, emoji_font
from plotlyst.view.icons import IconRegistry
from plotlyst.view.layout import group
from plotlyst.view.style.slider import apply_slider_color
from plotlyst.view.widget.button import CollapseButton
from plotlyst.view.widget.input import AutoAdjustableTextEdit
from plotlyst.view.widget.progress import CircularProgressBar
from plotlyst.view.widget.template.impl import TraitSelectionWidget, LabelsSelectionWidget


class ProfileFieldWidget(QWidget):
    valueFilled = pyqtSignal(float)
    valueReset = pyqtSignal()


class TemplateFieldWidgetBase(ProfileFieldWidget):
    def __init__(self, parent=None):
        super(TemplateFieldWidgetBase, self).__init__(parent)
        self.lblEmoji = QLabel(self)
        self.lblEmoji.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        # self.lblEmoji.setToolTip(field.description if field.description else field.placeholder)
        self.lblName = QLabel(self)
        self.lblName.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        # self.lblName.setText(self.field.name)
        # self.lblName.setToolTip(field.description if field.description else field.placeholder)

        # if self.field.emoji:
        #     self.updateEmoji(emoji.emojize(self.field.emoji))
        # else:
        self.lblName.setHidden(True)
        self.lblEmoji.setHidden(True)

        # if not field.show_label:
        #     self.lblName.setHidden(True)

        if app_env.is_mac():
            self._boxSpacing = 1
            self._boxMargin = 0
        else:
            self._boxSpacing = 3
            self._boxMargin = 1

    @abstractmethod
    def value(self) -> Any:
        pass

    @abstractmethod
    def setValue(self, value: Any):
        pass

    def updateEmoji(self, emoji: str):
        self.lblEmoji.setFont(emoji_font())
        self.lblEmoji.setText(emoji)
        self.lblEmoji.setVisible(True)

    def updateLabel(self, text: str):
        self.lblName.setText(text)
        self.lblName.setVisible(True)


class ProfileSectionWidget(ProfileFieldWidget):
    headerEnabledChanged = pyqtSignal(bool)

    def __init__(self, section: CharacterProfileSectionReference, parent=None):
        super().__init__(parent)
        self.section = section
        vbox(self)
        self.btnHeader = CollapseButton(Qt.Edge.BottomEdge, Qt.Edge.RightEdge)
        self.btnHeader.setIconSize(QSize(16, 16))
        bold(self.btnHeader)
        underline(self.btnHeader)
        self.btnHeader.setText(section.type.name)
        self.btnHeader.setToolTip(section.type.name)

        self.wdgHeader = QWidget()
        hbox(self.wdgHeader, 1, 0)
        self.wdgHeader.layout().addWidget(self.btnHeader)
        self.progress = CircularProgressBar()
        self.wdgHeader.layout().addWidget(self.progress, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.wdgHeader.layout().addWidget(spacer())

        self.wdgContainer = QWidget()
        vbox(self.wdgContainer, 0)
        margins(self.wdgContainer, left=20)

        self.layout().addWidget(self.wdgHeader)
        self.layout().addWidget(self.wdgContainer)

        self.children: List[ProfileFieldWidget] = []
        self.progressStatuses: Dict[ProfileFieldWidget, float] = {}

        self.btnHeader.toggled.connect(self._toggleCollapse)

    def attachWidget(self, widget: ProfileFieldWidget):
        self.children.append(widget)
        self.wdgContainer.layout().addWidget(widget)
        self.progressStatuses[widget] = False
        widget.valueFilled.connect(partial(self._valueFilled, widget))
        widget.valueReset.connect(partial(self._valueReset, widget))

    def updateProgress(self):
        self.progress.setMaxValue(len(self.progressStatuses.keys()))
        self.progress.update()

    def collapse(self, collapsed: bool):
        self.btnHeader.setChecked(collapsed)

    def _toggleCollapse(self, checked: bool):
        self.wdgContainer.setHidden(checked)

    def _valueFilled(self, widget: ProfileFieldWidget, value: float):
        if self.progressStatuses[widget] == value:
            return

        self.progressStatuses[widget] = value
        self.progress.setValue(sum(self.progressStatuses.values()))

    def _valueReset(self, widget: ProfileFieldWidget):
        if not self.progressStatuses[widget]:
            return

        self.progressStatuses[widget] = 0
        self.progress.setValue(sum(self.progressStatuses.values()))


class SmallTextTemplateFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, parent=None, minHeight: int = 60):
        super(SmallTextTemplateFieldWidget, self).__init__(parent)
        _layout = vbox(self, margin=self._boxMargin, spacing=self._boxSpacing)
        self.wdgEditor = AutoAdjustableTextEdit(height=minHeight)
        self.wdgEditor.setProperty('white-bg', True)
        self.wdgEditor.setProperty('rounded', True)
        self.wdgEditor.setAcceptRichText(False)
        self.wdgEditor.setTabChangesFocus(True)
        self.setMaximumWidth(600)

        self._filledBefore: bool = False

        self.wdgTop = group(self.lblEmoji, self.lblName, spacer())
        _layout.addWidget(self.wdgTop)
        _layout.addWidget(self.wdgEditor)

        self.wdgEditor.textChanged.connect(self._textChanged)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.toPlainText()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setText(value)

    def _textChanged(self):
        text = self.wdgEditor.toPlainText()
        if text and not self._filledBefore:
            self.valueFilled.emit(1)
            self._filledBefore = True
        elif not text:
            self.valueReset.emit()
            self._filledBefore = False

        self._saveText(text)

    def _saveText(self, text: str):
        pass


class NoteField(SmallTextTemplateFieldWidget):
    def __init__(self, field: CharacterProfileFieldReference, parent=None):
        super().__init__(parent)
        self.field = field
        self.setValue(self.field.value)
        self.wdgEditor.setPlaceholderText('Write your notes...')

    @overrides
    def _saveText(self, text: str):
        self.field.value = text


class CustomTextField(SmallTextTemplateFieldWidget):
    def __init__(self, parent=None):
        # add CustomCharacterProfileField
        super().__init__(parent)


class SummaryField(SmallTextTemplateFieldWidget):
    def __init__(self, character: Character, parent=None):
        super().__init__(parent=parent)
        self.character = character
        self.wdgEditor.setPlaceholderText("Summarize your character's role in the story")
        self.setValue(self.character.summary)

    @overrides
    def _saveText(self, text: str):
        self.character.summary = text


class LabelsTemplateFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wdgEditor = self._editor()
        _layout = vbox(self)
        _layout.addWidget(group(self.lblEmoji, self.lblName, spacer()))
        _layout.addWidget(self.wdgEditor)

        self.wdgEditor.selectionChanged.connect(self._selectionChanged)

    @abstractmethod
    def _editor(self) -> LabelsSelectionWidget:
        pass

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setValue(value)

    def _selectionChanged(self):
        if self.wdgEditor.selectedItems():
            self.valueFilled.emit(1)
        else:
            self.valueReset.emit()


class TraitsFieldWidget(LabelsTemplateFieldWidget):
    def __init__(self, character: Character, parent=None):
        super(TraitsFieldWidget, self).__init__(parent)
        self.character = character

        self.updateEmoji(emoji.emojize(':dna:'))
        self.updateLabel('Traits')

        self.setValue(self.character.traits)

    @overrides
    def _editor(self) -> LabelsSelectionWidget:
        return TraitSelectionWidget(traits_field)

    @overrides
    def _selectionChanged(self):
        traits = self.value()
        if traits:
            self.valueFilled.emit(1)
        else:
            self.valueReset.emit()

        self.character.traits[:] = traits


class ValuesFieldWidget(LabelsTemplateFieldWidget):
    def __init__(self, character: Character, parent=None):
        super().__init__(parent)
        self.character = character

        self.updateEmoji(emoji.emojize(':smiling_face_with_open_hands:'))
        self.updateLabel('Values')

    @overrides
    def _editor(self) -> LabelsSelectionWidget:
        return LabelsSelectionWidget(values_field)


class BarSlider(QSlider):
    @overrides
    def wheelEvent(self, event: QWheelEvent) -> None:
        event.ignore()


class BarTemplateFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        _layout = vbox(self)
        self.wdgEditor = BarSlider(Qt.Orientation.Horizontal)
        pointy(self.wdgEditor)
        self.wdgEditor.setPageStep(5)
        self.setMaximumWidth(600)

        _layout.addWidget(group(self.lblEmoji, self.lblName, spacer()))
        # if self.field.compact:
        #     editor = group(self.wdgEditor, spacer())
        #     margins(editor, left=5)
        #     _layout.addWidget(editor)
        # else:
        _layout.addWidget(wrap(self.wdgEditor, margin_left=5))

        self.wdgEditor.valueChanged.connect(self._valueChanged)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setValue(value)

    def _valueChanged(self, value: int):
        if value:
            self.valueFilled.emit(1)
        else:
            self.valueReset.emit()
        self._saveValue(value)

    def _saveValue(self, value: int):
        pass


class FacultyField(BarTemplateFieldWidget):
    def __init__(self, ref: CharacterProfileFieldReference, field: TemplateField, character: Character, parent=None):
        super().__init__(parent)
        self.ref = ref
        self.field = field
        self.character = character

        self.lblEmoji.setToolTip(field.description if field.description else field.placeholder)
        self.lblName.setText(self.field.name)
        self.lblName.setVisible(True)
        self.lblName.setToolTip(field.description if field.description else field.placeholder)

        if self.field.emoji:
            self.updateEmoji(emoji.emojize(self.field.emoji))
        else:
            self.lblEmoji.setHidden(True)

        self.wdgEditor.setMinimum(field.min_value)
        self.wdgEditor.setMaximum(field.max_value)
        if field.color:
            apply_slider_color(self.wdgEditor, field.color)

        self.setValue(self.character.faculties.get(self.ref.type.value, 0))

    @overrides
    def _saveValue(self, value: int):
        self.character.faculties[self.ref.type.value] = value


def field_widget(ref: CharacterProfileFieldReference, character: Character) -> TemplateFieldWidgetBase:
    if ref.type == CharacterProfileFieldType.Field_Summary:
        return SummaryField(character)
    elif ref.type.name.startswith('Field_Faculties'):
        if ref.type == CharacterProfileFieldType.Field_Faculties_IQ:
            field = iq_field
        elif ref.type == CharacterProfileFieldType.Field_Faculties_EQ:
            field = eq_field
        elif ref.type == CharacterProfileFieldType.Field_Faculties_Rationalism:
            field = rationalism_field
        elif ref.type == CharacterProfileFieldType.Field_Faculties_Willpower:
            field = willpower_field
        elif ref.type == CharacterProfileFieldType.Field_Faculties_Creativity:
            field = creativity_field
        else:
            raise ValueError(f'Unrecognized field type {ref.type}')
        return FacultyField(ref, field, character)
    elif ref.type == CharacterProfileFieldType.Field_Traits:
        return TraitsFieldWidget(character)
    elif ref.type == CharacterProfileFieldType.Field_Values:
        return ValuesFieldWidget(character)
    else:
        return NoteField(ref)


class CharacterProfileEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._character: Optional[Character] = None
        self.btnCustomize = tool_btn(IconRegistry.preferences_icon(), tooltip='Customize character profile', base=True,
                                     parent=self)

        vbox(self)

    def setCharacter(self, character: Character):
        self._character = character
        self.refresh()

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.btnCustomize.setGeometry(event.size().width() - 30, 2, 25, 25)

    def refresh(self):
        clear_layout(self)

        for section in self._character.profile:
            wdg = ProfileSectionWidget(section)
            self.layout().addWidget(wdg)
            for field in section.fields:
                fieldWdg = field_widget(field, self._character)
                wdg.attachWidget(fieldWdg)

        self.layout().addWidget(vspacer())

        self.btnCustomize.raise_()
