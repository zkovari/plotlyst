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
import copy
from functools import partial
from typing import Optional, List, Any, Dict, Set, Tuple

import emoji
import qtanim
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QModelIndex, QSize
from PyQt6.QtGui import QMouseEvent, QIcon, QWheelEvent
from PyQt6.QtWidgets import QHBoxLayout, QWidget, QLineEdit, QToolButton, QLabel, \
    QSpinBox, QButtonGroup, QSizePolicy, QListView, QVBoxLayout, QSlider, QGridLayout
from overrides import overrides
from qthandy import spacer, hbox, vbox, bold, line, underline, transparent, margins, \
    decr_font, retain_when_hidden, vspacer, gc, sp, pointy, grid
from qthandy.filter import OpacityEventFilter, VisibilityToggleEventFilter
from qtmenu import MenuWidget, ActionTooltipDisplayMode

from src.main.python.plotlyst.core.help import enneagram_help, mbti_help, mbti_keywords
from src.main.python.plotlyst.core.template import TemplateField, SelectionItem, \
    enneagram_choices, goal_field, internal_goal_field, stakes_field, conflict_field, motivation_field, \
    internal_motivation_field, internal_conflict_field, internal_stakes_field, wound_field, trigger_field, fear_field, \
    healing_field, methods_field, misbelief_field, ghost_field, demon_field, mbti_choices, love_style_choices, \
    work_style_choices, flaw_placeholder_field, flaw_relation_field, flaw_manifestation_field, flaw_coping_field, \
    flaw_triggers_field, flaw_goals_field, flaw_growth_field, flaw_deterioration_field
from src.main.python.plotlyst.model.template import TemplateFieldSelectionModel, TraitsFieldItemsSelectionModel, \
    TraitsProxyModel
from src.main.python.plotlyst.view.common import wrap, emoji_font, insert_before_the_end, action, label
from src.main.python.plotlyst.view.generated.trait_selection_widget_ui import Ui_TraitSelectionWidget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.style.slider import apply_slider_color
from src.main.python.plotlyst.view.widget.button import SecondaryActionPushButton, CollapseButton
from src.main.python.plotlyst.view.widget.character.editor import EnneagramSelector, MbtiSelector, LoveStyleSelector, \
    DiscSelector
from src.main.python.plotlyst.view.widget.display import Subtitle, Emoji, Icon, dash_icon
from src.main.python.plotlyst.view.widget.input import AutoAdjustableTextEdit, Toggle, TextInputDialog
from src.main.python.plotlyst.view.widget.labels import TraitLabel, LabelsEditorWidget
from src.main.python.plotlyst.view.widget.progress import CircularProgressBar
from src.main.python.plotlyst.view.widget.template.base import TemplateDisplayWidget, TemplateFieldWidgetBase, \
    TemplateWidgetBase, ComplexTemplateWidgetBase, EditableTemplateWidget


def _icon(item: SelectionItem) -> QIcon:
    if item.icon:
        return IconRegistry.from_name(item.icon, item.icon_color)
    else:
        return QIcon('')


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
        hbox(self, margin=1, spacing=0)
        self.btnHeader = CollapseButton(Qt.Edge.BottomEdge, Qt.Edge.RightEdge)
        self.btnHeader.setIconSize(QSize(16, 16))
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
        self.progressStatuses: Dict[TemplateWidgetBase, float] = {}

        self.btnHeader.toggled.connect(self._toggleCollapse)

    def attachWidget(self, widget: TemplateWidgetBase):
        self.children.append(widget)
        if not widget.field.type.is_display():
            self.progressStatuses[widget] = False
        widget.valueFilled.connect(partial(self._valueFilled, widget))
        widget.valueReset.connect(partial(self._valueReset, widget))

    def updateProgress(self):
        self.progress.setMaxValue(len(self.progressStatuses.keys()))
        self.progress.update()

    def collapse(self, collapsed: bool):
        self.btnHeader.setChecked(collapsed)

    @overrides
    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        if self._toggle and self.progress.value() == 0:
            self._toggle.setVisible(True)

    @overrides
    def leaveEvent(self, a0: QEvent) -> None:
        if self._toggle and self._toggle.isChecked():
            self._toggle.setHidden(True)

    def _toggleCollapse(self, checked: bool):
        for wdg in self.children:
            wdg.setHidden(checked)

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

        self._toggle.setVisible(True)

    def _valueFilled(self, widget: TemplateWidgetBase, value: float):
        if self.progressStatuses[widget] == value:
            return

        self.progressStatuses[widget] = value
        self.progress.setValue(sum(self.progressStatuses.values()))

    def _valueReset(self, widget: TemplateWidgetBase):
        if not self.progressStatuses[widget]:
            return

        self.progressStatuses[widget] = 0
        self.progress.setValue(sum(self.progressStatuses.values()))


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
            self.valueFilled.emit(1)
        else:
            self.valueReset.emit()


class SmallTextTemplateFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None, minHeight: int = 60):
        super(SmallTextTemplateFieldWidget, self).__init__(field, parent)
        _layout = vbox(self, margin=self._boxMargin, spacing=self._boxSpacing)
        self.wdgEditor = AutoAdjustableTextEdit(height=minHeight)
        self.wdgEditor.setProperty('white-bg', True)
        self.wdgEditor.setProperty('rounded', True)
        self.wdgEditor.setAcceptRichText(False)
        self.wdgEditor.setTabChangesFocus(True)
        self.wdgEditor.setPlaceholderText(field.placeholder)
        self.wdgEditor.setToolTip(field.description if field.description else field.placeholder)
        self.setMaximumWidth(600)

        self._filledBefore: bool = False

        # self.btnNotes = QToolButton()

        self.wdgTop = group(self.lblEmoji, self.lblName, spacer())
        _layout.addWidget(self.wdgTop)
        _layout.addWidget(self.wdgEditor)

        self.wdgEditor.textChanged.connect(self._textChanged)
        # if field.has_notes:
        #     self.btnNotes.setIcon(IconRegistry.from_name('mdi6.note-plus-outline'))
        #     pointy(self.btnNotes)
        #     transparent(self.btnNotes)
        #     translucent(self.btnNotes)
        #     self._notesEditor = EnhancedTextEdit()
        #     self._notesEditor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        #     self._notesEditor.setMinimumSize(400, 300)
        #     self._notesEditor.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
        #     self._notesEditor.setPlaceholderText(f'Add notes to {field.name}')
        #     self._notesEditor.setViewportMargins(5, 5, 5, 5)
        #     menu = btn_popup(self.btnNotes, self._notesEditor)
        #     menu.aboutToShow.connect(self._notesEditor.setFocus)
        #     self.installEventFilter(VisibilityToggleEventFilter(self.btnNotes, self))
        #     retain_when_hidden(self.btnNotes)
        # else:
        #     self.btnNotes.setHidden(True)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.toPlainText()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setText(value)

    def _textChanged(self):
        if self.wdgEditor.toPlainText() and not self._filledBefore:
            self.valueFilled.emit(1)
            self._filledBefore = True
        elif not self.wdgEditor.toPlainText():
            self.valueReset.emit()
            self._filledBefore = False


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
            self.valueFilled.emit(1)
        else:
            self.valueReset.emit()


class BarSlider(QSlider):
    @overrides
    def wheelEvent(self, event: QWheelEvent) -> None:
        event.ignore()


class BarTemplateFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(BarTemplateFieldWidget, self).__init__(field, parent)
        _layout = vbox(self)
        self.wdgEditor = BarSlider(Qt.Orientation.Horizontal)
        pointy(self.wdgEditor)
        self.wdgEditor.setPageStep(5)
        self.setMaximumWidth(600)

        self.wdgEditor.setMinimum(field.min_value)
        self.wdgEditor.setMaximum(field.max_value)
        if field.color:
            apply_slider_color(self.wdgEditor, field.color)

        _layout.addWidget(group(self.lblEmoji, self.lblName, spacer()))
        if self.field.compact:
            editor = group(self.wdgEditor, spacer())
            margins(editor, left=5)
            _layout.addWidget(editor)
        else:
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


class EnneagramFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(EnneagramFieldWidget, self).__init__(field, parent)
        self.wdgEditor = EnneagramSelector()
        self._defaultTooltip: str = 'Select Enneagram personality'
        _layout = vbox(self)
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

        decr_font(emojiDesire, 2)
        decr_font(self.lblDesire)
        decr_font(emojiFear, 2)
        decr_font(self.lblFear)

        self.wdgAttr = group(
            group(dash_icon(), emojiDesire, self.lblDesire, spacer()),
            group(dash_icon(), emojiFear, self.lblFear, spacer()),
            vertical=False)
        margins(self.wdgAttr, left=10)
        _layout.addWidget(self.wdgAttr)
        self.wdgAttr.setHidden(True)

        if self.field.compact:
            _layout.addWidget(spacer())

        self.wdgEditor.selected.connect(self._selectionChanged)
        self.wdgEditor.ignored.connect(self._ignored)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setValue(value)
        enneagram = enneagram_choices.get(value)
        if enneagram:
            # self.wdgEditor.setToolTip(enneagram_help[value])
            self._selectionChanged(enneagram)
        elif value is None:
            self._ignored()
        else:
            self.wdgEditor.setToolTip(self._defaultTooltip)

    def _selectionChanged(self, item: SelectionItem):
        self.lblDesire.setText(item.meta['desire'])
        self.lblFear.setText(item.meta['fear'])
        self.wdgEditor.setToolTip(enneagram_help[item.text])
        if self.isVisible():
            qtanim.fade_in(self.wdgAttr)
        else:
            self.wdgAttr.setVisible(True)

        self.valueFilled.emit(1)

    def _ignored(self):
        self.wdgEditor.setToolTip('Enneagram field is ignored for this character')
        self.lblDesire.setText('')
        self.lblFear.setText('')
        self.wdgAttr.setHidden(True)
        self.valueFilled.emit(1)


class MbtiFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(MbtiFieldWidget, self).__init__(field, parent)
        self.wdgEditor = MbtiSelector()
        self._defaultTooltip: str = 'Select MBTI personality type'
        self.wdgEditor.setToolTip(self._defaultTooltip)

        _layout = vbox(self)
        _layout.addWidget(self.wdgEditor)

        self.lblKeywords = label(wordWrap=True)
        decr_font(self.lblKeywords)

        self.wdgAttr = group(dash_icon(), self.lblKeywords, spacer())
        margins(self.wdgAttr, left=10)
        _layout.addWidget(self.wdgAttr)
        self.wdgAttr.setHidden(True)

        if self.field.compact:
            _layout.addWidget(spacer())

        self.wdgEditor.selected.connect(self._selectionChanged)
        self.wdgEditor.ignored.connect(self._ignored)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setValue(value)
        if value:
            mbti = mbti_choices[value]
            self._selectionChanged(mbti)
        elif value is None:
            self._ignored()
        else:
            self.wdgEditor.setToolTip(self._defaultTooltip)

    def _selectionChanged(self, item: SelectionItem):
        self.lblKeywords.setText(mbti_keywords.get(item.text, ''))
        if self.isVisible():
            qtanim.fade_in(self.wdgAttr)
        else:
            self.wdgAttr.setVisible(True)

        self.wdgEditor.setToolTip(mbti_help[item.text])
        self.valueFilled.emit(1)

    def _ignored(self):
        self.wdgEditor.setToolTip('MBTI field is ignored for this character')
        self.wdgAttr.setHidden(True)
        self.valueFilled.emit(1)


class LoveStyleFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super().__init__(field, parent)
        self.wdgEditor = LoveStyleSelector()
        self._defaultTooltip: str = 'Select love style'
        _layout = vbox(self)
        _layout.addWidget(self.wdgEditor, alignment=Qt.AlignmentFlag.AlignLeft)

        self.wdgEditor.selected.connect(self._selectionChanged)
        self.wdgEditor.ignored.connect(self._ignored)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setValue(value)
        if value:
            mbti = love_style_choices[value]
            self._selectionChanged(mbti)
        elif value is None:
            self._ignored()
        else:
            self.wdgEditor.setToolTip(self._defaultTooltip)

    def _selectionChanged(self, item: SelectionItem):
        pass

    def _ignored(self):
        self.wdgEditor.setToolTip('Love style field is ignored for this character')
        self.valueFilled.emit(1)


