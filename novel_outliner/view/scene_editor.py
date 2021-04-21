from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal, QModelIndex, Qt, QAbstractItemModel, QSortFilterProxyModel
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QStyledItemDelegate, QStyleOptionViewItem, QLineEdit, QComboBox
from overrides import overrides

from novel_outliner.core.domain import Novel, Scene, ACTION_SCENE, REACTION_SCENE
from novel_outliner.model.characters_model import CharactersSceneAssociationTableModel
from novel_outliner.model.scenes_model import SceneEditorTableModel
from novel_outliner.view.common import EditorCommand
from novel_outliner.view.generated.scene_editor_ui import Ui_SceneEditor
from novel_outliner.view.icons import IconRegistry


class SceneEditor(QObject):
    commands_sent = pyqtSignal(QWidget, list)

    def __init__(self, novel: Novel, scene: Optional[Scene] = None):
        super().__init__()
        self.widget = QWidget()
        self.ui = Ui_SceneEditor()
        self.ui.setupUi(self.widget)
        self.novel = novel

        if scene:
            self.scene = scene
            self._new_scene = False
        else:
            self.scene = Scene('')
            self._new_scene = True

        self.ui.tabWidget.setTabIcon(self.ui.tabWidget.indexOf(self.ui.tabGeneral), IconRegistry.general_info_icon())
        self.ui.tabWidget.setTabIcon(self.ui.tabWidget.indexOf(self.ui.tabCharacters), IconRegistry.character_icon())
        self.ui.tabWidget.setTabIcon(self.ui.tabWidget.indexOf(self.ui.tabSynopsis), IconRegistry.synopsis_icon())

        self.ui.cbPov.addItem('', None)
        for char in self.novel.characters:
            self.ui.cbPov.addItem(char.name, char)
        if self.scene.pov:
            self.ui.cbPov.setCurrentText(self.scene.pov.name)
        self.ui.cbPov.currentIndexChanged.connect(self._on_pov_changed)

        self.ui.cbType.setItemIcon(1, IconRegistry.action_scene())
        self.ui.cbType.setItemIcon(2, IconRegistry.reaction_scene())
        self.ui.cbType.currentTextChanged.connect(self._on_type_changed)
        if self.scene.type:
            self.ui.cbType.setCurrentText(self.scene.type)

        self.ui.textEvent1.setText(self.scene.event_1)
        self.ui.textEvent2.setText(self.scene.event_2)
        self.ui.textEvent3.setText(self.scene.event_3)

        self.ui.lineTitle.setText(self.scene.title)
        self.ui.lineTitle.textChanged.connect(self._on_title_changed)
        self.ui.textSynopsis.setText(self.scene.synopsis)

        self._characters_model = CharactersSceneAssociationTableModel(self.novel, self.scene)
        self._characters_proxy_model = QSortFilterProxyModel()
        self._characters_proxy_model.setSourceModel(self._characters_model)
        self.ui.tblCharacters.setModel(self._characters_proxy_model)

        self.btn_save = self.ui.buttonBox.button(QDialogButtonBox.Save)
        self.btn_save.clicked.connect(self._on_saved)
        self.btn_cancel = self.ui.buttonBox.button(QDialogButtonBox.Cancel)
        self.btn_cancel.clicked.connect(self._on_cancel)

    def _on_title_changed(self, text: str):
        self.scene.title = text

    def _on_pov_changed(self):
        pov = self.ui.cbPov.currentData()
        if pov:
            self.scene.pov = pov

    def _on_type_changed(self, text: str):
        if text == ACTION_SCENE:
            self.ui.lblType1.setText('Goal:')
            self.ui.lblType2.setText('Conflict:')
            self.ui.lblType3.setText('Disaster:')
        elif text == REACTION_SCENE:
            self.ui.lblType1.setText('Reaction:')
            self.ui.lblType2.setText('Dilemma:')
            self.ui.lblType3.setText('Decision:')
        else:
            self.ui.lblType1.setText('Setup:')
            self.ui.lblType2.setText('Action:')
            self.ui.lblType3.setText('End:')
        self.scene.type = text

    def _on_saved(self):
        self.scene.synopsis = self.ui.textSynopsis.toPlainText()
        self.scene.event_1 = self.ui.textEvent1.toPlainText()
        self.scene.event_2 = self.ui.textEvent2.toPlainText()
        self.scene.event_3 = self.ui.textEvent3.toPlainText()
        if self._new_scene:
            self.novel.scenes.append(self.scene)
        self.commands_sent.emit(self.widget, [EditorCommand.SAVE, EditorCommand.CLOSE_CURRENT_EDITOR,
                                              EditorCommand.DISPLAY_SCENES])

    def _on_cancel(self):
        self.commands_sent.emit(self.widget, [EditorCommand.CLOSE_CURRENT_EDITOR])


class SceneEditorDelegate(QStyledItemDelegate):

    def __init__(self, novel: Novel):
        super().__init__()
        self.novel = novel

    @overrides
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        if index.row() == SceneEditorTableModel.RowPov:
            combo_box = QComboBox(parent)
            combo_box.activated.connect(lambda: self.commitData.emit(combo_box))
            for char in self.novel.characters:
                combo_box.addItem(char.name, char)
            return combo_box
        elif index.row() == SceneEditorTableModel.RowType:
            combo_box = QComboBox(parent)
            combo_box.activated.connect(lambda: self.commitData.emit(combo_box))
            combo_box.addItem(ACTION_SCENE)
            combo_box.setItemIcon(0, IconRegistry.action_scene())
            combo_box.addItem(REACTION_SCENE)
            combo_box.setItemIcon(1, IconRegistry.reaction_scene())
            return combo_box
        else:
            return QLineEdit(parent)

    @overrides
    def setEditorData(self, editor: QWidget, index: QModelIndex):
        edit_data = index.data(Qt.EditRole)
        if not edit_data:
            edit_data = index.data(Qt.DisplayRole)

        if index.row() == SceneEditorTableModel.RowPov:
            editor.setCurrentText(edit_data)
            editor.showPopup()
        elif index.row() == SceneEditorTableModel.RowType:
            editor.setCurrentText(edit_data)
            editor.showPopup()
        else:
            editor.setText(str(edit_data))

    @overrides
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if index.row() == SceneEditorTableModel.RowPov:
            character = editor.currentData()
            model.setData(index, character)
        else:
            super().setModelData(editor, model, index)
