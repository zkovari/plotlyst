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
from dataclasses import dataclass
from functools import partial
from typing import Iterable, List, Optional, Dict, Union

from PyQt6.QtCore import QItemSelection, Qt, pyqtSignal, QSize, QByteArray, QBuffer, QIODevice
from PyQt6.QtGui import QIcon, QColor, QImageReader, QImage, QPixmap, \
    QShowEvent
from PyQt6.QtWidgets import QWidget, QToolButton, QButtonGroup, QSizePolicy, QLabel, QPushButton, \
    QFileDialog, QMessageBox, QGridLayout
from overrides import overrides
from qthandy import vspacer, transparent, gc, line, spacer, clear_layout, hbox, flow, translucent, margins, pointy, \
    retain_when_hidden
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget, ScrollableMenuWidget

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Novel, Character
from src.main.python.plotlyst.core.template import SelectionItem, TemplateFieldType, TemplateField, RoleImportance
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import EventListener, Event
from src.main.python.plotlyst.event.handler import event_dispatchers
from src.main.python.plotlyst.events import CharacterSummaryChangedEvent
from src.main.python.plotlyst.model.common import DistributionFilterProxyModel
from src.main.python.plotlyst.model.distribution import CharactersScenesDistributionTableModel, \
    ConflictScenesDistributionTableModel, TagScenesDistributionTableModel
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.view.common import action, ButtonPressResizeEventFilter, tool_btn
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog, ArtbreederDialog, ImageCropDialog
from src.main.python.plotlyst.view.generated.avatar_selectors_ui import Ui_AvatarSelectors
from src.main.python.plotlyst.view.generated.characters_progress_widget_ui import Ui_CharactersProgressWidget
from src.main.python.plotlyst.view.generated.scene_dstribution_widget_ui import Ui_CharactersScenesDistributionWidget
from src.main.python.plotlyst.view.icons import avatars, IconRegistry
from src.main.python.plotlyst.view.style.base import apply_border_image
from src.main.python.plotlyst.view.widget.display import IconText, Icon
from src.main.python.plotlyst.view.widget.labels import CharacterLabel
from src.main.python.plotlyst.view.widget.progress import CircularProgressBar, ProgressTooltipMode, \
    CharacterRoleProgressChart


