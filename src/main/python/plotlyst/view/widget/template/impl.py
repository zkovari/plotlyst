"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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
from typing import Optional, List, Any, Dict, Set

import emoji
import qtanim
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QModelIndex, QSize
from PyQt6.QtGui import QMouseEvent, QIcon
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QWidget, QLineEdit, QToolButton, QLabel, \
    QSpinBox, QButtonGroup, QSizePolicy, QListView, QPushButton, QTextEdit, QGridLayout, QMenu
from overrides import overrides
from qthandy import spacer, btn_popup, hbox, vbox, bold, line, underline, transparent, margins, \
    decr_font, retain_when_hidden, translucent, grid, btn_popup_menu, gc
from qthandy.filter import VisibilityToggleEventFilter, OpacityEventFilter
from qttextedit import EnhancedTextEdit

from src.main.python.plotlyst.core.help import enneagram_help, mbti_help
from src.main.python.plotlyst.core.template import TemplateField, SelectionItem, \
    enneagram_choices, goal_field, internal_goal_field, stakes_field, conflict_field, motivation_field, \
    internal_motivation_field, internal_conflict_field, internal_stakes_field
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.model.template import TemplateFieldSelectionModel, TraitsFieldItemsSelectionModel, \
    TraitsProxyModel
from src.main.python.plotlyst.view.common import pointy, action, wrap, emoji_font
from src.main.python.plotlyst.view.generated.field_text_selection_widget_ui import Ui_FieldTextSelectionWidget
from src.main.python.plotlyst.view.generated.trait_selection_widget_ui import Ui_TraitSelectionWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.button import SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.display import Subtitle, Emoji, Icon
from src.main.python.plotlyst.view.widget.input import AutoAdjustableTextEdit, Toggle
from src.main.python.plotlyst.view.widget.labels import TraitLabel, LabelsEditorWidget
from src.main.python.plotlyst.view.widget.progress import CircularProgressBar
from src.main.python.plotlyst.view.widget.template.base import TemplateDisplayWidget, TemplateFieldWidgetBase, \
    TemplateWidgetBase, ComplexTemplateWidgetBase


def _icon(item: SelectionItem) -> QIcon:
    if item.icon:
        return IconRegistry.from_name(item.icon, item.icon_color)
    else:
        return QIcon('')


class TextSelectionWidget(SecondaryActionPushButton):
    selectionChanged = pyqtSignal(object, object)

    def __init__(self, field: TemplateField, help: Dict[Any, str], parent=None):
        super(TextSelectionWidget, self).__init__(parent)
        self.field = field
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        self.setText(f'{self.field.name}...')
        self._popup = self.Popup(self.field, help)
        btn_popup(self, self._popup)

        self._selected: Optional[SelectionItem] = None
        self._items: Dict[str, SelectionItem] = {}
        for item in self.field.selections:
            self._items[item.text] = item

        self._popup.selected.connect(self._selection_changed)

    def value(self) -> str:
        return self._selected.text if self._selected else ''

    def setValue(self, value: str):
        self._selected = self._items.get(value)
        if self._selected:
            self.setText(self._selected.text)
            if self._selected.icon:
                self.setIcon(IconRegistry.from_name(self._selected.icon, self._selected.icon_color))
                self.initStyleSheet(self._selected.icon_color, 'solid', 'black')
            else:
                self.setIcon(IconRegistry.empty_icon())
                self.initStyleSheet('black', 'solid', 'black')
        else:
            self.setText(f'{self.field.name}...')
            self.setIcon(IconRegistry.empty_icon())

    def _selection_changed(self, item: SelectionItem):
        self.menu().hide()
        previous = self._selected
        self.setValue(item.text)
        self.selectionChanged.emit(previous, self._selected)

    class Popup(QFrame, Ui_FieldTextSelectionWidget):
        selected = pyqtSignal(SelectionItem)

        def __init__(self, field: TemplateField, help_: Dict[Any, str], parent=None):
            super().__init__(parent)
            self.setupUi(self)
            self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

            self.field = field
            self.help = help_

            self.model = TemplateFieldSelectionModel(self.field)
            self.model.setEditable(False)
            self.tblItems.setModel(self.model)
            self.tblItems.setColumnWidth(TemplateFieldSelectionModel.ColIcon, 26)
            self.tblItems.hideColumn(TemplateFieldSelectionModel.ColBgColor)

            self.btnSelect.setIcon(IconRegistry.ok_icon('white'))
            self.tblItems.selectionModel().selectionChanged.connect(self._selection_changed)
            self.tblItems.doubleClicked.connect(self._select)

            self.btnSelect.clicked.connect(self._select)

        @overrides
        def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
            pass  # catch event not to close the popup

        def _selection_changed(self):
            item = self._current_item()
            self.wdgLabels.clear()
            if item:
                self.btnSelect.setEnabled(True)
                self.textBrowser.setText(self.help.get(item.text, ''))
                if 'positive' in item.meta.keys():
                    for trait in item.meta['positive']:
                        self.wdgLabels.addLabel(TraitLabel(trait))  # '#008148'
                if 'negative' in item.meta.keys():
                    for trait in item.meta['negative']:
                        self.wdgLabels.addLabel(TraitLabel(trait, positive=False))
            else:
                self.btnSelect.setDisabled(True)
                self.textBrowser.clear()

        def _select(self):
            item = self._current_item()
            if item:
                self.selected.emit(item)

        def _current_item(self) -> Optional[SelectionItem]:
            indexes = self.tblItems.selectedIndexes()
            if not indexes:
                self.btnSelect.setDisabled(True)
                return
            return indexes[0].data(TemplateFieldSelectionModel.ItemRole)


