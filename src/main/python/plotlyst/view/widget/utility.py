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
from typing import Any, Optional, Tuple, Dict, List

from PyQt6.QtCore import QModelIndex, Qt, QAbstractListModel, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QBrush, QResizeEvent
from PyQt6.QtWidgets import QWidget, QListView, QSizePolicy, QToolButton, QButtonGroup, QDialog, QLabel, QPushButton, \
    QGridLayout, QColorDialog
from overrides import overrides
from qthandy import flow, transparent, pointy, grid, vspacer, italic, underline, decr_font, incr_font, bold, \
    spacer, line, decr_icon, ask_confirmation, vline
from qthandy.filter import OpacityEventFilter

from plotlyst.common import PLOTLYST_MAIN_COMPLEMENTARY_COLOR, RELAXED_WHITE_COLOR, PLOTLYST_SECONDARY_COLOR
from plotlyst.event.core import EventListener, Event
from plotlyst.event.handler import global_event_dispatcher
from plotlyst.model.common import proxy
from plotlyst.resources import ResourceType, resource_manager, ResourceDescriptor, \
    ResourceStatusChangedEvent
from plotlyst.service.resource import remove_resource, download_resource
from plotlyst.view.common import ButtonPressResizeEventFilter, spin, tool_btn
from plotlyst.view.generated.icon_selector_widget_ui import Ui_IconsSelectorWidget
from plotlyst.view.generated.resource_manager_dialog_ui import Ui_ResourceManagerDialog
from plotlyst.view.icons import IconRegistry
from plotlyst.view.layout import group
from plotlyst.view.widget._icons import icons_registry
from plotlyst.view.widget.button import SecondaryActionToolButton
from plotlyst.view.widget.display import PopupDialog


class ColorButton(QToolButton):
    def __init__(self, color: str, parent=None):
        super(ColorButton, self).__init__(parent)
        self.color = color
        self.setCheckable(True)
        pointy(self)
        self.setIcon(IconRegistry.from_name('fa5s.circle', color=color))
        transparent(self)
        self.setIconSize(QSize(24, 24))
        self.installEventFilter(ButtonPressResizeEventFilter(self))


BASE_COLORS = ['darkBlue', '#0077b6', '#00b4d8', '#007200', '#2a9d8f', '#94d2bd', '#ffd000', '#f48c06',
               '#e85d04',
               '#dc2f02',
               '#ffc6ff', '#b5179e', '#7209b7', '#d6ccc2', '#6c757d', '#dda15e', '#bc6c25', 'black']