class WorkStyleFieldWidget(TemplateFieldWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super().__init__(field, parent)
        self.wdgEditor = DiscSelector()
        self._defaultTooltip: str = 'Select work style'
        _layout = vbox(self)
        _layout.addWidget(self.wdgEditor, alignment=Qt.AlignmentFlag.AlignLeft)

        self.wdgEditor.selected.connect(self._selectionChanged)
        self.wdgEditor.ignored.connect(self._ignored)

    @overrides
    def value(self) -> Any:
        return self.wdgEditor.value()

    @overrides
    def setValue(self, value: Any):
        self.wdgEditor.setValue(value)
        if value:
            mbti = work_style_choices[value]
            self._selectionChanged(mbti)
        elif value is None:
            self._ignored()
        else:
            self.wdgEditor.setToolTip(self._defaultTooltip)

    def _selectionChanged(self, item: SelectionItem):
        pass

    def _ignored(self):
        self.wdgEditor.setToolTip('Work style field is ignored for this character')
        self.valueFilled.emit(1)


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
            self.valueFilled.emit(1)
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
            self.valueFilled.emit(1)
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

    def __init__(self, field: TemplateField, secondaryFields: List[TemplateField], parent=None):
        super().__init__(parent)
        self._field = field
        self._secondaryFields = secondaryFields
        self._secondaryFieldWidgets: Dict[TemplateField, Optional[SmallTextTemplateFieldWidget]] = {}
        for sf in secondaryFields:
            self._secondaryFieldWidgets[sf] = None
        vbox(self, 0, 2)
        self._primaryWdg = SmallTextTemplateFieldWidget(field)
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
            wdg = SmallTextTemplateFieldWidget(secondary, minHeight=40)
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

    def _clickSecondaryField(self):
        self.valueChanged.emit()


class MultiLayerComplexTemplateWidgetBase(ComplexTemplateWidgetBase):
    ID_KEY: str = 'id'
    VALUE_KEY: str = 'value'
    SECONDARY_KEY: str = 'secondary'
    ALIAS_KEY = 'alias'

    def __init__(self, field: TemplateField, parent=None):
        super().__init__(field, parent)
        self._hasAlias = False
        self._primaryWidgets: List[_PrimaryFieldWidget] = []

        self._btnPrimary = SecondaryActionPushButton()
        self._btnPrimary.setText(self._primaryButtonText())
        self._btnPrimary.setIcon(IconRegistry.plus_icon('grey'))
        decr_font(self._btnPrimary)
        fields = self._primaryFields()
        self._menu = MenuWidget(self._btnPrimary)
        self._menu.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
        for field in fields:
            self._menu.addAction(
                action(field.name, tooltip=field.description, slot=partial(self._addPrimaryField, field),
                       parent=self._menu))
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._layout: QVBoxLayout = vbox(self, 0, 5)

        self.layout().addWidget(wrap(self._btnPrimary, margin_left=5))
        self._layout.addWidget(vspacer())

    @overrides
    def value(self) -> Any:
        def secondaryValues(primaryWdg: _PrimaryFieldWidget):
            values = []
            for field in primaryWdg.secondaryFields():
                s_id, value_ = field
                values.append({self.ID_KEY: s_id, self.VALUE_KEY: value_})
            return values

        value = {}
        for i, primary_wdg in enumerate(self._primaryWidgets):
            sid = str(primary_wdg.field().id)
            sid += f'&{i}'
            if self._hasAlias:
                sid += f'&{primary_wdg.field().name}'
            value[sid] = {self.VALUE_KEY: primary_wdg.value(),
                          self.SECONDARY_KEY: secondaryValues(primary_wdg)}
            if self._hasAlias:
                value[sid][self.ALIAS_KEY] = primary_wdg.field().name

        return value

    @overrides
    def setValue(self, value: Any):
        if value is None:
            return
        if isinstance(value, str):
            return

        primary_fields = self._primaryFields()
        for k, v in value.items():
            k = k.split('&')[0]
            primary = next((x for x in primary_fields if str(x.id) == k), None)
            if primary is None:
                continue
            if self._hasAlias and self.ALIAS_KEY in v.keys():
                primary = copy.deepcopy(primary)
                primary.name = v[self.ALIAS_KEY]
            wdg = self._addPrimaryField(primary)
            wdg.setValue(v[self.VALUE_KEY])

            secondary_fields = self._secondaryFields(primary)
            for secondary in v[self.SECONDARY_KEY]:
                secondary_field = next((x for x in secondary_fields if str(x.id) == secondary[self.ID_KEY]), None)
                if secondary_field:
                    wdg.setSecondaryField(secondary_field, secondary[self.VALUE_KEY])

        self._valueChanged()

    def _primaryFields(self) -> List[TemplateField]:
        return []

    def _primaryButtonText(self) -> str:
        return 'Add new item'

    def _secondaryFields(self, primary: TemplateField) -> List[TemplateField]:
        return []

    def _addPrimaryField(self, field: TemplateField) -> _PrimaryFieldWidget:
        wdg = _PrimaryFieldWidget(field, self._secondaryFields(field))
        self._primaryWidgets.append(wdg)
        wdg.removed.connect(partial(self._removePrimaryField, wdg))
        wdg.renamed.connect(partial(self._renamePrimaryField, wdg))
        wdg.valueChanged.connect(self._valueChanged)
        if self._layout.count() > 2:
            self._layout.insertWidget(self._layout.count() - 2, line())
        self._layout.insertWidget(self._layout.count() - 2, wdg)

        return wdg

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


class FlawsFieldWidget(MultiLayerComplexTemplateWidgetBase):

    def __init__(self, field: TemplateField, parent=None):
        super().__init__(field, parent)
        self._hasAlias = True
        self._menu.clear()
        self._menu.addAction(
            action('Add a new character flaw...', icon=IconRegistry.from_name('mdi.virus'),
                   tooltip='A flaw can deepen the character, provide complexity, and may even impact the plot',
                   slot=self._addNew))

    @property
    def wdgEditor(self):
        return self

    @overrides
    def _primaryButtonText(self) -> str:
        return 'Add new flaw'

    @overrides
    def _primaryFields(self) -> List[TemplateField]:
        return [flaw_placeholder_field]

    @overrides
    def _secondaryFields(self, primary: TemplateField) -> List[TemplateField]:
        return [flaw_triggers_field, flaw_coping_field, flaw_manifestation_field, flaw_relation_field, flaw_goals_field,
                flaw_growth_field, flaw_deterioration_field]

    def _addNew(self):
        flaw = TextInputDialog.edit('Define a character flaw', 'Name of the flaw')
        if flaw:
            field = copy.deepcopy(flaw_placeholder_field)
            field.name = flaw
            self._addPrimaryField(field)

    @overrides
    def _renamePrimaryField(self, wdg: _PrimaryFieldWidget):
        flaw = wdg.field()
        flaw_name = TextInputDialog.edit('Rename character flaw', 'Name of the flaw', flaw.name)
        if flaw_name:
            flaw.name = flaw_name
            wdg.refresh()


class GmcFieldWidget(MultiLayerComplexTemplateWidgetBase):

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
            return [stakes_field, conflict_field, motivation_field, methods_field, internal_motivation_field,
                    internal_conflict_field,
                    internal_stakes_field]
        else:
            return [methods_field, internal_motivation_field, internal_conflict_field, internal_stakes_field]


class BaggageFieldWidget(MultiLayerComplexTemplateWidgetBase):
    @property
    def wdgEditor(self):
        return self

    @overrides
    def _primaryButtonText(self) -> str:
        return 'Add new baggage'

    @overrides
    def _primaryFields(self) -> List[TemplateField]:
        return [wound_field, ghost_field, demon_field]

    @overrides
    def _secondaryFields(self, primary: TemplateField) -> List[TemplateField]:
        if primary.id == wound_field.id:
            return [fear_field, misbelief_field, trigger_field, healing_field]
        return []


class StrengthsWeaknessesTableRow(QWidget):
    def __init__(self, attribute: str, parent=None):
        super().__init__(parent)
        hbox(self)
        self.lblAttribute = label(attribute)
        self.layout().addWidget(self.lblAttribute)


class StrengthsWeaknessesFieldWidget(EditableTemplateWidget):
    def __init__(self, field: TemplateField, parent=None):
        super().__init__(field, parent)
        self._rows: List[StrengthsWeaknessesTableRow] = []

        self._layout: QGridLayout = grid(self, 0, 5, 2)

        self.lblStrength = label('Strength')
        self.lblWeakness = label('Weakness')
        self._layout.addWidget(self.lblStrength, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self.lblWeakness, 0, 2, alignment=Qt.AlignmentFlag.AlignCenter)

        self._btnPrimary = SecondaryActionPushButton()
        self._btnPrimary.setText('Add new attribute')
        self._btnPrimary.setIcon(IconRegistry.plus_icon('grey'))
        self._btnPrimary.clicked.connect(self._addNewAttribute)
        decr_font(self._btnPrimary)


        self._layout.addWidget(wrap(self._btnPrimary, margin_left=5), 1, 0)

    @overrides
    def value(self) -> Any:
        pass

    @overrides
    def setValue(self, value: Any):
        if value is None:
            return
        if isinstance(value, str):
            return

        for item in value:
            pass

    def _addNewAttribute(self):
        attribute = TextInputDialog.edit('Define attribute',
                                         'Name an attribute that is a potential weakness, strength, or both')
        if attribute:
            wdg = StrengthsWeaknessesTableRow(attribute)
            self._rows.append(wdg)
            # wdg.removed.connect(partial(self._removePrimaryField, wdg))
            # wdg.renamed.connect(partial(self._renamePrimaryField, wdg))
            # wdg.valueChanged.connect(self._valueChanged)
            insert_before_the_end(self._layout, wdg)
            self._layout.addWidget(wdg, self._layout.rowCount() - 1, )

            # return wdg