class CharactersScenesDistributionWidget(QWidget, Ui_CharactersScenesDistributionWidget):
    avg_text: str = 'Characters per scene: '
    common_text: str = 'Common scenes: '

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.average = 0

        self.btnCharacters.setIcon(IconRegistry.character_icon())
        self.btnConflicts.setIcon(IconRegistry.conflict_icon())
        self.btnTags.setIcon(IconRegistry.tags_icon())

        self._model = CharactersScenesDistributionTableModel(self.novel)
        self._scenes_proxy = DistributionFilterProxyModel()
        self._scenes_proxy.setSourceModel(self._model)
        self._scenes_proxy.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._scenes_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._scenes_proxy.setSortRole(CharactersScenesDistributionTableModel.SortRole)
        self._scenes_proxy.sort(CharactersScenesDistributionTableModel.IndexTags, Qt.SortOrder.DescendingOrder)
        self.tblSceneDistribution.horizontalHeader().setDefaultSectionSize(26)
        self.tblSceneDistribution.setModel(self._scenes_proxy)
        self.tblSceneDistribution.hideColumn(0)
        self.tblSceneDistribution.hideColumn(1)
        self.tblCharacters.setModel(self._scenes_proxy)
        self.tblCharacters.hideColumn(0)
        self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexTags, 70)
        self.tblCharacters.setMaximumWidth(70)

        self.tblCharacters.selectionModel().selectionChanged.connect(self._on_character_selected)
        self.tblSceneDistribution.selectionModel().selectionChanged.connect(self._on_scene_selected)

        self.btnCharacters.toggled.connect(self._toggle_characters)
        self.btnConflicts.toggled.connect(self._toggle_conflicts)
        self.btnTags.toggled.connect(self._toggle_tags)

        transparent(self.spinAverage)
        retain_when_hidden(self.spinAverage)

        self.btnCharacters.setChecked(True)

        self.refresh()

    def refresh(self):
        if self.novel.scenes:
            self.average = sum([len(x.characters) + 1 for x in self.novel.scenes]) / len(self.novel.scenes)
        else:
            self.average = 0
        for col in range(self._model.columnCount()):
            if col == CharactersScenesDistributionTableModel.IndexTags:
                continue
            self.tblCharacters.hideColumn(col)
        self.spinAverage.setValue(self.average)
        self.tblSceneDistribution.horizontalHeader().setMaximumSectionSize(15)
        self._model.modelReset.emit()

    def setActsFilter(self, act: int, filter: bool):
        self._scenes_proxy.setActsFilter(act, filter)

    def _toggle_characters(self, toggled: bool):
        if toggled:
            self._model = CharactersScenesDistributionTableModel(self.novel)
            self._scenes_proxy.setSourceModel(self._model)
            self.tblCharacters.hideColumn(0)
            self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexTags, 70)
            self.tblCharacters.setMaximumWidth(70)

            self.spinAverage.setVisible(True)

    # def _toggle_goals(self, toggled: bool):
    #     if toggled:
    #         self._model = GoalScenesDistributionTableModel(self.novel)
    #         self._scenes_proxy.setSourceModel(self._model)
    #         self.tblCharacters.hideColumn(0)
    #         self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexTags, 170)
    #         self.tblCharacters.setMaximumWidth(170)
    #
    #         self.spinAverage.setVisible(False)

    def _toggle_conflicts(self, toggled: bool):
        if toggled:
            self._model = ConflictScenesDistributionTableModel(self.novel)
            self._scenes_proxy.setSourceModel(self._model)
            self.tblCharacters.showColumn(0)
            self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexMeta, 34)
            self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexTags, 170)
            self.tblCharacters.setMaximumWidth(204)

            self.spinAverage.setVisible(False)

    def _toggle_tags(self, toggled: bool):
        if toggled:
            self._model = TagScenesDistributionTableModel(self.novel)
            self._scenes_proxy.setSourceModel(self._model)
            self.tblCharacters.hideColumn(0)
            self.tblCharacters.setColumnWidth(CharactersScenesDistributionTableModel.IndexTags, 170)
            self.tblCharacters.setMaximumWidth(170)

            self.spinAverage.setVisible(False)

    def _on_character_selected(self):
        selected = self.tblCharacters.selectionModel().selectedIndexes()
        self._model.highlightTags(
            [self._scenes_proxy.mapToSource(x) for x in selected])

        if selected and len(selected) > 1:
            self.spinAverage.setPrefix(self.common_text)
            self.spinAverage.setValue(self._model.commonScenes())
        else:
            self.spinAverage.setPrefix(self.avg_text)
            self.spinAverage.setValue(self.average)

        self.tblSceneDistribution.clearSelection()

    def _on_scene_selected(self, selection: QItemSelection):
        indexes = selection.indexes()
        if not indexes:
            return
        self._model.highlightScene(self._scenes_proxy.mapToSource(indexes[0]))
        self.tblCharacters.clearSelection()


class CharacterToolButton(QToolButton):
    def __init__(self, character: Character, parent=None):
        super(CharacterToolButton, self).__init__(parent)
        self.character = character
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        pointy(self)
        self.refresh()

    def refresh(self):
        self.setToolTip(self.character.name)
        self.setIcon(avatars.avatar(self.character))


