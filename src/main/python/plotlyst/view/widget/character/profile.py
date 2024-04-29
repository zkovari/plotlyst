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
from typing import Optional, List, Dict, Any, Tuple

import emoji
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QResizeEvent, QWheelEvent
from PyQt6.QtWidgets import QWidget, QLabel, QSizePolicy, QSlider, QToolButton, QVBoxLayout
from overrides import overrides
from qthandy import vbox, clear_layout, hbox, bold, underline, spacer, vspacer, margins, pointy, retain_when_hidden, \
    transparent, sp, gc, decr_font
from qthandy.filter import OpacityEventFilter, VisibilityToggleEventFilter
from qtmenu import MenuWidget, ActionTooltipDisplayMode

from plotlyst.core.domain import Character, CharacterProfileSectionReference, CharacterProfileFieldReference, \
    CharacterProfileFieldType, CharacterMultiAttribute, CharacterProfileSectionType, MultiAttributePrimaryType, \
    MultiAttributeSecondaryType
from plotlyst.core.template import TemplateField, iq_field, eq_field, rationalism_field, willpower_field, \
    creativity_field, traits_field, values_field, flaw_placeholder_field, goal_field, internal_goal_field, stakes_field, \
    conflict_field, motivation_field, methods_field, internal_motivation_field, internal_conflict_field, \
    internal_stakes_field
from plotlyst.env import app_env
from plotlyst.view.common import tool_btn, wrap, emoji_font, action, insert_before_the_end
from plotlyst.view.icons import IconRegistry
from plotlyst.view.layout import group
from plotlyst.view.style.slider import apply_slider_color
from plotlyst.view.widget.button import CollapseButton, SecondaryActionPushButton
from plotlyst.view.widget.display import Icon
from plotlyst.view.widget.input import AutoAdjustableTextEdit, Toggle
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


class SectionContext:

    def has_addition(self) -> bool:
        return False

    def primaryFields(self) -> List[TemplateField]:
        return []

    def primaryButtonText(self) -> str:
        return 'Add new item'

    def primaryAttributes(self, character: Character) -> List[CharacterMultiAttribute]:
        pass

    def primaryFieldType(self) -> CharacterProfileFieldType:
        pass

    # def secondaryFields(self, primary: TemplateField) -> List[TemplateField]:
    #     return []


def character_primary_attribute_type(field: TemplateField) -> MultiAttributePrimaryType:
    if field is goal_field:
        return MultiAttributePrimaryType.External_goal
    elif field is internal_goal_field:
        return MultiAttributePrimaryType.Internal_goal


def character_secondary_attribute_type(field: TemplateField) -> MultiAttributeSecondaryType:
    if field is motivation_field:
        return MultiAttributeSecondaryType.External_motivation
    elif field is internal_motivation_field:
        return MultiAttributeSecondaryType.Internal_motivation
    elif field is conflict_field:
        return MultiAttributeSecondaryType.External_conflict
    elif field is internal_conflict_field:
        return MultiAttributeSecondaryType.Internal_conflict
    elif field is stakes_field:
        return MultiAttributeSecondaryType.External_stakes
    elif field is internal_stakes_field:
        return MultiAttributeSecondaryType.Internal_stakes
    elif field is methods_field:
        return MultiAttributeSecondaryType.Methods


def character_secondary_field(value: str) -> TemplateField:
    secondary = MultiAttributeSecondaryType(value)
    if secondary == MultiAttributeSecondaryType.External_motivation:
        return motivation_field
    elif secondary == MultiAttributeSecondaryType.Internal_motivation:
        return internal_motivation_field
    elif secondary == MultiAttributeSecondaryType.External_conflict:
        return conflict_field
    elif secondary == MultiAttributeSecondaryType.Internal_conflict:
        return internal_conflict_field
    elif secondary == MultiAttributeSecondaryType.External_stakes:
        return stakes_field
    elif secondary == MultiAttributeSecondaryType.Internal_stakes:
        return internal_stakes_field
    elif secondary == MultiAttributeSecondaryType.Methods:
        return methods_field