class ColorPicker(QWidget):
    colorPicked = pyqtSignal(QColor)

    def __init__(self, parent=None, maxColumn: Optional[int] = None):
        super().__init__(parent)
        if maxColumn:
            grid(self, 1, 1, 1)
        else:
            flow(self)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self.btnGroup = QButtonGroup(self)
        self.btnGroup.setExclusive(True)

        row = -1
        for i, color in enumerate(BASE_COLORS):
            btn = ColorButton(color, self)

            self.btnGroup.addButton(btn)
            if maxColumn:
                if i % maxColumn == 0:
                    row += 1
                    col = 0
                else:
                    col = i % maxColumn
                self.layout().addWidget(btn, row, col)
            else:
                self.layout().addWidget(btn)

        self._btnCustomColor = tool_btn(IconRegistry.from_name('msc.symbol-color'), transparent_=True,
                                        tooltip='Select a custom color')
        self._btnCustomColor.clicked.connect(self._customColorClicked)
        self.layout().addWidget(vline())
        self.layout().addWidget(self._btnCustomColor)
        self.btnGroup.buttonClicked.connect(self._clicked)

    def color(self) -> QColor:
        btn = self.btnGroup.checkedButton()
        if btn:
            return QColor(btn.color)
        else:
            return QColor(Qt.GlobalColor.black)

    def _clicked(self, btn: ColorButton):
        self.colorPicked.emit(QColor(btn.color))

    def _customColorClicked(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.colorPicked.emit(color)


class IconSelectorWidget(QWidget, Ui_IconsSelectorWidget):
    iconSelected = pyqtSignal(str, QColor)
    model = None

    def __init__(self, parent=None):
        super(IconSelectorWidget, self).__init__(parent)
        self.setupUi(self)

        self.btnFilterIcon.setIcon(IconRegistry.from_name('mdi.magnify'))

        self.btnPeople.setIcon(IconRegistry.from_name('mdi.account', color_on=PLOTLYST_SECONDARY_COLOR))
        self.btnPeople.setToolTip('People and emotions')
        self.btnFood.setIcon(IconRegistry.from_name('fa5s.ice-cream', color_on=PLOTLYST_SECONDARY_COLOR))
        self.btnFood.setToolTip('Food and beverage')
        self.btnNature.setIcon(IconRegistry.from_name('mdi.nature', color_on=PLOTLYST_SECONDARY_COLOR))
        self.btnNature.setToolTip('Nature')
        self.btnSports.setIcon(IconRegistry.from_name('fa5s.football-ball', color_on=PLOTLYST_SECONDARY_COLOR))
        self.btnSports.setToolTip('Sports')
        self.btnObjects.setIcon(IconRegistry.from_name('fa5.lightbulb', color_on=PLOTLYST_SECONDARY_COLOR))
        self.btnObjects.setToolTip('Objects')
        self.btnPlaces.setIcon(IconRegistry.from_name('ei.globe', color_on=PLOTLYST_SECONDARY_COLOR))
        self.btnPlaces.setToolTip('Places and travel')
        self.btnCharacters.setIcon(
            IconRegistry.from_name('mdi6.alphabetical-variant', color_on=PLOTLYST_SECONDARY_COLOR))
        self.btnCharacters.setToolTip('Numbers and characters')
        self.btnSymbols.setIcon(IconRegistry.from_name('mdi.symbol', color_on=PLOTLYST_SECONDARY_COLOR))
        self.btnSymbols.setToolTip('Symbols')
        self.btnAll.setChecked(True)

        self.colorPicker = ColorPicker(self)
        self.colorPicker.colorPicked.connect(self._colorPicked)
        self.wdgTop.layout().insertWidget(0, self.colorPicker)

        if IconSelectorWidget.model is None:
            filtered_icons = []
            for type, icons_list in icons_registry.items():
                for icon in icons_list:
                    if icon and icon != 'fa5s.' and icon != 'mdi.':
                        filtered_icons.append(self._IconItem(type, icon))
            IconSelectorWidget.model = self._Model(filtered_icons)

        self._proxy = proxy(IconSelectorWidget.model)
        self._proxy.setFilterRole(self._Model.IconTypeRole)
        self.lstIcons.setModel(self._proxy)
        self.lstIcons.setViewMode(QListView.ViewMode.IconMode)
        self.lstIcons.clicked.connect(self._iconClicked)

        self.lineFilter.textChanged.connect(self._textChanged)

        self.buttonGroup.buttonToggled.connect(self._filterToggled)
        self.lineFilter.setFocus()

    def setColor(self, color: QColor):
        self.model.setColor(color)

    def _colorPicked(self, color: QColor):
        self.model.setColor(color)

    def _textChanged(self, text: str):
        self.btnAll.setChecked(True)
        self._proxy.setFilterRole(self._Model.IconAliasRole)
        self._proxy.setFilterRegularExpression(text)

    def _filterToggled(self):
        self._proxy.setFilterRole(self._Model.IconTypeRole)
        if self.btnPeople.isChecked():
            self._proxy.setFilterFixedString('People')
        elif self.btnFood.isChecked():
            self._proxy.setFilterFixedString('Food')
        elif self.btnNature.isChecked():
            self._proxy.setFilterFixedString('Animals & Nature')
        elif self.btnSports.isChecked():
            self._proxy.setFilterFixedString('Sports & Activities')
        elif self.btnPlaces.isChecked():
            self._proxy.setFilterFixedString('Travel & Places')
        elif self.btnObjects.isChecked():
            self._proxy.setFilterFixedString('Objects')
        elif self.btnCharacters.isChecked():
            self._proxy.setFilterFixedString('Numbers and Characters')
        elif self.btnSymbols.isChecked():
            self._proxy.setFilterFixedString('Symbols')
        elif self.btnAll.isChecked():
            self._proxy.setFilterFixedString('')

    def _iconClicked(self, index: QModelIndex):
        icon_alias: str = index.data(role=self._Model.IconAliasRole)
        self.iconSelected.emit(icon_alias, QColor(self.model.color))

    class _IconItem:
        def __init__(self, type: str, name: str):
            self.type = type
            self.name = name

    class _Model(QAbstractListModel):

        IconAliasRole = Qt.ItemDataRole.UserRole + 1
        IconTypeRole = Qt.ItemDataRole.UserRole + 2

        def __init__(self, icons):
            super().__init__()
            self.icons = icons
            self.color: str = 'black'

        @overrides
        def rowCount(self, parent: QModelIndex = ...) -> int:
            return len(self.icons)

        @overrides
        def data(self, index: QModelIndex, role: int) -> Any:
            if role == self.IconAliasRole:
                return self.icons[index.row()].name
            if role == self.IconTypeRole:
                return self.icons[index.row()].type
            if role == Qt.ItemDataRole.DecorationRole:
                return IconRegistry.from_name(self.icons[index.row()].name, self.color)
            if role == Qt.ItemDataRole.BackgroundRole:
                if self.color == '#ffffff':
                    return QBrush(Qt.GlobalColor.lightGray)
                else:
                    return QBrush(QColor(RELAXED_WHITE_COLOR))

            if role == Qt.ItemDataRole.ToolTipRole:
                return self.icons[index.row()].name.split('.')[1].replace('-', ' ').capitalize()

        def setColor(self, color: QColor):
            self.color = color.name()
            self.modelReset.emit()


class IconSelectorDialog(PopupDialog):

    def __init__(self, pickColor: bool = True, color: QColor = QColor(Qt.GlobalColor.black), parent=None):
        super().__init__(parent)
        self.resize(500, 500)

        self._icon = ''
        self._color: Optional[QColor] = None
        self.selector = IconSelectorWidget(self)
        self.selector.colorPicker.setVisible(pickColor)
        self.selector.setColor(color)
        self.selector.iconSelected.connect(self._icon_selected)

        self.frame.layout().addWidget(self.btnReset, alignment=Qt.AlignmentFlag.AlignRight)
        self.frame.layout().addWidget(self.selector)

    def display(self) -> Optional[Tuple[str, QColor]]:
        result = self.exec()
        if result == QDialog.DialogCode.Accepted and self._icon:
            return self._icon, self._color

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.selector.lstIcons.model().modelReset.emit()
        self.selector.lstIcons.update()

    def _icon_selected(self, icon_alias: str, color: QColor):
        self._icon = icon_alias
        self._color = color

        self.accept()


class IconSelectorButton(SecondaryActionToolButton):
    iconSelected = pyqtSignal(str, QColor)

    def __init__(self, parent=None):
        super(IconSelectorButton, self).__init__(parent)
        self._selectedIconSize = QSize(32, 32)
        self._defaultIconSize = QSize(24, 24)

        self._selected: bool = False
        self.installEventFilter(ButtonPressResizeEventFilter(self))
        self.reset()
        self.clicked.connect(self._displayIcons)

    def setSelectedIconSize(self, size: QSize):
        self._selectedIconSize = size
        if self._selected:
            self.setIconSize(self._selectedIconSize)

    def setDefaultIconSize(self, size: QSize):
        self._defaultIconSize = size

    def selectIcon(self, icon: str, icon_color: str):
        self.setIcon(IconRegistry.from_name(icon, icon_color))
        transparent(self)
        self.setIconSize(self._selectedIconSize)
        self._selected = True

    def reset(self):
        self.setIconSize(self._defaultIconSize)
        self.setIcon(IconRegistry.icons_icon())
        self.initStyleSheet()
        self._selected = False

    def _displayIcons(self):
        result = IconSelectorDialog.popup()
        if result:
            self.selectIcon(result[0], result[1].name())
            self.iconSelected.emit(result[0], result[1])


class _ResourceControllers:
    def __init__(self, resourceType: ResourceType):
        super(_ResourceControllers, self).__init__()
        self._resourceType = resourceType
        self._resource: ResourceDescriptor = resource_manager.resource(self._resourceType)

        self.label = QLabel(self._resource.human_name)
        incr_font(self.label)
        bold(self.label)
        self.description = QLabel(self._resource.description)
        decr_font(self.description)
        self.description.setProperty('description', True)
        self.btnStatus = QToolButton()
        italic(self.btnStatus)
        transparent(self.btnStatus)

        self.btnRemove = QPushButton()
        self.btnRemove.setToolTip('Remove downloaded resource. Some functionality might stop working')
        self.btnRemove.setProperty('base', True)
        self.btnRemove.setProperty('deconstructive', True)
        decr_icon(self.btnRemove, 2)
        pointy(self.btnRemove)
        self.btnRemove.setIcon(IconRegistry.trash_can_icon('white'))
        self.btnRemove.installEventFilter(OpacityEventFilter(self.btnRemove, leaveOpacity=0.7))
        self.btnRemove.installEventFilter(ButtonPressResizeEventFilter(self.btnRemove))

        self.btnDownload = QPushButton()
        self.btnDownload.setToolTip('Download external resource. Internet access is necessary')
        self.btnDownload.setProperty('base', True)
        self.btnDownload.setProperty('highlighted', True)
        decr_icon(self.btnDownload, 2)
        pointy(self.btnDownload)
        self.btnDownload.setIcon(IconRegistry.from_name('mdi.download', 'white'))
        self.btnDownload.installEventFilter(OpacityEventFilter(self.btnDownload, leaveOpacity=0.7))
        self.btnDownload.installEventFilter(ButtonPressResizeEventFilter(self.btnDownload))

        self.btnRemove.clicked.connect(self._askRemove)
        self.btnDownload.clicked.connect(self.download)

        self.refresh()

    def resource(self) -> ResourceDescriptor:
        return self._resource

    def remove(self):
        spin(self.btnStatus)
        self.btnRemove.setDisabled(True)
        remove_resource(self._resourceType)

    def download(self):
        spin(self.btnStatus)
        self.btnDownload.setDisabled(True)
        download_resource(self._resourceType)

    def refresh(self):
        if resource_manager.has_resource(self._resourceType):
            self.btnStatus.setIcon(IconRegistry.ok_icon(PLOTLYST_MAIN_COMPLEMENTARY_COLOR))
            self.btnStatus.setToolTip('Downloaded')
            self.btnRemove.setVisible(True)
            self.btnRemove.setEnabled(True)
            self.btnDownload.setHidden(True)
        else:
            self.btnStatus.setIcon(IconRegistry.from_name('fa5s.minus'))
            self.btnStatus.setToolTip('Missing')
            self.btnRemove.setHidden(True)
            self.btnDownload.setVisible(True)
            self.btnDownload.setEnabled(True)

    def _askRemove(self):
        if ask_confirmation(
                f"Remove downloaded resource '{self._resource.human_name}'? Some functionality might stop working."):
            self.remove()


class ResourceManagerWidget(QWidget, EventListener):

    def __init__(self, resourceTypes: Optional[List[ResourceType]] = None, parent=None):
        super(ResourceManagerWidget, self).__init__(parent)
        if not resourceTypes:
            resourceTypes = [ResourceType.JRE_8, ResourceType.PANDOC, ResourceType.NLTK_AVERAGED_PERCEPTRON_TAGGER,
                             ResourceType.NLTK_PUNKT_TOKENIZER]
        self._resources: Dict[ResourceType, _ResourceControllers] = {}

        self._gridLayout: QGridLayout = grid(self)

        header = QLabel('Resource')
        underline(header)
        self._gridLayout.addWidget(header, 0, 0)
        header = QLabel('Status')
        underline(header)
        self._gridLayout.addWidget(header, 0, 1)
        self._gridLayout.addWidget(line(), 1, 0, 1, 3)

        for i, resourceType in enumerate(resourceTypes):
            contr = _ResourceControllers(resourceType)
            self._resources[resourceType] = contr
            self._gridLayout.addWidget(group(contr.label, contr.description, vertical=False, spacing=2), i + 2, 0)
            self._gridLayout.addWidget(contr.btnStatus, i + 2, 1, alignment=Qt.AlignmentFlag.AlignCenter)
            self._gridLayout.addWidget(contr.btnRemove, i + 2, 2, alignment=Qt.AlignmentFlag.AlignCenter)
            self._gridLayout.addWidget(contr.btnDownload, i + 2, 3, alignment=Qt.AlignmentFlag.AlignCenter)
            self._gridLayout.addWidget(spacer(), i + 2, 4)

        global_event_dispatcher.register(self, ResourceStatusChangedEvent)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, ResourceStatusChangedEvent):
            self._resources[event.type].refresh()