class CharacterSelectorButtons(QWidget):
    characterToggled = pyqtSignal(Character, bool)
    characterClicked = pyqtSignal(Character)

    def __init__(self, parent=None, exclusive: bool = True):
        super(CharacterSelectorButtons, self).__init__(parent)
        hbox(self)
        self.container = QWidget()
        self.container.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)

        self._layout = flow(self.container)

        self.layout().addWidget(self.container)

        self._btn_group = QButtonGroup()
        self._buttons: List[CharacterToolButton] = []
        self._buttonsPerCharacters: Dict[Character, CharacterToolButton] = {}
        self.setExclusive(exclusive)

    def exclusive(self) -> bool:
        return self._btn_group.exclusive()

    def setExclusive(self, exclusive: bool):
        self._btn_group.setExclusive(exclusive)

    def characters(self, all: bool = True) -> Iterable[Character]:
        return [x.character for x in self._buttons if all or x.isChecked()]

    def setCharacters(self, characters: Iterable[Character], checkAll: bool = True):
        self.clear()

        for char in characters:
            self.addCharacter(char, checked=checkAll)

        if not self._buttons:
            return
        if self._btn_group.exclusive():
            self._buttons[0].setChecked(True)

    def updateCharacters(self, characters: Iterable[Character], checkAll: bool = True):
        if not self._buttons:
            return self.setCharacters(characters, checkAll)

        current_characters = set(x for x in self._buttonsPerCharacters.keys())

        for c in characters:
            if c in self._buttonsPerCharacters.keys():
                current_characters.remove(c)
            else:
                self.addCharacter(c, checkAll)

        for c in current_characters:
            self.removeCharacter(c)

        for btn in self._buttons:
            btn.refresh()

    def addCharacter(self, character: Character, checked: bool = True):
        tool_btn = CharacterToolButton(character)

        self._buttons.append(tool_btn)
        self._buttonsPerCharacters[character] = tool_btn
        self._btn_group.addButton(tool_btn)
        self._layout.addWidget(tool_btn)

        tool_btn.setChecked(checked)

        tool_btn.toggled.connect(partial(self.characterToggled.emit, character))
        tool_btn.clicked.connect(partial(self.characterClicked.emit, character))
        tool_btn.installEventFilter(OpacityEventFilter(parent=tool_btn, ignoreCheckedButton=True))

    def removeCharacter(self, character: Character):
        if character not in self._buttonsPerCharacters:
            return

        btn = self._buttonsPerCharacters.pop(character)
        if btn.isChecked():
            btn.setChecked(False)

        self._btn_group.removeButton(btn)
        self._buttons.remove(btn)
        self._layout.removeWidget(btn)
        gc(btn)

    def clear(self):
        clear_layout(self._layout)

        for btn in self._buttons:
            self._btn_group.removeButton(btn)
            self._layout.removeWidget(btn)
            gc(btn)

        self._buttons.clear()
        self._buttonsPerCharacters.clear()


class CharacterSelectorMenu(MenuWidget):
    selected = pyqtSignal(Character)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._characters: Optional[List[Character]] = None
        self.aboutToShow.connect(self._beforeShow)

    def setCharacters(self, character: List[Character]):
        self._characters = character
        self._fillUpMenu()

    def characters(self) -> List[Character]:
        if self._characters is not None:
            return self._characters
        else:
            return self._novel.characters

    def refresh(self):
        self._fillUpMenu()

    def _beforeShow(self):
        if self._characters is None:
            self._fillUpMenu()

    def _fillUpMenu(self):
        self.clear()

        for char in self.characters():
            self.addAction(
                action(char.name, avatars.avatar(char), slot=partial(self.selected.emit, char), parent=self))

        if not self.actions():
            self.addSection('No characters were found')
            self.addSeparator()
            self.addSection('Go to the Characters panel to create your first character')

        self._frame.updateGeometry()