class ProfileSectionWidget(ProfileFieldWidget):
    headerEnabledChanged = pyqtSignal(bool)
    fieldAdded = pyqtSignal(CharacterProfileFieldReference)

    def __init__(self, section: CharacterProfileSectionReference, context: SectionContext, character: Character,
                 parent=None):
        super().__init__(parent)
        self.character = character
        self.section = section
        self.context = context
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

        self.wdgBottom = QWidget()
        vbox(self.wdgBottom, 0, 0)
        margins(self.wdgBottom, left=20)

        self.layout().addWidget(self.wdgHeader)
        self.layout().addWidget(self.wdgContainer)
        self.layout().addWidget(self.wdgBottom)

        if self.context.has_addition():
            self._btnPrimary = SecondaryActionPushButton()
            self._btnPrimary.setText(self.context.primaryButtonText())
            self._btnPrimary.setIcon(IconRegistry.plus_icon('grey'))
            decr_font(self._btnPrimary)
            fields = self.context.primaryFields()
            self._menu = MenuWidget(self._btnPrimary)
            self._menu.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
            for field in fields:
                self._menu.addAction(
                    action(field.name, icon=IconRegistry.from_name(field.icon), tooltip=field.description,
                           slot=partial(self._addPrimaryField, field),
                           parent=self._menu))

            self.wdgBottom.layout().addWidget(self._btnPrimary)

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
        self.wdgBottom.setHidden(checked)

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

    def _addPrimaryField(self, field: TemplateField):
        attr = CharacterMultiAttribute(character_primary_attribute_type(field))
        self.context.primaryAttributes(self.character).append(attr)
        field = CharacterProfileFieldReference(self.context.primaryFieldType(), ref=attr.id)
        self.section.fields.append(field)

        fieldWdg = field_widget(field, self.character)
        self.attachWidget(fieldWdg)


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
    def __init__(self, field: TemplateField, parent=None, minHeight: int = 60):
        super().__init__(parent, minHeight=minHeight)
        self.field = field
        self.updateEmoji(emoji.emojize(self.field.emoji))
        self.updateLabel(self.field.name)
        self.wdgEditor.setPlaceholderText(self.field.placeholder)


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
        value = self.value()
        if value:
            self.valueFilled.emit(1)
        else:
            self.valueReset.emit()

        self._saveValue(value)

    def _saveValue(self, value: Any):
        pass


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
    def _saveValue(self, value: Any):
        self.character.traits[:] = value


class ValuesFieldWidget(LabelsTemplateFieldWidget):
    def __init__(self, character: Character, parent=None):
        super().__init__(parent)
        self.character = character

        self.updateEmoji(emoji.emojize(':smiling_face_with_open_hands:'))
        self.updateLabel('Values')

        self.setValue(self.character.values)

    @overrides
    def _editor(self) -> LabelsSelectionWidget:
        return LabelsSelectionWidget(values_field)

    @overrides
    def _saveValue(self, value: Any):
        self.character.values[:] = value


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


class FieldToggle(QWidget):
    def __init__(self, field: TemplateField, parent=None):
        super().__init__(parent)
        self._field = field
        hbox(self)

        self._lblEmoji = QLabel(self)
        self._lblEmoji.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._lblEmoji.setToolTip(field.description if field.description else field.placeholder)
        self._lblName = QLabel(self)
        self._lblName.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._lblName.setText(self._field.name)
        self._lblName.setToolTip(field.description if field.description else field.placeholder)

        if self._field.emoji:
            self._lblEmoji.setFont(emoji_font())
            self._lblEmoji.setText(emoji.emojize(self._field.emoji))
        else:
            self._lblEmoji.setHidden(True)

        self.toggle = Toggle()

        self.layout().addWidget(self._lblEmoji)
        self.layout().addWidget(self._lblName)
        self.layout().addWidget(spacer())
        self.layout().addWidget(self.toggle)


