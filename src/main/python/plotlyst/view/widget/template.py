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
from typing import Optional, List, Any, Dict

import emoji
import qtawesome
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal, QByteArray, QBuffer, QIODevice, QObject, QEvent
from PyQt5.QtGui import QDropEvent, QIcon, QMouseEvent, QDragEnterEvent, QImageReader, QImage, QDragMoveEvent
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QWidget, QGridLayout, QLineEdit, QLayoutItem, \
    QToolButton, QLabel, QSpinBox, QComboBox, QButtonGroup, QFileDialog, QMessageBox, QSizePolicy, QVBoxLayout, \
    QSpacerItem, QTextEdit, QWidgetAction, QMenu, QListView, QPushButton
from fbs_runtime import platform
from overrides import overrides

from src.main.python.plotlyst.core.domain import TemplateField, TemplateFieldType, SelectionItem, \
    ProfileTemplate, TemplateValue, ProfileElement, name_field, Character, avatar_field, SelectionItemType, \
    enneagram_field, traits_field, desire_field, fear_field
from src.main.python.plotlyst.core.help import enneagram_help
from src.main.python.plotlyst.model.template import TemplateFieldSelectionModel, TraitsFieldItemsSelectionModel
from src.main.python.plotlyst.view.common import emoji_font, spacer_widget, ask_confirmation
from src.main.python.plotlyst.view.generated.avatar_widget_ui import Ui_AvatarWidget
from src.main.python.plotlyst.view.generated.field_text_selection_widget_ui import Ui_FieldTextSelectionWidget
from src.main.python.plotlyst.view.icons import avatars, IconRegistry, set_avatar
from src.main.python.plotlyst.view.widget.labels import TraitLabel, LabelsWidget


class _ProfileTemplateBase(QWidget):

    def __init__(self, profile: ProfileTemplate, parent=None):
        super().__init__(parent)
        self._profile = profile
        self.layout = QVBoxLayout(self)
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFocusPolicy(Qt.NoFocus)
        self.scrollAreaWidgetContents = QWidget()
        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setContentsMargins(2, 0, 2, 0)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.layout.addWidget(self.scrollArea)

        self.widgets: List[TemplateFieldWidget] = []
        self._initGrid()

    def _initGrid(self):
        for el in self._profile.elements:
            widget = TemplateFieldWidget(el.field)
            self.widgets.append(widget)
            self.gridLayout.addWidget(widget, el.row, el.col, el.row_span, el.col_span,
                                      el.h_alignment.value | el.v_alignment.value)

        self.gridLayout.addItem(QSpacerItem(20, 50, QSizePolicy.Preferred, QSizePolicy.Expanding),
                                self.gridLayout.rowCount(), 0)
        self.gridLayout.setRowStretch(self.gridLayout.rowCount() - 1, 1)


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


class AvatarWidget(QWidget, Ui_AvatarWidget):

    def __init__(self, field: TemplateField, parent=None):
        super(AvatarWidget, self).__init__(parent)
        self.setupUi(self)
        self.field = field
        self.character: Optional[Character] = None
        self.btnUploadAvatar.setIcon(IconRegistry.upload_icon())
        self.btnUploadAvatar.clicked.connect(self._upload_avatar)
        self.avatarUpdated: bool = False
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

    def setCharacter(self, character: Character):
        self.character = character
        set_avatar(self.lblAvatar, self.character)

    def _upload_avatar(self):
        filename: str = QFileDialog.getOpenFileName(None, 'Choose an image', '', 'Images (*.png *.jpg *jpeg)')
        if not filename:
            return
        reader = QImageReader(filename[0])
        reader.setAutoTransform(True)
        image: QImage = reader.read()
        if image is None:
            QMessageBox.warning(self.widget, 'Error while uploading image', 'Could not upload image')
            return
        array = QByteArray()
        buffer = QBuffer(array)
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, 'PNG')
        self.character.avatar = array

        avatars.update(self.character)
        set_avatar(self.lblAvatar, self.character)

        self.avatarUpdated = True