class CharacterSelectorButton(QToolButton):
    characterSelected = pyqtSignal(Character)

    def __init__(self, novel: Novel, parent=None, opacityEffectEnabled: bool = True, iconSize: int = 32):
        super().__init__(parent)
        self._novel = novel
        self._iconSize = iconSize
        self._setIconSize = self._iconSize + 4
        pointy(self)
        self._opacityEffectEnabled = opacityEffectEnabled
        if self._opacityEffectEnabled:
            self._opacityFilter = OpacityEventFilter(self)
        else:
            self._opacityFilter = None
        self.installEventFilter(ButtonPressResizeEventFilter(self))
        self._menu = CharacterSelectorMenu(self._novel, self)
        self._menu.selected.connect(self._selected)
        self.clear()

    def characterSelectorMenu(self) -> CharacterSelectorMenu:
        return self._menu

    def setCharacter(self, character: Character):
        self.setIcon(avatars.avatar(character))
        transparent(self)
        if self._opacityEffectEnabled:
            self.removeEventFilter(self._opacityFilter)
            translucent(self, 1.0)
        self.setIconSize(QSize(self._setIconSize, self._setIconSize))

    def clear(self):
        self.setStyleSheet('''
                QToolButton {
                    border: 2px dotted grey;
                    border-radius: 6px;
                }
                QToolButton:hover {
                    border: 2px dotted black;
                }
        ''')
        self.setIcon(IconRegistry.character_icon('grey'))
        self.setIconSize(QSize(self._iconSize, self._iconSize))
        if self._opacityEffectEnabled:
            self.installEventFilter(self._opacityFilter)

    def _selected(self, character: Character):
        self.setCharacter(character)
        self.characterSelected.emit(character)


class CharacterLinkWidget(QWidget):
    characterSelected = pyqtSignal(Character)

    def __init__(self, parent=None):
        super(CharacterLinkWidget, self).__init__(parent)
        hbox(self)
        self.novel = app_env.novel
        self.character: Optional[Character] = None
        self.label: Optional[CharacterLabel] = None

        self.btnLinkCharacter = QPushButton(self)
        self.layout().addWidget(self.btnLinkCharacter)
        self.btnLinkCharacter.setIcon(IconRegistry.character_icon())
        self.btnLinkCharacter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnLinkCharacter.setStyleSheet('''
                QPushButton {
                    border: 2px dotted grey;
                    border-radius: 6px;
                    font: italic;
                }
                QPushButton:hover {
                    border: 2px dotted darkBlue;
                }
            ''')

        self._menu = ScrollableMenuWidget(self.btnLinkCharacter)

    def setDefaultText(self, value: str):
        self.btnLinkCharacter.setText(value)

    def setCharacter(self, character: Character):
        if self.character and character.id == self.character.id:
            return
        self.character = character

        self._clearLabel()
        self.label = CharacterLabel(self.character)
        self.label.setToolTip(f'<html>Agenda character: <b>{character.name}</b>')
        self.label.installEventFilter(OpacityEventFilter(self.label, enterOpacity=0.7, leaveOpacity=1.0))
        pointy(self.label)
        self.label.clicked.connect(lambda: self._menu.exec())
        self.layout().addWidget(self.label)
        self.btnLinkCharacter.setHidden(True)

    def reset(self):
        self._clearLabel()
        self.btnLinkCharacter.setVisible(True)

    def setAvailableCharacters(self, characters: List[Character]):
        self._menu.clear()
        for character in characters:
            self._menu.addAction(
                action(character.name, avatars.avatar(character), partial(self._characterClicked, character)))

    def _clearLabel(self):
        if self.label is not None:
            self.layout().removeWidget(self.label)
            gc(self.label)
            self.label = None

    def _characterClicked(self, character: Character):
        self.btnLinkCharacter.menu().hide()
        self.setCharacter(character)
        self.characterSelected.emit(character)