class FieldSelector(QWidget):
    toggled = pyqtSignal(TemplateField, bool)
    clicked = pyqtSignal(TemplateField, bool)

    def __init__(self, fields: List[TemplateField], parent=None):
        super().__init__(parent)
        vbox(self)
        self._fields: Dict[TemplateField, FieldToggle] = {}

        for field in fields:
            wdg = FieldToggle(field)
            self._fields[field] = wdg
            self.layout().addWidget(wdg)
            wdg.toggle.toggled.connect(partial(self.toggled.emit, field))
            wdg.toggle.clicked.connect(partial(self.clicked.emit, field))

    def toggle(self, field: TemplateField):
        self._fields[field].toggle.toggle()


class _SecondaryFieldSelectorButton(QToolButton):
    removalRequested = pyqtSignal()
    renameRequested = pyqtSignal()

    def __init__(self, field: TemplateField, selector: FieldSelector, enableRename: bool = False, parent=None):
        super(_SecondaryFieldSelectorButton, self).__init__(parent)
        self._field = field
        self._selector = selector

        retain_when_hidden(self)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        transparent(self)
        pointy(self)
        self.setIconSize(QSize(22, 22))
        self.setIcon(IconRegistry.plus_edit_icon())

        menu = MenuWidget(self)
        menu.addWidget(self._selector)
        menu.addSeparator()

        if enableRename:
            menu.addAction(action('Rename', IconRegistry.edit_icon(), slot=self.renameRequested))
            menu.addSeparator()

        menu.addAction(action(f'Remove {self._field.name}', IconRegistry.trash_can_icon(), slot=self.removalRequested))
        self.installEventFilter(OpacityEventFilter(self, leaveOpacity=0.7))


class _PrimaryFieldWidget(QWidget):
    removed = pyqtSignal()
    renamed = pyqtSignal()
    valueChanged = pyqtSignal()

    def __init__(self, attribute: CharacterMultiAttribute, field: TemplateField, secondaryFields: List[TemplateField],
                 parent=None):
        super().__init__(parent)
        self.attribute = attribute
        self._field = field
        self._secondaryFields = secondaryFields
        self._secondaryFieldWidgets: Dict[TemplateField, Optional[SmallTextTemplateFieldWidget]] = {}
        for sf in secondaryFields:
            self._secondaryFieldWidgets[sf] = None
        vbox(self, 0, 2)
        self._primaryWdg = CustomTextField(field)
        self._primaryWdg.valueFilled.connect(self.valueChanged.emit)
        self._primaryWdg.valueReset.connect(self.valueChanged.emit)

        self._selector = FieldSelector(secondaryFields)
        btnSecondary = _SecondaryFieldSelectorButton(self._field, self._selector,
                                                     enableRename=field.id == flaw_placeholder_field.id)
        btnSecondary.removalRequested.connect(self.removed)
        btnSecondary.renameRequested.connect(self.renamed)
        self._selector.toggled.connect(self._toggleSecondaryField)
        self._selector.clicked.connect(self._clickSecondaryField)
        insert_before_the_end(self._primaryWdg.wdgTop, btnSecondary)

        self._secondaryWdgContainer = QWidget()
        vbox(self._secondaryWdgContainer, 0, 2)
        margins(self._secondaryWdgContainer, left=40)
        for _ in self._secondaryFields:
            self._secondaryWdgContainer.layout().addWidget(spacer())

        top = QWidget()
        hbox(top)
        top.layout().addWidget(self._primaryWdg)
        spacer_ = spacer()
        sp(spacer_).h_preferred()
        top.layout().addWidget(spacer_)
        self.layout().addWidget(top)
        self.layout().addWidget(self._secondaryWdgContainer)

        for value, toggled in self.attribute.settings.items():
            if toggled:
                self._selector.toggle(character_secondary_field(value))

        self.installEventFilter(VisibilityToggleEventFilter(btnSecondary, self._primaryWdg))

    def field(self) -> TemplateField:
        return self._field

    def value(self) -> str:
        return self._primaryWdg.value()

    def setValue(self, value: str):
        self._primaryWdg.setValue(value)

    def refresh(self):
        self._primaryWdg.refresh()

    def secondaryFields(self) -> List[Tuple[str, str]]:
        fields = []
        for field, wdg in self._secondaryFieldWidgets.items():
            if wdg is None:
                continue
            fields.append((str(field.id), wdg.value()))

        return fields

    def setSecondaryField(self, secondary: TemplateField, value: str):
        self._selector.toggle(secondary)
        self._secondaryFieldWidgets[secondary].setValue(value)

    def _toggleSecondaryField(self, secondary: TemplateField, toggled: bool):
        i = self._secondaryFields.index(secondary)

        if toggled:
            wdg = CustomTextField(secondary, minHeight=40)
            wdg.valueFilled.connect(self.valueChanged.emit)
            wdg.valueReset.connect(self.valueChanged.emit)
            self._secondaryFieldWidgets[secondary] = wdg
            item = self._secondaryWdgContainer.layout().itemAt(i)
            icon = Icon()
            icon.setIcon(IconRegistry.from_name('msc.dash', 'grey'))
            spac = spacer()
            sp(spac).h_preferred()
            self._secondaryWdgContainer.layout().replaceWidget(item.widget(), group(icon, wdg, spac))
        else:
            self._secondaryWdgContainer.layout().replaceWidget(self._secondaryFieldWidgets[secondary], spacer())
            gc(self._secondaryFieldWidgets[secondary])
            self._secondaryFieldWidgets[secondary] = None

    def _clickSecondaryField(self, secondary: TemplateField, toggled: bool):
        self.attribute.settings[character_secondary_attribute_type(secondary).value] = toggled
        self.valueChanged.emit()