class ResourceManagerDialog(QDialog, Ui_ResourceManagerDialog):
    def __init__(self, resourceTypes: Optional[List[ResourceType]] = None, parent=None):
        super(ResourceManagerDialog, self).__init__(parent)
        self.setupUi(self)

        wdg = ResourceManagerWidget(resourceTypes)
        self.wdgCentral.layout().addWidget(wdg)
        self.wdgCentral.layout().addWidget(vspacer())

    def display(self):
        self.exec()


class MissingResourceManagerDialog(QDialog, Ui_ResourceManagerDialog):
    def __init__(self, resourceTypes: List[ResourceType], parent=None):
        super(MissingResourceManagerDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Resource is missing')

        self._label = QLabel()
        self._label.setWordWrap(True)
        self._label.setText(
            "Additional resources are necessary to perform this action." +
            " Please click download to proceed (internet access is necessary)")
        italic(self._label)

        self.wdgCentral.layout().addWidget(self._label)
        self.wdgCentral.layout().addWidget(vspacer(40))
        wdg = ResourceManagerWidget(resourceTypes)
        self.wdgCentral.layout().addWidget(wdg)
        self.wdgCentral.layout().addWidget(vspacer())

    def display(self):
        self.exec()


def ask_for_resource(resource_type: ResourceType) -> bool:
    if not resource_manager.has_resource(resource_type):
        MissingResourceManagerDialog([resource_type]).display()
        if not resource_manager.has_resource(resource_type):
            return False

    return True