class AvatarSelectors(QWidget, Ui_AvatarSelectors):
    updated = pyqtSignal()
    selectorChanged = pyqtSignal()

    def __init__(self, character: Character, parent=None):
        super(AvatarSelectors, self).__init__(parent)
        self.setupUi(self)
        self.character = character
        self.btnUploadAvatar.setIcon(IconRegistry.upload_icon(color='white'))
        self.btnUploadAvatar.clicked.connect(self._upload_avatar)
        self.btnAi.setIcon(IconRegistry.from_name('mdi.robot-happy-outline', 'white'))
        self.btnAi.clicked.connect(self._select_ai)
        self.btnInitial.setIcon(IconRegistry.from_name('mdi.alpha-a-circle'))
        self.btnRole.setIcon(IconRegistry.from_name('fa5s.chess-bishop'))
        self.btnCustomIcon.setIcon(IconRegistry.icons_icon())
        if character.avatar:
            pass
        else:
            self.btnImage.setHidden(True)
            if self.character.prefs.avatar.use_image:
                self.character.prefs.avatar.allow_initial()

        self.btnGroupSelectors.buttonClicked.connect(self._selectorClicked)
        self.refresh()

    def refresh(self):
        prefs = self.character.prefs.avatar
        if prefs.use_image:
            self.btnImage.setChecked(True)
            self.btnImage.setVisible(True)
        elif prefs.use_initial:
            self.btnInitial.setChecked(True)
        elif prefs.use_role:
            self.btnRole.setChecked(True)
        elif prefs.use_custom_icon:
            self.btnCustomIcon.setChecked(True)

        if prefs.icon:
            self.btnCustomIcon.setIcon(IconRegistry.from_name(prefs.icon, prefs.icon_color))
        if self.character.role:
            self.btnRole.setIcon(IconRegistry.from_name(self.character.role.icon, self.character.role.icon_color))
        if avatars.has_name_initial_icon(self.character):
            self.btnInitial.setIcon(avatars.name_initial_icon(self.character))
        if self.character.avatar:
            self.btnImage.setIcon(QIcon(avatars.image(self.character)))

    def _selectorClicked(self):
        if self.btnImage.isChecked():
            self.character.prefs.avatar.allow_image()
        elif self.btnInitial.isChecked():
            self.character.prefs.avatar.allow_initial()
        elif self.btnRole.isChecked():
            self.character.prefs.avatar.allow_role()
        elif self.btnCustomIcon.isChecked():
            self.character.prefs.avatar.allow_custom_icon()
            result = IconSelectorDialog().display()
            if result:
                self.character.prefs.avatar.icon = result[0]
                self.character.prefs.avatar.icon_color = result[1].name()

        self.selectorChanged.emit()

    def _upload_avatar(self):
        filename: str = QFileDialog.getOpenFileName(None, 'Choose an image', '', 'Images (*.png *.jpg *jpeg)')
        if not filename or not filename[0]:
            return
        reader = QImageReader(filename[0])
        reader.setAutoTransform(True)
        image: QImage = reader.read()
        if image is None:
            QMessageBox.warning(self, 'Error while loading image',
                                'Could not load image. Did you select a valid image? (e.g.: png, jpg, jpeg)')
            return
        if image.width() < 128 or image.height() < 128:
            QMessageBox.warning(self, 'Uploaded image is too small',
                                'The uploaded image is too small. It must be larger than 128 pixels')
            return

        pixmap = QPixmap.fromImage(image)
        crop = ImageCropDialog().display(pixmap)
        if crop:
            self._update_avatar(crop)

    def _update_avatar(self, image: Union[QImage, QPixmap]):
        array = QByteArray()
        buffer = QBuffer(array)
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, 'PNG')
        self.character.avatar = array
        self.character.prefs.avatar.allow_image()
        self.refresh()

        self.updated.emit()

    def _select_ai(self):
        diag = ArtbreederDialog()
        pixmap = diag.display()
        if pixmap:
            self._update_avatar(pixmap)