class MultiAttributesTemplateWidgetBase(ProfileFieldWidget):
    def __init__(self, attribute: CharacterMultiAttribute, character: Character, parent=None):
        super().__init__(parent)
        self.attribute = attribute
        # self.field = field
        self.character = character
        self._hasAlias = False

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._layout: QVBoxLayout = vbox(self, 0, 5)

        if attribute.type == MultiAttributePrimaryType.External_goal:
            field = goal_field
        else:
            field = internal_goal_field
        wdg = _PrimaryFieldWidget(self.attribute, field, self._secondaryFields(field))
        self.layout().addWidget(wdg)

        self._layout.addWidget(vspacer())

    # def value(self) -> Any:
    #     def secondaryValues(primaryWdg: _PrimaryFieldWidget):
    #         values = []
    #         for field in primaryWdg.secondaryFields():
    #             s_id, value_ = field
    #             values.append({self.ID_KEY: s_id, self.VALUE_KEY: value_})
    #         return values
    #
    #     value = {}
    #     for i, primary_wdg in enumerate(self._primaryWidgets):
    #         sid = str(primary_wdg.field().id)
    #         sid += f'&{i}'
    #         if self._hasAlias:
    #             sid += f'&{primary_wdg.field().name}'
    #         value[sid] = {self.VALUE_KEY: primary_wdg.value(),
    #                       self.SECONDARY_KEY: secondaryValues(primary_wdg)}
    #         if self._hasAlias:
    #             value[sid][self.ALIAS_KEY] = primary_wdg.field().name
    #
    #     return value
    #
    # def setValue(self, value: Any):
    #     if value is None:
    #         return
    #     if isinstance(value, str):
    #         return
    #
    #     primary_fields = self._primaryFields()
    #     for k, v in value.items():
    #         k = k.split('&')[0]
    #         primary = next((x for x in primary_fields if str(x.id) == k), None)
    #         if primary is None:
    #             continue
    #         if self._hasAlias and self.ALIAS_KEY in v.keys():
    #             primary = copy.deepcopy(primary)
    #             primary.name = v[self.ALIAS_KEY]
    #         wdg = self._addPrimaryField(primary)
    #         wdg.setValue(v[self.VALUE_KEY])
    #
    #         secondary_fields = self._secondaryFields(primary)
    #         for secondary in v[self.SECONDARY_KEY]:
    #             secondary_field = next((x for x in secondary_fields if str(x.id) == secondary[self.ID_KEY]), None)
    #             if secondary_field:
    #                 wdg.setSecondaryField(secondary_field, secondary[self.VALUE_KEY])
    #
    #     self._valueChanged()

    # def _primaryFields(self) -> List[TemplateField]:
    #     return []
    #
    # def _primaryButtonText(self) -> str:
    #     return 'Add new item'

    def _secondaryFields(self, primary: TemplateField) -> List[TemplateField]:
        return []

    # def _addPrimaryField(self, field: TemplateField) -> _PrimaryFieldWidget:
    #     wdg = _PrimaryFieldWidget(field, self._secondaryFields(field))
    #     self._primaryWidgets.append(wdg)
    #     wdg.removed.connect(partial(self._removePrimaryField, wdg))
    #     wdg.renamed.connect(partial(self._renamePrimaryField, wdg))
    #     wdg.valueChanged.connect(self._valueChanged)
    #     if self._layout.count() > 2:
    #         self._layout.insertWidget(self._layout.count() - 2, line())
    #     self._layout.insertWidget(self._layout.count() - 2, wdg)
    #
    #     return wdg

    def _removePrimaryField(self, wdg: _PrimaryFieldWidget):
        self._primaryWidgets.remove(wdg)
        self._layout.removeWidget(wdg)
        gc(wdg)

    def _renamePrimaryField(self, wdg: _PrimaryFieldWidget):
        pass

    def _valueChanged(self):
        count = 0
        value = 0
        for wdg in self._primaryWidgets:
            count += 1
            if wdg.value():
                value += 1
            for _, v in wdg.secondaryFields():
                count += 1
                if v:
                    value += 1
        self.valueFilled.emit(value / count if count else 0)