class TextSelectionWidget(QToolButton):
    placeholder_text: str = 'Select...'
    selectionChanged = pyqtSignal(object, object)

    def __init__(self, field: TemplateField, help: Dict[Any, str], parent=None):
        super(TextSelectionWidget, self).__init__(parent)
        self.field = field

        self.setPopupMode(QToolButton.InstantPopup)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setText(self.placeholder_text)
        menu = QMenu(self)
        action = QWidgetAction(menu)
        self._popup = self.Popup(self.field, help)
        action.setDefaultWidget(self._popup)
        menu.addAction(action)
        self.setMenu(menu)

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
            self.setIcon(IconRegistry.from_name(self._selected.icon, self._selected.icon_color))
        else:
            self.setText(self.placeholder_text)
            self.setIcon(IconRegistry.empty_icon())

    def _selection_changed(self, item: SelectionItem):
        self.menu().hide()
        previous = self._selected
        self.setValue(item.text)
        self.selectionChanged.emit(previous, self._selected)

    class Popup(QFrame, Ui_FieldTextSelectionWidget):
        selected = pyqtSignal(SelectionItem)

        def __init__(self, field: TemplateField, help: Dict[Any, str], parent=None):
            super().__init__(parent)
            self.setupUi(self)
            self.setMaximumHeight(350)
            self.setMinimumWidth(400)
            self.setMinimumHeight(350)

            self.field = field
            self.help = help

            self.model = TemplateFieldSelectionModel(self.field)
            self.tblItems.setModel(self.model)
            self.tblItems.setColumnWidth(TemplateFieldSelectionModel.ColIcon, 26)

            self.btnSelect.setIcon(IconRegistry.ok_icon('white'))
            self.tblItems.selectionModel().selectionChanged.connect(self._selection_changed)

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


class LabelsSelectionWidget(QFrame):

    def __init__(self, field: TemplateField, parent=None):
        super(LabelsSelectionWidget, self).__init__(parent)
        self.field = field
        self.setLineWidth(1)
        self.setFrameShape(QFrame.Box)
        self.setStyleSheet('LabelsSelectionWidget {background: white;}')
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(1, 1, 1, 1)

        self._labels_index = {}
        for item in self.field.selections:
            self._labels_index[item.text] = item

        self._btnEdit = QToolButton()
        self._btnEdit.setIcon(IconRegistry.plus_edit_icon())
        self._lstTraitsView = QListView()
        self._lstTraitsView.setMaximumHeight(300)
        self._lstTraitsView.setMaximumWidth(300)
        self._lstTraitsView.setMinimumWidth(300)
        self._lstTraitsView.setMinimumHeight(300)
        self._model = TraitsFieldItemsSelectionModel(self.field)
        self._model.setCheckable(True, TemplateFieldSelectionModel.ColName)
        self._lstTraitsView.setModel(self._model)
        self._lstTraitsView.setModelColumn(TemplateFieldSelectionModel.ColName)
        self._lstTraitsView.setViewMode(QListView.IconMode)

        self._model.selection_changed.connect(self._selection_changed)

        menu = QMenu(self._btnEdit)
        action = QWidgetAction(menu)
        action.setDefaultWidget(self._lstTraitsView)
        menu.addAction(action)
        self._btnEdit.setMenu(menu)
        self._btnEdit.setPopupMode(QToolButton.InstantPopup)
        self.layout().addWidget(self._btnEdit)

        self._wdgLabels = LabelsWidget()
        self._wdgLabels.setStyleSheet('LabelsWidget {border: 1px solid black;}')
        self._wdgLabels.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.layout().addWidget(self._wdgLabels)

    def value(self) -> List[str]:
        return [x.text for x in self._model.selections()]

    def setValue(self, values: List[str]):
        self._model.uncheckAll()
        for v in values:
            item = self._labels_index.get(v)
            if item:
                self._model.checkItem(item)
        self._model.modelReset.emit()
        self._selection_changed()

    def _selection_changed(self):
        self._wdgLabels.clear()
        for item in self._model.selections():
            if item.meta.get('positive', True):
                self._wdgLabels.addLabel(TraitLabel(item.text))
        for item in self._model.selections():
            if not item.meta.get('positive', True):
                self._wdgLabels.addLabel(TraitLabel(item.text, False))


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