class CharacterAvatar(QWidget):
    avatarUpdated = pyqtSignal()

    def __init__(self, parent=None, defaultIconSize: int = 118, avatarSize: int = 168, customIconSize: int = 132,
                 margins: int = 17):
        super().__init__(parent)
        self._defaultIconSize = defaultIconSize
        self._avatarSize = avatarSize
        self._customIconSize = customIconSize
        self.wdgFrame = QWidget()
        self.wdgFrame.setProperty('border-image', True)
        hbox(self, 0, 0).addWidget(self.wdgFrame)
        self.btnAvatar = tool_btn(IconRegistry.character_icon(), transparent_=True)
        hbox(self.wdgFrame, margins).addWidget(self.btnAvatar)
        self.btnAvatar.installEventFilter(OpacityEventFilter(parent=self.btnAvatar, enterOpacity=0.7, leaveOpacity=1.0))
        apply_border_image(self.wdgFrame, resource_registry.circular_frame1)

        self._character: Optional[Character] = None
        self._uploaded: bool = False
        self._uploadSelectorsEnabled: bool = False

        self.reset()

    def setUploadPopupMenu(self):
        if not self._character:
            raise ValueError('Set character first')
        wdg = AvatarSelectors(self._character)
        wdg.updated.connect(self._uploadedAvatar)
        wdg.selectorChanged.connect(self.updateAvatar)

        menu = MenuWidget(self.btnAvatar)
        menu.addWidget(wdg)

    def character(self) -> Optional[Character]:
        return self._character

    def setCharacter(self, character: Character):
        self._character = character
        self.updateAvatar()

    def updateAvatar(self):
        self.btnAvatar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        if self._character.prefs.avatar.use_role or self._character.prefs.avatar.use_custom_icon:
            self.btnAvatar.setIconSize(QSize(self._customIconSize, self._customIconSize))
        else:
            self.btnAvatar.setIconSize(QSize(self._avatarSize, self._avatarSize))
        avatar = avatars.avatar(self._character, fallback=False)
        if avatar:
            self.btnAvatar.setIcon(avatar)
        else:
            self.reset()
        self.avatarUpdated.emit()

    def reset(self):
        self.btnAvatar.setIconSize(QSize(self._defaultIconSize, self._defaultIconSize))
        self.btnAvatar.setIcon(IconRegistry.character_icon(color='grey'))
        self.btnAvatar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

    def imageUploaded(self) -> bool:
        return self._uploaded

    def _uploadedAvatar(self):
        self._uploaded = True
        avatars.update_image(self._character)
        self.updateAvatar()