class MultiAttributeSectionContext(SectionContext):

    @overrides
    def has_addition(self) -> bool:
        return True


class GmcSectionContext(MultiAttributeSectionContext):
    @overrides
    def primaryButtonText(self) -> str:
        return 'Add new goal'

    @overrides
    def primaryFields(self) -> List[TemplateField]:
        return [goal_field, internal_goal_field]

    @overrides
    def primaryAttributes(self, character: Character) -> List[CharacterMultiAttribute]:
        return character.gmc

    @overrides
    def primaryFieldType(self) -> CharacterProfileFieldType:
        return CharacterProfileFieldType.Field_Goals
    # @overrides
    # def secondaryFields(self, primary: TemplateField) -> List[TemplateField]:
    #     if primary.id == goal_field.id:
    #         return [stakes_field, conflict_field, motivation_field, methods_field, internal_motivation_field,
    #                 internal_conflict_field,
    #                 internal_stakes_field]
    #     else:
    #         return [methods_field, internal_motivation_field, internal_conflict_field, internal_stakes_field]


class GmcFieldWidget(MultiAttributesTemplateWidgetBase):

    def __init__(self, attribute: CharacterMultiAttribute, character: Character,
                 ref: CharacterProfileFieldReference, parent=None):
        super().__init__(attribute, character, parent=parent)
        self.ref = ref

    @overrides
    def _secondaryFields(self, primary: TemplateField) -> List[TemplateField]:
        if primary.id == goal_field.id:
            return [stakes_field, conflict_field, motivation_field, methods_field, internal_motivation_field,
                    internal_conflict_field,
                    internal_stakes_field]
        else:
            return [methods_field, internal_motivation_field, internal_conflict_field, internal_stakes_field]


def field_widget(ref: CharacterProfileFieldReference, character: Character) -> ProfileFieldWidget:
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
    elif ref.type == CharacterProfileFieldType.Field_Goals:
        attribute = None
        for gmc in character.gmc:
            if gmc.id == ref.ref:
                attribute = gmc
                break
        return GmcFieldWidget(attribute, character, ref)

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
            sc = SectionContext()
            if section.type == CharacterProfileSectionType.Goals:
                sc = GmcSectionContext()
            wdg = ProfileSectionWidget(section, sc, self._character)
            # wdg.fieldAddedc.oonnect(partial(self._primaryFieldAdded, ))
            self.layout().addWidget(wdg)
            for field in section.fields:
                fieldWdg = field_widget(field, self._character)
                wdg.attachWidget(fieldWdg)

        self.layout().addWidget(vspacer())

        self.btnCustomize.raise_()

    # def _primaryFieldAdded(self, field: CharacterProfileFieldReference):
