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
import pickle
from abc import abstractmethod
from functools import partial
from typing import Optional, List, Any, Dict, Set

import emoji
import qtanim
import qtawesome
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QModelIndex, QSize
from PyQt5.QtGui import QDropEvent, QIcon, QMouseEvent, QDragEnterEvent, QDragMoveEvent
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QWidget, QGridLayout, QLineEdit, QLayoutItem, \
    QToolButton, QLabel, QSpinBox, QComboBox, QButtonGroup, QSizePolicy, QVBoxLayout, \
    QSpacerItem, QListView, QPushButton
from overrides import overrides
from qthandy import spacer, btn_popup, hbox, vbox, bold, line, underline, transparent, margins, \
    decr_font

from src.main.python.plotlyst.core.domain import TemplateValue, Character
from src.main.python.plotlyst.core.help import enneagram_help, mbti_help
from src.main.python.plotlyst.core.template import TemplateField, TemplateFieldType, SelectionItem, \
    ProfileTemplate, ProfileElement, SelectionItemType, \
    enneagram_field, traits_field, HAlignment, VAlignment, mbti_field, \
    enneagram_choices
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.model.template import TemplateFieldSelectionModel, TraitsFieldItemsSelectionModel, \
    TraitsProxyModel
from src.main.python.plotlyst.view.common import emoji_font, pointy
from src.main.python.plotlyst.view.generated.field_text_selection_widget_ui import Ui_FieldTextSelectionWidget
from src.main.python.plotlyst.view.generated.trait_selection_widget_ui import Ui_TraitSelectionWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.button import SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.display import Subtitle, Emoji
from src.main.python.plotlyst.view.widget.input import AutoAdjustableTextEdit
from src.main.python.plotlyst.view.widget.labels import TraitLabel, LabelsEditorWidget