class CharactersProgressWidget(QWidget, Ui_CharactersProgressWidget, EventListener):
    characterClicked = pyqtSignal(Character)

    RowOverall: int = 1
    RowName: int = 3
    RowRole: int = 4
    RowGender: int = 5

    @dataclass
    class Header:
        header: TemplateField
        row: int
        max_value: int = 0

        def __hash__(self):
            return hash(str(self.header.id))

    def __init__(self, parent=None):
        super(CharactersProgressWidget, self).__init__(parent)
        self.setupUi(self)
        self._layout = QGridLayout()
        self.scrollAreaProgress.setLayout(self._layout)
        margins(self, 2, 2, 2, 2)
        self._layout.setSpacing(5)
        self._refreshNext: bool = False

        self.novel: Optional[Novel] = None

        self._chartMajor = CharacterRoleProgressChart(RoleImportance.MAJOR)
        self.chartViewMajor.setChart(self._chartMajor)
        self._chartSecondary = CharacterRoleProgressChart(RoleImportance.SECONDARY)
        self.chartViewSecondary.setChart(self._chartSecondary)
        self._chartMinor = CharacterRoleProgressChart(RoleImportance.MINOR)
        self.chartViewMinor.setChart(self._chartMinor)

        self._chartMajor.setBackgroundBrush(QColor(RELAXED_WHITE_COLOR))
        self._chartSecondary.setBackgroundBrush(QColor(RELAXED_WHITE_COLOR))
        self._chartMinor.setBackgroundBrush(QColor(RELAXED_WHITE_COLOR))

        self._chartMajor.refresh()
        self._chartSecondary.refresh()
        self._chartMinor.refresh()

    def setNovel(self, novel: Novel):
        self.novel = novel
        dispatcher = event_dispatchers.instance(self.novel)
        dispatcher.register(self, CharacterSummaryChangedEvent)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, CharacterSummaryChangedEvent):
            self._refreshNext = True

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        if self._refreshNext:
            self._refreshNext = False
            self.refresh()

    def refresh(self):
        if not self.novel:
            return

        clear_layout(self._layout)
        for chart_ in [self._chartMajor, self._chartSecondary, self._chartMinor]:
            chart_.setValue(0)
            chart_.setMaxValue(0)

        for i, char in enumerate(self.novel.characters):
            btn = QToolButton(self)
            btn.setIconSize(QSize(45, 45))
            transparent(btn)
            btn.setIcon(avatars.avatar(char))
            btn.setToolTip(char.name)
            self._layout.addWidget(btn, 0, i + 1)
            pointy(btn)
            btn.installEventFilter(ButtonPressResizeEventFilter(btn))
            btn.installEventFilter(OpacityEventFilter(btn, 0.8, 1.0))
            btn.clicked.connect(partial(self.characterClicked.emit, char))
        self._layout.addWidget(spacer(), 0, self._layout.columnCount())

        self._addLabel(self.RowOverall, 'Overall', IconRegistry.progress_check_icon(), Qt.AlignmentFlag.AlignCenter)
        self._addLine(self.RowOverall + 1)
        self._addLabel(self.RowName, 'Name', IconRegistry.character_icon())
        self._addLabel(self.RowRole, 'Role', IconRegistry.major_character_icon())
        self._addLabel(self.RowGender, 'Gender', IconRegistry.male_gender_icon())
        self._addLine(self.RowGender + 1)

        fields = {}
        headers: Dict[CharactersProgressWidget.Header, int] = {}
        header: Optional[CharactersProgressWidget.Header] = None
        row = self.RowGender + 1
        for el in self.novel.character_profiles[0].elements:
            if el.field.type == TemplateFieldType.DISPLAY_HEADER:
                row += 1
                self._addLabel(row, el.field.name)
                header = self.Header(el.field, row)
                headers[header] = 0
            elif not el.field.type.name.startswith('DISPLAY') and header:
                fields[str(el.field.id)] = header
                header.max_value = header.max_value + 1

        row += 1
        self._addLine(row)
        row += 1
        for col, char in enumerate(self.novel.characters):
            self._updateForCharacter(char, fields, headers, row, col)

        self._addLabel(row, 'Backstory', IconRegistry.backstory_icon())
        self._addLabel(row + 1, 'Topics', IconRegistry.topics_icon())
        self._layout.addWidget(vspacer(), row + 2, 0)

        self._chartMajor.refresh()
        self._chartSecondary.refresh()
        self._chartMinor.refresh()

    def _updateForCharacter(self, char: Character, fields, headers, row: int, col: int):
        name_progress = CircularProgressBar(parent=self)
        if char.name:
            name_progress.setValue(1)
        self._addWidget(name_progress, self.RowName, col + 1)

        role_value = 0
        if char.role:
            role_value = 1
            self._addItem(char.role, self.RowRole, col + 1)
        else:
            self._addWidget(CircularProgressBar(parent=self), self.RowRole, col + 1)

        gender_value = 0
        if char.gender:
            gender_value = 1
            self._addIcon(IconRegistry.gender_icon(char.gender), self.RowGender, col + 1)
        else:
            self._addWidget(CircularProgressBar(parent=self), self.RowGender, col + 1)

        for h in headers.keys():
            headers[h] = 0  # reset char values
        for value in char.template_values:
            if str(value.id) not in fields.keys():
                continue
            header = fields[str(value.id)]
            if not header.header.required and char.is_minor():
                continue
            if not char.disabled_template_headers.get(str(header.header.id), header.header.enabled):
                continue
            if value.value or value.ignored:
                if isinstance(value.value, dict):
                    count = 0
                    values = 0
                    for _, attrs in value.value.items():
                        count += 1
                        if attrs.get('value'):
                            values += 1
                        for secondary in attrs.get('secondary', []):
                            count += 1
                            if secondary.get('value'):
                                values += 1

                    headers[header] = headers[header] + values / count
                else:
                    headers[header] = headers[header] + 1

        overall_progress = CircularProgressBar(maxValue=2, parent=self)
        overall_progress.setTooltipMode(ProgressTooltipMode.PERCENTAGE)
        overall_progress.setValue((name_progress.value() + gender_value) // 2 + role_value)

        for h, v in headers.items():
            if not h.header.required and char.is_minor():
                continue
            if not char.disabled_template_headers.get(str(h.header.id), h.header.enabled):
                continue
            value_progress = CircularProgressBar(v, h.max_value, parent=self)
            self._addWidget(value_progress, h.row, col + 1)
            overall_progress.addMaxValue(h.max_value)
            overall_progress.addValue(v)
        if not char.is_minor():
            backstory_progress = CircularProgressBar(parent=self)
            backstory_progress.setMaxValue(5 if char.is_major() else 3)
            backstory_progress.setValue(len(char.backstory))
            overall_progress.addMaxValue(backstory_progress.maxValue())
            overall_progress.addValue(backstory_progress.value())
            self._addWidget(backstory_progress, row, col + 1)

        if char.topics:
            topics_progress = CircularProgressBar(parent=self)
            topics_progress.setMaxValue(len(char.topics))
            topics_progress.setValue(len([x for x in char.topics if x.value]))
            overall_progress.addMaxValue(topics_progress.maxValue())
            overall_progress.addValue(topics_progress.value())
            self._addWidget(topics_progress, row + 1, col + 1)

        self._addWidget(overall_progress, self.RowOverall, col + 1)

        if char.is_major():
            self._chartMajor.setMaxValue(self._chartMajor.maxValue() + overall_progress.maxValue())
            self._chartMajor.setValue(self._chartMajor.value() + overall_progress.value())
        elif char.is_secondary():
            self._chartSecondary.setMaxValue(self._chartSecondary.maxValue() + overall_progress.maxValue())
            self._chartSecondary.setValue(self._chartSecondary.value() + overall_progress.value())
        elif char.is_minor():
            self._chartMinor.setMaxValue(self._chartMinor.maxValue() + overall_progress.maxValue())
            self._chartMinor.setValue(self._chartMinor.value() + overall_progress.value())

    def _addLine(self, row: int):
        self._layout.addWidget(line(), row, 0, 1, self._layout.columnCount() - 1)

    def _addLabel(self, row: int, text: str, icon=None, alignment=Qt.AlignmentFlag.AlignRight):
        if icon:
            wdg = IconText(self)
            wdg.setIcon(icon)
        else:
            wdg = QLabel(parent=self)
        wdg.setText(text)

        self._layout.addWidget(wdg, row, 0, alignment=alignment)

    def _addWidget(self, progress: QWidget, row: int, col: int):
        if row > self.RowOverall:
            progress.installEventFilter(OpacityEventFilter(parent=progress))
        self._layout.addWidget(progress, row, col, alignment=Qt.AlignmentFlag.AlignCenter)

    def _addIcon(self, icon: QIcon, row: int, col: int):
        _icon = Icon()
        _icon.setIcon(icon)
        self._addWidget(_icon, row, col)

    def _addItem(self, item: SelectionItem, row: int, col: int):
        icon = Icon()
        icon.iconName = item.icon
        icon.iconColor = item.icon_color
        icon.setToolTip(item.text)
        self._addWidget(icon, row, col)