class TemplateFieldWidget(QFrame):
    def __init__(self, field: TemplateField, parent=None):
        super(TemplateFieldWidget, self).__init__(parent)
        self.field = field
        self.layout = QHBoxLayout()
        self.setProperty('mainFrame', True)

        self.setLayout(self.layout)

        if self.field.emoji:
            if platform.is_windows():
                emoji_size = 14
            else:
                emoji_size = 20
            self.lblEmoji = QLabel()
            self.lblEmoji.setFont(emoji_font(emoji_size))
            self.lblEmoji.setText(emoji.emojize(self.field.emoji))
            self.layout.addWidget(self.lblEmoji, alignment=Qt.AlignTop)

        self.lblName = QLabel()
        self.lblName.setText(self.field.name)
        self.layout.addWidget(self.lblName)

        if not field.show_label:
            self.lblName.setHidden(True)

        self.wdgEditor = self._fieldWidget()
        self.layout.addWidget(self.wdgEditor)

        if self.field.compact:
            self.layout.addWidget(spacer_widget())

        self.layout.setSpacing(4)
        self.layout.setContentsMargins(2, 2, 1, 2)

    @overrides
    def setEnabled(self, enabled: bool):
        self.wdgEditor.setEnabled(enabled)

    def select(self):
        self.setStyleSheet('QFrame[mainFrame=true] {border: 2px dashed #0496ff;}')

    def deselect(self):
        self.setStyleSheet('')

    def value(self) -> Any:
        if isinstance(self.wdgEditor, QSpinBox):
            return self.wdgEditor.value()
        if isinstance(self.wdgEditor, QLineEdit):
            return self.wdgEditor.text()
        if isinstance(self.wdgEditor, QTextEdit):
            return self.wdgEditor.toPlainText()
        if isinstance(self.wdgEditor, QComboBox):
            return self.wdgEditor.currentText()
        if isinstance(self.wdgEditor, (ButtonSelectionWidget, TextSelectionWidget, LabelsSelectionWidget)):
            return self.wdgEditor.value()

    def setValue(self, value: Any):
        if isinstance(self.wdgEditor, QSpinBox):
            self.wdgEditor.setValue(value)
        if isinstance(self.wdgEditor, (QLineEdit, QTextEdit)):
            self.wdgEditor.setText(value)
        if isinstance(self.wdgEditor, QComboBox):
            self.wdgEditor.setCurrentText(value)
        if isinstance(self.wdgEditor, (ButtonSelectionWidget, TextSelectionWidget, LabelsSelectionWidget)):
            self.wdgEditor.setValue(value)

    def _fieldWidget(self) -> QWidget:
        if self.field.id == enneagram_field.id:
            widget = TextSelectionWidget(self.field, enneagram_help)
        elif self.field.id == traits_field.id:
            widget = LabelsSelectionWidget(self.field)
        elif self.field.type == TemplateFieldType.NUMERIC:
            widget = QSpinBox()
            widget.setMinimum(self.field.min_value)
            widget.setMaximum(self.field.max_value)
        elif self.field.type == TemplateFieldType.TEXT_SELECTION:
            widget = QComboBox()
            for item in self.field.selections:
                if item.type == SelectionItemType.CHOICE:
                    widget.addItem(_icon(item), item.text)
                if item.type == SelectionItemType.SEPARATOR:
                    widget.insertSeparator(widget.count())
        elif self.field.type == TemplateFieldType.BUTTON_SELECTION:
            widget = ButtonSelectionWidget(self.field)
        elif self.field.type == TemplateFieldType.IMAGE:
            widget = AvatarWidget(self.field)
        elif self.field.type == TemplateFieldType.SMALL_TEXT:
            widget = QTextEdit()
            widget.setMaximumHeight(60)
            widget.setPlaceholderText(self.field.placeholder)
        else:
            widget = QLineEdit()
            widget.setPlaceholderText(self.field.placeholder)

        return widget


class ProfileTemplateEditor(_ProfileTemplateBase):
    MimeType: str = 'application/template-field'

    fieldSelected = pyqtSignal(TemplateField)
    placeholderSelected = pyqtSignal()
    fieldAdded = pyqtSignal(TemplateField)

    def __init__(self, profile: ProfileTemplate):
        super(ProfileTemplateEditor, self).__init__(profile)
        self.setAcceptDrops(True)
        self.setStyleSheet('QWidget {background-color: rgb(255, 255, 255);}')
        self._selected: Optional[TemplateFieldWidget] = None
        self._target_to_drop: Optional[QWidget] = None

        for w in self.widgets:
            w.setEnabled(False)
            w.setAcceptDrops(True)
            self._installEventFilter(w)

        for row in range(max(6, self.gridLayout.rowCount() + 1)):
            for col in range(2):
                if not self.gridLayout.itemAtPosition(row, col):
                    self._addPlaceholder(row, col)

    def profile(self) -> ProfileTemplate:
        elements = []
        for i in range(self.gridLayout.count()):
            item = self.gridLayout.itemAt(i)
            if item and isinstance(item.widget(), TemplateFieldWidget):
                pos = self.gridLayout.getItemPosition(i)
                elements.append(
                    ProfileElement(item.widget().field, row=pos[0], col=pos[1], row_span=pos[2], col_span=pos[3]))

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
        widget_to_drop = TemplateFieldWidget(field)
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
                if isinstance(watched.parent(), AvatarWidget):
                    self._select(watched.parent().parent())
                else:
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

    def _select(self, widget: TemplateFieldWidget):
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
            self._selected.lblEmoji.setText(emoji.emojize(text))

    def _installEventFilter(self, widget: TemplateFieldWidget):
        widget.installEventFilter(self)
        if isinstance(widget.wdgEditor, AvatarWidget):
            widget.wdgEditor.btnUploadAvatar.installEventFilter(self)
        if isinstance(widget.wdgEditor, TextSelectionWidget):
            widget.wdgEditor.installEventFilter(self)

    def _addPlaceholder(self, row: int, col: int):
        _placeholder = _PlaceHolder()
        self.gridLayout.addWidget(_placeholder, row, col)
        _placeholder.setAcceptDrops(True)
        _placeholder.btn.setAcceptDrops(True)
        _placeholder.installEventFilter(self)
        _placeholder.btn.installEventFilter(self)