class _ProfileTemplateBase(QWidget):

    def __init__(self, profile: ProfileTemplate, editor_mode: bool = False, parent=None):
        super().__init__(parent)
        self._profile = profile
        self.layout = QVBoxLayout(self)
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFocusPolicy(Qt.NoFocus)
        self.scrollAreaWidgetContents = QWidget()
        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setSpacing(1)
        self.gridLayout.setContentsMargins(2, 0, 2, 0)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.layout.addWidget(self.scrollArea)

        self._spacer_item = QSpacerItem(20, 50, QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.widgets: List[TemplateWidgetBase] = []
        self._header_rows: List[int] = []
        self._initGrid(editor_mode)

    def _initGrid(self, editor_mode: bool):
        for el in self._profile.elements:
            widget = TemplateFieldWidgetFactory.widget(el.field, self)
            if el.margins:
                widget.setContentsMargins(el.margins.left, el.margins.top, el.margins.right, el.margins.bottom)
            self.widgets.append(widget)
            self.gridLayout.addWidget(widget, el.row, el.col, el.row_span, el.col_span,
                                      el.h_alignment.value | el.v_alignment.value)

            if isinstance(widget, HeaderTemplateDisplayWidget):
                self._header_rows.append(el.row)
                widget.collapsed.connect(partial(self._collapse, el.row))

        self._addSpacerToEnd()

    def _addSpacerToEnd(self):
        self.gridLayout.addItem(self._spacer_item,
                                self.gridLayout.rowCount(), 0)
        self.gridLayout.setRowStretch(self.gridLayout.rowCount() - 1, 1)

    def _collapse(self, row: int, collapsed: bool):
        last_row = self.gridLayout.rowCount() - 1
        for header_row in self._header_rows:
            if header_row > row:
                last_row = header_row
                break

        for i in range(row + 1, last_row):
            for j in range(0, 2):
                item = self.gridLayout.itemAtPosition(i, j)
                if item:
                    item.widget().setHidden(collapsed)


class _PlaceHolder(QFrame):
    def __init__(self):
        super(_PlaceHolder, self).__init__()
        layout = QHBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(2, 2, 1, 2)
        self.setLayout(layout)

        self.btn = QToolButton()
        self.btn.setIcon(qtawesome.icon('ei.plus-sign', color='lightgrey'))
        self.btn.setText('<Drop here>')
        self.btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.btn.setStyleSheet('''
                background-color: rgb(255, 255, 255);
                border: 0px;
                color: lightgrey;''')
        layout.addWidget(self.btn)


def is_placeholder(widget: QWidget) -> bool:
    return isinstance(widget, _PlaceHolder) or isinstance(widget.parent(), _PlaceHolder)


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
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

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
            self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

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
                self._wdgLabels.addLabel(TraitLabel(item.text, False))

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

            self.positiveProxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
            self.positiveProxy.setSourceModel(model)
            self.positiveProxy.setFilterKeyColumn(TemplateFieldSelectionModel.ColName)
            self.lstPositiveTraitsView.setModel(self.positiveProxy)
            self.filterPositive.textChanged.connect(self.positiveProxy.setFilterRegExp)

            self.negativeProxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
            self.negativeProxy.setSourceModel(model)
            self.negativeProxy.setFilterKeyColumn(TemplateFieldSelectionModel.ColName)
            self.lstNegativeTraitsView.setModel(self.negativeProxy)
            self.filterNegative.textChanged.connect(self.negativeProxy.setFilterRegExp)

            for lst in [self.lstPositiveTraitsView, self.lstNegativeTraitsView]:
                lst.setModelColumn(TemplateFieldSelectionModel.ColName)
                lst.setViewMode(QListView.IconMode)
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
            btn.setCursor(Qt.PointingHandCursor)
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


class TemplateWidgetBase(QFrame):
    def __init__(self, field: TemplateField, parent=None):
        super(TemplateWidgetBase, self).__init__(parent)
        self.field = field
        self.setProperty('mainFrame', True)

    def select(self):
        self.setStyleSheet('QFrame[mainFrame=true] {border: 2px dashed #0496ff;}')

    def deselect(self):
        self.setStyleSheet('')


class TemplateDisplayWidget(TemplateWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(TemplateDisplayWidget, self).__init__(field, parent)


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


class HeaderTemplateDisplayWidget(TemplateDisplayWidget):
    collapsed = pyqtSignal(bool)

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
        self.layout().addWidget(self.btnHeader, alignment=Qt.AlignLeft)

        self.btnHeader.clicked.connect(self._toggleCollapse)

    def _toggleCollapse(self, checked: bool):
        if checked:
            self.btnHeader.setIcon(IconRegistry.from_name('mdi.chevron-right'))
        else:
            self.btnHeader.setIcon(IconRegistry.from_name('mdi.chevron-down'))

        self.collapsed.emit(checked)


class LineTemplateDisplayWidget(TemplateDisplayWidget):
    def __init__(self, field: TemplateField, parent=None):
        super(LineTemplateDisplayWidget, self).__init__(field, parent)
        hbox(self)
        self.layout().addWidget(line())


class TemplateFieldWidgetBase(TemplateWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(TemplateFieldWidgetBase, self).__init__(field, parent)
        self.lblEmoji = QLabel(self)
        self.lblEmoji.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.lblName = QLabel(self)
        self.lblName.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.lblName.setText(self.field.name)

        if self.field.emoji:
            self.updateEmoji(emoji.emojize(self.field.emoji))
        else:
            self.lblEmoji.setHidden(True)

        if not field.show_label:
            self.lblName.setHidden(True)

    @overrides
    def setEnabled(self, enabled: bool):
        if not self.layout():
            return
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.widget():
                item.widget().setEnabled(enabled)

    def updateEmoji(self, emoji: str):
        if app_env.is_windows():
            emoji_size = 14
        else:
            emoji_size = 20

        self.lblEmoji.setFont(emoji_font(emoji_size))
        self.lblEmoji.setText(emoji)
        self.lblEmoji.setVisible(True)

    @abstractmethod
    def value(self) -> Any:
        pass

    @abstractmethod
    def setValue(self, value: Any):
        pass


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

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.text()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setText(value)


class SmallTextTemplateFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(SmallTextTemplateFieldWidget, self).__init__(field, parent)
        _layout = vbox(self, margin=1)
        self.wdgEditor = AutoAdjustableTextEdit(height=60)
        self.wdgEditor.setAcceptRichText(False)
        self.wdgEditor.setPlaceholderText(field.placeholder)

        _layout.addWidget(group(self.lblEmoji, self.lblName, spacer()))
        _layout.addWidget(self.wdgEditor)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.toPlainText()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setText(value)


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

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setValue(value)


class EnneagramFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(EnneagramFieldWidget, self).__init__(field, parent)
        self.wdgEditor = TextSelectionWidget(field, enneagram_help)
        _layout = vbox(self)
        _layout.addWidget(self.wdgEditor)

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

        decr_font(emojiDesire, 4)
        decr_font(self.lblDesire, 2)
        decr_font(emojiFear, 4)
        decr_font(self.lblFear, 2)

        self.wdgAttr = group(emojiDesire, self.lblDesire, emojiFear, self.lblFear, spacer())
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
            return

        if animated:
            qtanim.fade_in(self.wdgAttr)
        else:
            self.wdgAttr.setVisible(True)
        self.lblDesire.setText(new.meta['desire'])
        self.lblFear.setText(new.meta['fear'])


class CustomTemplateFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, editor: QWidget, parent=None, vertical: bool = True):
        super(CustomTemplateFieldWidget, self).__init__(field, parent)
        self.wdgEditor = editor
        _layout = vbox(self) if vertical else hbox(self)

        if vertical:
            _layout.addWidget(group(self.lblEmoji, self.lblName, spacer()))
        else:
            _layout.addWidget(self.lblEmoji)
            _layout.addWidget(self.lblName)
        _layout.addWidget(self.wdgEditor)

        if self.field.compact:
            _layout.addWidget(spacer(vertical=vertical))

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setValue(value)


class TemplateFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, editor: QWidget, parent=None):
        super(TemplateFieldWidget, self).__init__(field, parent)
        self._layout = hbox(self)
        self.wdgEditor = editor

        if self.field.type in [TemplateFieldType.LABELS, TemplateFieldType.SMALL_TEXT]:
            label_alignment = Qt.AlignTop
        else:
            label_alignment = Qt.AlignVCenter
        self._layout.addWidget(self.lblName, alignment=label_alignment)

        self._layout.addWidget(self.wdgEditor)

        if self.field.compact:
            self._layout.addWidget(spacer())

    @overrides
    def value(self) -> Any:
        if isinstance(self.wdgEditor, QComboBox):
            return self.wdgEditor.currentText()
        if isinstance(self.wdgEditor, (ButtonSelectionWidget, TextSelectionWidget, LabelsSelectionWidget)):
            return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        if isinstance(self.wdgEditor, QComboBox):
            self.wdgEditor.setCurrentText(value)
        if isinstance(self.wdgEditor, (ButtonSelectionWidget, TextSelectionWidget, LabelsSelectionWidget)):
            self.wdgEditor.setValue(value)


class TemplateFieldWidgetFactory:

    @staticmethod
    def widget(field: TemplateField, parent=None) -> TemplateWidgetBase:
        if field.type == TemplateFieldType.DISPLAY_SUBTITLE:
            return SubtitleTemplateDisplayWidget(field, parent)
        elif field.type == TemplateFieldType.DISPLAY_LABEL:
            return LabelTemplateDisplayWidget(field, parent)
        elif field.type == TemplateFieldType.DISPLAY_HEADER:
            return HeaderTemplateDisplayWidget(field, parent)
        elif field.type == TemplateFieldType.DISPLAY_LINE:
            return LineTemplateDisplayWidget(field, parent)

        if field.id == enneagram_field.id:
            return EnneagramFieldWidget(field, parent)
        elif field.id == mbti_field.id:
            return CustomTemplateFieldWidget(field, TextSelectionWidget(field, mbti_help), parent, vertical=False)
        elif field.id == traits_field.id:
            return CustomTemplateFieldWidget(field, TraitSelectionWidget(field, parent))
        elif field.type == TemplateFieldType.NUMERIC:
            return NumericTemplateFieldWidget(field, parent)
        elif field.type == TemplateFieldType.TEXT_SELECTION:
            widget = QComboBox()
            if not field.required:
                widget.addItem('')
            for item in field.selections:
                if item.type == SelectionItemType.CHOICE:
                    widget.addItem(_icon(item), item.text)
                if item.type == SelectionItemType.SEPARATOR:
                    widget.insertSeparator(widget.count())
        # elif field.type == TemplateFieldType.BUTTON_SELECTION:
        #     widget = ButtonSelectionWidget(field)
        elif field.type == TemplateFieldType.SMALL_TEXT:
            return SmallTextTemplateFieldWidget(field, parent)
        elif field.type == TemplateFieldType.TEXT:
            return LineTextTemplateFieldWidget(field, parent)
        elif field.type == TemplateFieldType.LABELS:
            return CustomTemplateFieldWidget(field, LabelsSelectionWidget(field), parent)
        else:
            raise ValueError('Unrecognized template field type %s', field.type)

        return TemplateFieldWidget(field, widget)


class ProfileTemplateEditor(_ProfileTemplateBase):
    MimeType: str = 'application/template-field'

    fieldSelected = pyqtSignal(TemplateField)
    placeholderSelected = pyqtSignal()
    fieldAdded = pyqtSignal(TemplateField)

    def __init__(self, profile: ProfileTemplate):
        super(ProfileTemplateEditor, self).__init__(profile, editor_mode=True)
        self.setAcceptDrops(True)
        self.setStyleSheet('QWidget {background-color: rgb(255, 255, 255);}')
        self._selected: Optional[TemplateFieldWidget] = None
        self._target_to_drop: Optional[QWidget] = None

        for w in self.widgets:
            w.setEnabled(False)
            w.setAcceptDrops(True)
            self._installEventFilter(w)

        self.gridLayout.removeItem(self._spacer_item)
        for row in range(max(6, self.gridLayout.rowCount() + 1)):
            for col in range(2):
                if not self.gridLayout.itemAtPosition(row, col):
                    self._addPlaceholder(row, col)

    def profile(self) -> ProfileTemplate:
        elements = []
        for i in range(self.gridLayout.count()):
            item = self.gridLayout.itemAt(i)
            if item and isinstance(item.widget(), TemplateFieldWidgetBase):
                pos = self.gridLayout.getItemPosition(i)
                item = self.gridLayout.itemAtPosition(pos[0], pos[1])
                if item.alignment() & Qt.AlignRight:
                    h_alignment = HAlignment.RIGHT
                elif item.alignment() & Qt.AlignLeft:
                    h_alignment = HAlignment.LEFT
                elif item.alignment() & Qt.AlignHCenter:
                    h_alignment = HAlignment.CENTER
                elif item.alignment() & Qt.AlignJustify:
                    h_alignment = HAlignment.JUSTIFY
                else:
                    h_alignment = HAlignment.DEFAULT

                if item.alignment() & Qt.AlignTop:
                    v_alignment = VAlignment.TOP
                elif item.alignment() & Qt.AlignBottom:
                    v_alignment = VAlignment.BOTTOM
                else:
                    v_alignment = VAlignment.CENTER

                elements.append(
                    ProfileElement(item.widget().field, row=pos[0], col=pos[1], row_span=pos[2], col_span=pos[3],
                                   h_alignment=h_alignment, v_alignment=v_alignment))

        self._profile.elements = elements
        return self._profile

    @overrides
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat(self.MimeType):
            event.accept()
        else:
            event.ignore()

    @overrides
    def dragMoveEvent(self, event: QDragMoveEvent):
        if not self._target_to_drop:
            event.ignore()
            return
        if is_placeholder(self._target_to_drop):
            event.accept()
        else:
            event.ignore()

    @overrides
    def dropEvent(self, event: QDropEvent):
        if not self._target_to_drop:
            event.ignore()
            return

        if isinstance(self._target_to_drop, _PlaceHolder):
            placeholder = self._target_to_drop
        elif isinstance(self._target_to_drop.parent(), _PlaceHolder):
            placeholder = self._target_to_drop.parent()
        else:
            event.ignore()
            return
        index = self.gridLayout.indexOf(placeholder)

        field: TemplateField = pickle.loads(event.mimeData().data(self.MimeType))
        widget_to_drop = TemplateFieldWidgetFactory.widget(field)
        widget_to_drop.setEnabled(False)
        pos = self.gridLayout.getItemPosition(index)
        item: QLayoutItem = self.gridLayout.takeAt(index)
        item.widget().deleteLater()
        self.gridLayout.addWidget(widget_to_drop, *pos)
        self._installEventFilter(widget_to_drop)

        self.widgets.append(widget_to_drop)

        self.fieldAdded.emit(field)
        self._select(widget_to_drop)

        if pos[0] == self.gridLayout.rowCount() - 1:
            self._addPlaceholder(pos[0] + 1, 0)
            self._addPlaceholder(pos[0] + 1, 1)
            self.gridLayout.update()

        event.accept()

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.MouseButtonRelease:
            if isinstance(watched, (QToolButton, QPushButton)):
                self._select(watched.parent())
            else:
                self._select(watched)
        elif event.type() == QEvent.DragEnter:
            self._target_to_drop = watched
            self.dragMoveEvent(event)
        elif event.type() == QEvent.Drop:
            self.dropEvent(event)
            self._target_to_drop = None
        return super().eventFilter(watched, event)

    def _select(self, widget: TemplateWidgetBase):
        if self._selected:
            self._selected.deselect()
        if is_placeholder(widget):
            self._selected = None
            self.placeholderSelected.emit()
            return
        self._selected = widget
        self._selected.select()
        self.fieldSelected.emit(self._selected.field)

    def removeSelected(self):
        if self._selected:
            index = self.gridLayout.indexOf(self._selected)
            pos = self.gridLayout.getItemPosition(index)
            self.gridLayout.removeWidget(self._selected)
            self._addPlaceholder(pos[0], pos[1])
            self.widgets.remove(self._selected)
            self._selected.deleteLater()
            self._selected = None

    def setShowLabelForSelected(self, enabled: bool):
        if self._selected:
            self._selected.lblName.setVisible(enabled)

    def updateLabelForSelected(self, text: str):
        if self._selected:
            self._selected.lblName.setText(text)

    def updateEmojiForSelected(self, text: str):
        if self._selected:
            self._selected.updateEmoji(emoji.emojize(text))

    def _installEventFilter(self, widget: TemplateWidgetBase):
        widget.installEventFilter(self)
        if isinstance(TemplateWidgetBase, TemplateFieldWidget) and isinstance(widget.wdgEditor, TextSelectionWidget):
            widget.wdgEditor.installEventFilter(self)

    def _addPlaceholder(self, row: int, col: int):
        _placeholder = _PlaceHolder()
        self.gridLayout.addWidget(_placeholder, row, col)
        _placeholder.setAcceptDrops(True)
        _placeholder.btn.setAcceptDrops(True)
        _placeholder.installEventFilter(self)
        _placeholder.btn.installEventFilter(self)


class ProfileTemplateView(_ProfileTemplateBase):
    def __init__(self, values: List[TemplateValue], profile: ProfileTemplate):
        super().__init__(profile)
        self.setProperty('mainFrame', True)
        self.setValues(values)

    def values(self) -> List[TemplateValue]:
        values: List[TemplateValue] = []
        for widget in self.widgets:
            if isinstance(widget, TemplateDisplayWidget):
                continue
            values.append(TemplateValue(id=widget.field.id, value=widget.value()))

        return values

    def setValues(self, values: List[TemplateValue]):
        ids = {}
        for value in values:
            ids[str(value.id)] = value.value

        for widget in self.widgets:
            if isinstance(widget, TemplateDisplayWidget):
                continue
            if str(widget.field.id) in ids.keys():
                widget.setValue(ids[str(widget.field.id)])


class CharacterProfileTemplateView(ProfileTemplateView):
    def __init__(self, character: Character, profile: ProfileTemplate):
        super().__init__(character.template_values, profile)
        self.character = character
        self._enneagram_widget: Optional[TextSelectionWidget] = None
        self._traits_widget: Optional[TraitSelectionWidget] = None
        self._goals_widget: Optional[TemplateFieldWidget] = None
        for widget in self.widgets:
            if widget.field.id == enneagram_field.id:
                self._enneagram_widget = widget.wdgEditor
            elif widget.field.id == traits_field.id:
                self._traits_widget = widget.wdgEditor

        if self._enneagram_widget:
            self._enneagram_widget.selectionChanged.connect(self._enneagram_changed)

    def _enneagram_changed(self, previous: Optional[SelectionItem], current: SelectionItem):
        if self._traits_widget:
            traits: List[str] = self._traits_widget.value()
            if previous:
                for pos_trait in previous.meta['positive']:
                    if pos_trait in traits:
                        traits.remove(pos_trait)
                for neg_trait in previous.meta['negative']:
                    if neg_trait in traits:
                        traits.remove(neg_trait)
            for pos_trait in current.meta['positive']:
                if pos_trait not in traits:
                    traits.append(pos_trait)
            for neg_trait in current.meta['negative']:
                if neg_trait not in traits:
                    traits.append(neg_trait)
            self._traits_widget.setValue(traits)