class LabelsSelectionWidget(LabelsEditorWidget):
    selectionChanged = pyqtSignal()

    def __init__(self, field: TemplateField, parent=None):
        self.field = field
        super(LabelsSelectionWidget, self).__init__(parent)
        self._model.selection_changed.connect(self.selectionChanged.emit)
        self._model.item_edited.connect(self.selectionChanged.emit)

    @overrides
    def items(self) -> List[SelectionItem]:
        return self.field.selections

    @overrides
    def _initModel(self) -> TemplateFieldSelectionModel:
        return TemplateFieldSelectionModel(self.field)


class TraitSelectionWidget(LabelsSelectionWidget):

    def __init__(self, field: TemplateField, parent=None):
        super(TraitSelectionWidget, self).__init__(field, parent)
        self._model.setEditable(False)

    @overrides
    def _initModel(self) -> TemplateFieldSelectionModel:
        return TraitsFieldItemsSelectionModel(self.field)

    @overrides
    def _initPopupWidget(self) -> QWidget:
        wdg = self.Popup()
        wdg.setModel(self._model)
        return wdg

    @overrides
    def _addItems(self, items: Set[SelectionItem]):
        for item in items:
            if item.meta.get('positive', True):
                self._wdgLabels.addLabel(TraitLabel(item.text))
        for item in items:
            if not item.meta.get('positive', True):
                self._wdgLabels.addLabel(TraitLabel(item.text, positive=False))

    class Popup(QWidget, Ui_TraitSelectionWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setupUi(self)
            self.positiveProxy = TraitsProxyModel()
            self.negativeProxy = TraitsProxyModel(positive=False)
            self._model: Optional[TraitsFieldItemsSelectionModel] = None
            self.lstPositiveTraitsView.clicked.connect(self._toggleSelection)
            self.lstNegativeTraitsView.clicked.connect(self._toggleSelection)

        def setModel(self, model: TraitsFieldItemsSelectionModel):
            self._model = model

            self.positiveProxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.positiveProxy.setSourceModel(model)
            self.positiveProxy.setFilterKeyColumn(TemplateFieldSelectionModel.ColName)
            self.lstPositiveTraitsView.setModel(self.positiveProxy)
            self.filterPositive.textChanged.connect(self.positiveProxy.setFilterRegularExpression)

            self.negativeProxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.negativeProxy.setSourceModel(model)
            self.negativeProxy.setFilterKeyColumn(TemplateFieldSelectionModel.ColName)
            self.lstNegativeTraitsView.setModel(self.negativeProxy)
            self.filterNegative.textChanged.connect(self.negativeProxy.setFilterRegularExpression)

            for lst in [self.lstPositiveTraitsView, self.lstNegativeTraitsView]:
                lst.setModelColumn(TemplateFieldSelectionModel.ColName)
                lst.setViewMode(QListView.ViewMode.IconMode)
                lst.setFixedSize(300, 300)

        @overrides
        def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
            pass

        def _toggleSelection(self, index: QModelIndex):
            if self._model is None:
                return

            item = index.data(role=TraitsFieldItemsSelectionModel.ItemRole)
            self._model.toggleCheckedItem(item)


class ButtonSelectionWidget(QWidget):

    def __init__(self, field: TemplateField, parent=None):
        super(ButtonSelectionWidget, self).__init__(parent)
        self.field = field

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.group = QButtonGroup()
        self.group.setExclusive(self.field.exclusive)
        self.buttons = []
        for i, item in enumerate(self.field.selections):
            btn = QToolButton()
            btn.setIcon(_icon(item))
            btn.setToolTip(item.text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.buttons.append(btn)
            self.layout.addWidget(btn)
            self.group.addButton(btn, i)

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent):
        event.ignore()

    def value(self) -> List[int]:
        values = []
        for btn in self.group.buttons():
            if btn.isChecked():
                values.append(self.group.id(btn))
        return values

    def setValue(self, value: List[int]):
        for v in value:
            btn = self.group.button(v)
            if btn:
                btn.setChecked(True)


class SubtitleTemplateDisplayWidget(TemplateDisplayWidget):
    def __init__(self, field: TemplateField, parent=None):
        super(SubtitleTemplateDisplayWidget, self).__init__(field, parent)
        hbox(self)
        self.subtitle = Subtitle(self)
        self.subtitle.setTitle(field.name)
        self.subtitle.setDescription(field.description)
        self.layout().addWidget(self.subtitle)


class LabelTemplateDisplayWidget(TemplateDisplayWidget):
    def __init__(self, field: TemplateField, parent=None):
        super(LabelTemplateDisplayWidget, self).__init__(field, parent)
        hbox(self)
        self.label = QLabel(self)
        self.label.setText(field.name)
        self.label.setToolTip(field.description)
        self.layout().addWidget(self.label)


class IconTemplateDisplayWidget(TemplateDisplayWidget):
    def __init__(self, field: TemplateField, parent=None):
        super(IconTemplateDisplayWidget, self).__init__(field, parent)
        self.icon = Icon(self)
        self.icon.iconName = field.name
        if field.color:
            self.icon.iconColor = field.color
        vbox(self, 0, 0).addWidget(self.icon, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)


class HeaderTemplateDisplayWidget(TemplateDisplayWidget):
    headerEnabledChanged = pyqtSignal(bool)

    def __init__(self, field: TemplateField, parent=None):
        super(HeaderTemplateDisplayWidget, self).__init__(field, parent)
        hbox(self, margin=0, spacing=0)
        self.btnHeader = QPushButton()
        pointy(self.btnHeader)
        self.btnHeader.setIconSize(QSize(16, 16))
        self.btnHeader.setCheckable(True)
        self.btnHeader.setIcon(IconRegistry.from_name('mdi.chevron-down'))
        transparent(self.btnHeader)
        bold(self.btnHeader)
        underline(self.btnHeader)
        self.btnHeader.setText(field.name)
        self.btnHeader.setToolTip(field.description)
        self.layout().addWidget(self.btnHeader)

        self.progress = CircularProgressBar()
        self.layout().addWidget(self.progress, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.layout().addWidget(spacer())

        self._toggle: Optional[Toggle] = None
        if not field.required:
            self._toggle = Toggle(self)
            self._toggle.setToolTip(f'Character has {field.name}')
            retain_when_hidden(self._toggle)
            self._toggle.toggled.connect(self._headerEnabledChanged)
            self.layout().addWidget(self._toggle)

        self.children: List[TemplateWidgetBase] = []
        self.progressStatuses: Dict[TemplateWidgetBase] = {}

        self.btnHeader.toggled.connect(self._toggleCollapse)

    def attachWidget(self, widget: TemplateWidgetBase):
        self.children.append(widget)
        self.progressStatuses[widget] = False
        widget.valueFilled.connect(partial(self._valueFilled, widget))
        widget.valueReset.connect(partial(self._valueReset, widget))

    def updateProgress(self):
        self.progress.setMaxValue(len(self.children))
        self.progress.update()

    def collapse(self, collapsed: bool):
        self.btnHeader.setChecked(collapsed)

    @overrides
    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        if self._toggle:
            self._toggle.setVisible(True)

    @overrides
    def leaveEvent(self, a0: QEvent) -> None:
        if self._toggle and self._toggle.isChecked():
            self._toggle.setHidden(True)

    def _toggleCollapse(self, checked: bool):
        for wdg in self.children:
            wdg.setHidden(checked)
        if checked:
            self.btnHeader.setIcon(IconRegistry.from_name('mdi.chevron-right'))
        else:
            self.btnHeader.setIcon(IconRegistry.from_name('mdi.chevron-down'))

    def setHeaderEnabled(self, enabled: bool):
        self.collapse(not enabled)
        self.btnHeader.setEnabled(enabled)
        self.progress.setVisible(enabled)
        if self._toggle:
            self._toggle.setChecked(enabled)
            self._toggle.setHidden(enabled)

    def _headerEnabledChanged(self, enabled: bool):
        self.setHeaderEnabled(enabled)
        self.headerEnabledChanged.emit(enabled)

    def _valueFilled(self, widget: TemplateWidgetBase):
        if self.progressStatuses[widget]:
            return

        self.progressStatuses[widget] = True
        value = self.progress.value()
        self.progress.setValue(value + 1)

    def _valueReset(self, widget: TemplateWidgetBase):
        if not self.progressStatuses[widget]:
            return

        self.progressStatuses[widget] = False
        value = self.progress.value()
        self.progress.setValue(value - 1)


class LineTemplateDisplayWidget(TemplateDisplayWidget):
    def __init__(self, field: TemplateField, parent=None):
        super(LineTemplateDisplayWidget, self).__init__(field, parent)
        hbox(self)
        self.layout().addWidget(line())


class LineTextTemplateFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(LineTextTemplateFieldWidget, self).__init__(field, parent)
        _layout = hbox(self)
        self.wdgEditor = QLineEdit(self)

        _layout.addWidget(self.lblEmoji)
        _layout.addWidget(self.lblName)
        _layout.addWidget(self.wdgEditor)

        if self.field.compact:
            _layout.addWidget(spacer())

        self.wdgEditor.textChanged.connect(self._textChanged)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.text()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setText(value)

    def _textChanged(self, text: str):
        if text:
            self.valueFilled.emit()
        else:
            self.valueReset.emit()


class SmallTextTemplateFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(SmallTextTemplateFieldWidget, self).__init__(field, parent)
        _layout = vbox(self, margin=self._boxMargin, spacing=self._boxSpacing)
        self.wdgEditor = AutoAdjustableTextEdit(height=60)
        self.wdgEditor.setAcceptRichText(False)
        self.wdgEditor.setPlaceholderText(field.placeholder)
        self.wdgEditor.setToolTip(field.description if field.description else field.placeholder)
        self.setMaximumWidth(600)

        self.btnNotes = QToolButton()

        _layout.addWidget(group(self.lblEmoji, self.lblName, spacer(), self.btnNotes))
        _layout.addWidget(self.wdgEditor)

        self.wdgEditor.textChanged.connect(self._textChanged)
        if field.has_notes:
            self.btnNotes.setIcon(IconRegistry.from_name('mdi6.note-plus-outline'))
            pointy(self.btnNotes)
            transparent(self.btnNotes)
            translucent(self.btnNotes)
            self._notesEditor = EnhancedTextEdit()
            self._notesEditor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._notesEditor.setMinimumSize(400, 300)
            self._notesEditor.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
            self._notesEditor.setPlaceholderText(f'Add notes to {field.name}')
            self._notesEditor.setViewportMargins(5, 5, 5, 5)
            menu = btn_popup(self.btnNotes, self._notesEditor)
            menu.aboutToShow.connect(self._notesEditor.setFocus)
            self.installEventFilter(VisibilityToggleEventFilter(self.btnNotes, self))
            retain_when_hidden(self.btnNotes)
        else:
            self.btnNotes.setHidden(True)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.toPlainText()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setText(value)

    def _textChanged(self):
        if self.wdgEditor.toPlainText():
            self.valueFilled.emit()
        else:
            self.valueReset.emit()


class NumericTemplateFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(NumericTemplateFieldWidget, self).__init__(field, parent)

        _layout = hbox(self)
        self.wdgEditor = QSpinBox()
        if field.placeholder:
            self.wdgEditor.setPrefix(field.placeholder + ': ')
        self.wdgEditor.setMinimum(field.min_value)
        self.wdgEditor.setMaximum(field.max_value)

        _layout.addWidget(self.lblEmoji)
        _layout.addWidget(self.lblName)
        _layout.addWidget(self.wdgEditor)
        if self.field.compact:
            _layout.addWidget(spacer())

        self.wdgEditor.valueChanged.connect(self._valueChanged)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setValue(value)

    def _valueChanged(self, value: int):
        if value:
            self.valueFilled.emit()
        else:
            self.valueReset.emit()


class EnneagramFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(EnneagramFieldWidget, self).__init__(field, parent)
        self.wdgEditor = TextSelectionWidget(field, enneagram_help)
        _layout = hbox(self)
        _layout.addWidget(self.wdgEditor, alignment=Qt.AlignmentFlag.AlignTop)

        emojiDesire = Emoji()
        emojiDesire.setText(emoji.emojize(':smiling_face:'))
        emojiDesire.setToolTip('Core desire')
        emojiFear = Emoji()
        emojiFear.setText(emoji.emojize(':face_screaming_in_fear:'))
        emojiFear.setToolTip('Core fear')
        self.lblDesire = QLabel('')
        self.lblDesire.setToolTip('Core desire')
        self.lblFear = QLabel('')
        self.lblFear.setToolTip('Core fear')

        decr_font(emojiDesire, 3)
        decr_font(self.lblDesire)
        decr_font(emojiFear, 3)
        decr_font(self.lblFear)

        self.wdgAttr = group(
            group(emojiDesire, self.lblDesire, spacer()),
            group(emojiFear, self.lblFear, spacer()),
            vertical=False)
        margins(self.wdgAttr, left=10)
        _layout.addWidget(self.wdgAttr)
        self.wdgAttr.setHidden(True)

        if self.field.compact:
            _layout.addWidget(spacer())

        self.wdgEditor.selectionChanged.connect(self._selectionChanged)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setValue(value)
        enneagram = enneagram_choices.get(value)
        if enneagram:
            self._selectionChanged(new=enneagram, animated=False)

    def _selectionChanged(self, old: Optional[SelectionItem] = None, new: Optional[SelectionItem] = None,
                          animated: bool = True):
        if not new:
            self.wdgAttr.setHidden(True)
            self.valueReset.emit()
            return

        if animated:
            qtanim.fade_in(self.wdgAttr)
        else:
            self.wdgAttr.setVisible(True)
        self.lblDesire.setText(new.meta['desire'])
        self.lblFear.setText(new.meta['fear'])

        self.valueFilled.emit()


class MbtiFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(MbtiFieldWidget, self).__init__(field, parent)
        self.wdgEditor = TextSelectionWidget(field, mbti_help)

        _layout = vbox(self)
        _layout.addWidget(self.wdgEditor)

        if self.field.compact:
            _layout.addWidget(spacer())

        self.wdgEditor.selectionChanged.connect(self._selectionChanged)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setValue(value)
        if value:
            self.valueFilled.emit()

    def _selectionChanged(self, old: Optional[SelectionItem] = None, new: Optional[SelectionItem] = None,
                          animated: bool = True):
        if not new:
            self.valueReset.emit()
            return

        self.valueFilled.emit()


class TraitsFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(TraitsFieldWidget, self).__init__(field, parent)
        self.wdgEditor = TraitSelectionWidget(field, parent)
        _layout = vbox(self)
        _layout.addWidget(group(self.lblEmoji, self.lblName, spacer()))
        _layout.addWidget(self.wdgEditor)

        self.wdgEditor.selectionChanged.connect(self._selectionChanged)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setValue(value)

    def _selectionChanged(self):
        if self.wdgEditor.selectedItems():
            self.valueFilled.emit()
        else:
            self.valueReset.emit()


class LabelsTemplateFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(LabelsTemplateFieldWidget, self).__init__(field, parent)
        self.wdgEditor = LabelsSelectionWidget(field)
        _layout = vbox(self)
        _layout.addWidget(group(self.lblEmoji, self.lblName, spacer()))
        _layout.addWidget(self.wdgEditor)

        self.wdgEditor.selectionChanged.connect(self._selectionChanged)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setValue(value)

    def _selectionChanged(self):
        if self.wdgEditor.selectedItems():
            self.valueFilled.emit()
        else:
            self.valueReset.emit()


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
            if app_env.is_windows():
                emoji_size = 14
            else:
                emoji_size = 20

            self._lblEmoji.setFont(emoji_font(emoji_size))
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

    def __init__(self, fields: List[TemplateField], parent=None):
        super().__init__(parent)
        vbox(self)
        self._fields: Dict[TemplateField, FieldToggle] = {}

        for field in fields:
            wdg = FieldToggle(field)
            self._fields[field] = wdg
            self.layout().addWidget(wdg)
            wdg.toggle.toggled.connect(partial(self.toggled.emit, field))

    def toggle(self, field: TemplateField):
        self._fields[field].toggle.toggle()


class MultiLayerComplexTemplateWidgetBase(ComplexTemplateWidgetBase):
    VALUE_KEY: str = 'value'
    SECONDARY_KEY: str = 'secondary'

    def __init__(self, field: TemplateField, parent=None):
        super().__init__(field, parent)

        self._btnPrimary = SecondaryActionPushButton()
        self._btnPrimary.setText(self._primaryButtonText())
        self._btnPrimary.setIcon(IconRegistry.plus_icon('grey'))
        btn_popup_menu(self._btnPrimary, self._primaryMenu())
        vbox(self, 0, 2)
        self._editor = QWidget(self)
        self._editor.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._layout: QGridLayout = grid(self._editor)

        self.layout().addWidget(self._editor)
        self.layout().addWidget(wrap(self._btnPrimary, margin_left=5))
        # self._layout.addWidget(spacer(), 0, 2)

    @abstractmethod
    def _primaryFields(self) -> List[TemplateField]:
        pass

    def _primaryButtonText(self) -> str:
        return 'Add new item'

    def _primaryMenu(self) -> QMenu:
        fields = self._primaryFields()
        menu = QMenu()
        for field in fields:
            menu.addAction(action(field.name, slot=partial(self._addPrimaryField, field), parent=menu))

        return menu

    @abstractmethod
    def _secondaryFields(self, primary: TemplateField) -> List[TemplateField]:
        pass

    @abstractmethod
    def _secondaryRowDiff(self, primary: TemplateField, secondary: TemplateField) -> int:
        pass

    @overrides
    def setValue(self, value: Any):
        if value is None:
            return

        primary_fields = self._primaryFields()
        for k, v in value.items():
            primary = next((x for x in primary_fields if str(x.id) == k), None)
            if primary:
                self._addPrimaryField(primary)

    def _addPrimaryField(self, field: TemplateField):
        row = self._layout.rowCount()
        wdg = SmallTextTemplateFieldWidget(field)
        secondaryFields = self._secondaryFields(field)
        row += len(secondaryFields) // 2
        self._layout.addWidget(wdg, row, 0)

        btnSecondary = QToolButton()
        transparent(btnSecondary)
        pointy(btnSecondary)
        btnSecondary.setIcon(IconRegistry.plus_circle_icon('grey'))
        selector = FieldSelector(secondaryFields)
        btn_popup(btnSecondary, selector)
        selector.toggled.connect(partial(self._toggleSecondaryField, wdg))
        btnSecondary.installEventFilter(OpacityEventFilter(btnSecondary))

        self._layout.addWidget(wrap(btnSecondary, margin_top=20), row, 1, 1, 1, Qt.AlignmentFlag.AlignVCenter)

    def _toggleSecondaryField(self, primaryWdg: SmallTextTemplateFieldWidget, secondary: TemplateField, toggled: bool):
        primary = primaryWdg.field
        i = self._layout.indexOf(primaryWdg)
        primary_row = self._layout.getItemPosition(i)[0]
        secondaryFields = self._secondaryFields(primary)
        i = secondaryFields.index(secondary)
        row = primary_row - len(secondaryFields) // 2 + i

        if toggled:
            wdg = SmallTextTemplateFieldWidget(secondary)
            self._layout.addWidget(wdg, row, 2)
        else:
            item = self._layout.itemAtPosition(row, 2)
            self._layout.removeItem(item)
            if item.widget():
                gc(item.widget())


class GmcFieldWidget(MultiLayerComplexTemplateWidgetBase):

    def __init__(self, field: TemplateField, parent=None):
        super().__init__(field, parent)

        value = {str(goal_field.id): {self.VALUE_KEY: 'test', self.SECONDARY_KEY: ['']}}
        self.setValue(value)

    @property
    def wdgEditor(self):
        return self

    @overrides
    def _primaryButtonText(self) -> str:
        return 'Add new goal'

    @overrides
    def _primaryFields(self) -> List[TemplateField]:
        return [goal_field, internal_goal_field]

    @overrides
    def _secondaryFields(self, primary: TemplateField) -> List[TemplateField]:
        if primary.id == goal_field.id:
            return [stakes_field, conflict_field, motivation_field, internal_motivation_field, internal_conflict_field,
                    internal_stakes_field]
        else:
            return [internal_motivation_field, internal_conflict_field, internal_stakes_field]

    @overrides
    def _secondaryRowDiff(self, primary: TemplateField, secondary: TemplateField) -> int:
        return -1