class ProfileTemplateView(_ProfileTemplateBase):
    def __init__(self, character: Character, profile: ProfileTemplate):
        super(ProfileTemplateView, self).__init__(profile)
        self.setObjectName('profileView')
        self.character = character
        self._name_widget: Optional[TemplateFieldWidget] = None
        self._avatar_widget: Optional[AvatarWidget] = None
        self._enneagram_widget: Optional[TextSelectionWidget] = None
        self._desire_widget: Optional[TemplateFieldWidget] = None
        self._fear_widget: Optional[TemplateFieldWidget] = None
        self._traits_widget: Optional[LabelsSelectionWidget] = None
        for widget in self.widgets:
            if widget.field.id == name_field.id:
                self._name_widget = widget
            elif widget.field.id == avatar_field.id:
                self._avatar_widget = widget.wdgEditor
            elif widget.field.id == enneagram_field.id:
                self._enneagram_widget = widget.wdgEditor
            elif widget.field.id == desire_field.id:
                self._desire_widget = widget
            elif widget.field.id == fear_field.id:
                self._fear_widget = widget
            elif widget.field.id == traits_field.id:
                self._traits_widget = widget.wdgEditor
        if not self._name_widget:
            raise ValueError('Obligatory name field is missing from profile')
        if not self._avatar_widget:
            raise ValueError('Obligatory avatar field is missing from profile')

        self._name_widget.wdgEditor.setFocusPolicy(Qt.StrongFocus)
        self._avatar_widget.setCharacter(self.character)
        if self._enneagram_widget:
            self._enneagram_widget.selectionChanged.connect(self._enneagram_changed)
        self.setProperty('mainFrame', True)

        self._selected: Optional[TemplateFieldWidget] = None

        self.setName(self.character.name)
        self.setValues(self.character.template_values)

    def name(self) -> str:
        return self._name_widget.value()

    def setName(self, value: str):
        self._name_widget.setValue(value)

    def avatarUpdated(self) -> bool:
        return self._avatar_widget.avatarUpdated

    def values(self) -> List[TemplateValue]:
        values: List[TemplateValue] = []
        for widget in self.widgets:
            if widget is self._name_widget:
                continue
            values.append(TemplateValue(id=widget.field.id, value=widget.value()))

        return values

    def setValues(self, values: List[TemplateValue]):
        ids = {}
        for value in values:
            ids[str(value.id)] = value.value

        for widget in self.widgets:
            if str(widget.field.id) in ids.keys():
                widget.setValue(ids[str(widget.field.id)])

    def _enneagram_changed(self, previous: Optional[SelectionItem], current: SelectionItem):
        update_desire = False
        update_fear = False
        if self._desire_widget:
            update_desire = True
            if previous:
                current_value = self._desire_widget.value()
                if current_value and current_value != previous.meta['desire']:
                    if not ask_confirmation("Do you want to update your character's DESIRE based on their Enneagram?"):
                        update_desire = False

        if self._fear_widget:
            update_fear = True
            if previous:
                current_value = self._fear_widget.value()
                if current_value and current_value != previous.meta['fear']:
                    if not ask_confirmation("Do you want to update your character's FEAR based on their Enneagram?"):
                        update_fear = False

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

        if update_desire:
            self._desire_widget.setValue(current.meta['desire'])
        if update_fear:
            self._fear_widget.setValue(current.meta['fear'])
