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
import random
from abc import abstractmethod
from enum import Enum, auto
from functools import partial
from typing import Tuple, Optional, Dict

from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QSpinBox, QSlider, QTextBrowser, QButtonGroup, QToolButton
from overrides import overrides
from qthandy import vbox, pointy, hbox, sp, vspacer, underline, decr_font, flow, clear_layout, margins
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import PLOTLYST_MAIN_COLOR
from src.main.python.plotlyst.core.help import enneagram_help
from src.main.python.plotlyst.core.template import SelectionItem, enneagram_field, TemplateField, mbti_field
from src.main.python.plotlyst.view.common import push_btn, action, tool_btn, label
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.style.base import apply_white_menu
from src.main.python.plotlyst.view.widget.button import SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.labels import TraitLabel


class LifeStage(Enum):
    Infancy = auto()
    Preschool = auto()
    Early_childhood = auto()
    Children = auto()
    Teenagers = auto()
    Early_adulthood = auto()
    Middle_adulthood = auto()
    Late_adulthood = auto()
    Senior = auto()

    def display_name(self) -> str:
        return self.name.replace('_', ' ')

    def range(self) -> Tuple[int, int]:
        if self == LifeStage.Infancy:
            return 0, 2
        elif self == LifeStage.Preschool:
            return 3, 5
        elif self == LifeStage.Early_childhood:
            return 6, 7
        elif self == LifeStage.Children:
            return 8, 12
        elif self == LifeStage.Teenagers:
            return 13, 19
        elif self == LifeStage.Early_adulthood:
            return 20, 30
        elif self == LifeStage.Middle_adulthood:
            return 31, 65
        elif self == LifeStage.Late_adulthood:
            return 65, 79
        elif self == LifeStage.Senior:
            return 80, 100

    def icon(self) -> str:
        if self == LifeStage.Infancy:
            return 'fa5s.baby'
        elif self == LifeStage.Preschool:
            return 'fa5s.child'
        elif self == LifeStage.Early_childhood:
            return 'fa5s.child'
        elif self == LifeStage.Children:
            return 'fa5s.child'
        elif self == LifeStage.Teenagers:
            return 'mdi.human'
        elif self == LifeStage.Early_adulthood:
            return 'ei.adult'
        elif self == LifeStage.Middle_adulthood:
            return 'ei.adult'
        elif self == LifeStage.Late_adulthood:
            return 'ei.adult'
        elif self == LifeStage.Senior:
            return 'mdi.human-cane'

    def description(self) -> str:
        if self == LifeStage.Infancy:
            return "Early bonding, motor and language development, sensory exploration."
        elif self == LifeStage.Preschool:
            return "Social and cognitive growth, school readiness, creative play."
        elif self == LifeStage.Early_childhood:
            return "Transition into formal schooling, moral and ethical development, continued play and creativity"
        elif self == LifeStage.Children:
            return "Development of competitiveness, skill building, and motivation"
        elif self == LifeStage.Teenagers:
            return "Exploration of identity, self-discovery, and peer relationships"
        elif self == LifeStage.Early_adulthood:
            return "Career and life planning, independence, and personal growth."
        elif self == LifeStage.Middle_adulthood:
            return "Coping with life transitions, self-reflection, and reassessment of goals"
        elif self == LifeStage.Late_adulthood:
            return "Retirement transition, legacy considerations, and life reflection."
        elif self == LifeStage.Senior:
            return "Health management, end-of-life planning, and legacy concerns."


class CharacterAgeEditor(QWidget):
    valueChanged = pyqtSignal(int)
    infiniteToggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._wdgEditor = QWidget()
        self._wdgHintDisplay = QWidget()
        hbox(self)
        self.layout().addWidget(self._wdgEditor)
        self.layout().addWidget(self._wdgHintDisplay)

        self._btnInfinite = tool_btn(IconRegistry.from_name('mdi.infinity', 'grey', PLOTLYST_MAIN_COLOR),
                                     checkable=True, transparent_=True,
                                     tooltip='Immortal or any character with an extraordinary lifespan')
        self._btnInfinite.installEventFilter(
            OpacityEventFilter(self._btnInfinite, leaveOpacity=0.7, ignoreCheckedButton=True))
        self._btnInfinite.toggled.connect(self._infiniteToggled)

        self._slider = QSlider(self)
        self._slider.setMinimum(1)
        self._slider.setMaximum(100)
        self._slider.setValue(1)
        sp(self._slider).v_exp()
        pointy(self._slider)

        self._spinbox = QSpinBox(self)
        self._spinbox.setPrefix('Age: ')
        self._spinbox.setMinimum(0)
        self._spinbox.setMaximum(65000)
        self._spinbox.setValue(0)

        self._btnStage = push_btn(text='Life stage', transparent_=True)
        self._menuStages = MenuWidget(self._btnStage)
        self._menuStages.addSection('Select a stage to generate an age')
        self._menuStages.addSeparator()
        self._addAction(LifeStage.Infancy)
        self._addAction(LifeStage.Preschool)
        self._addAction(LifeStage.Early_childhood)
        self._addAction(LifeStage.Children)
        self._addAction(LifeStage.Teenagers)
        self._addAction(LifeStage.Early_adulthood)
        self._addAction(LifeStage.Middle_adulthood)
        self._addAction(LifeStage.Late_adulthood)
        self._addAction(LifeStage.Senior)

        self._text = QTextBrowser()
        self._text.setMaximumSize(200, 150)
        self._text.setProperty('rounded', True)

        vbox(self._wdgHintDisplay)
        self._wdgHintDisplay.layout().addWidget(self._btnStage, alignment=Qt.AlignmentFlag.AlignCenter)
        self._wdgHintDisplay.layout().addWidget(self._text)

        vbox(self._wdgEditor)
        self._wdgEditor.layout().addWidget(self._btnInfinite, alignment=Qt.AlignmentFlag.AlignRight)
        self._wdgEditor.layout().addWidget(vspacer(20))
        self._wdgEditor.layout().addWidget(self._slider, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._wdgEditor.layout().addWidget(self._spinbox)

        self._slider.valueChanged.connect(self._sliderValueChanged)
        self._spinbox.valueChanged.connect(self._spinboxValueChanged)

    def value(self) -> int:
        return self._spinbox.value()

    def setValue(self, age: int):
        self._spinbox.setValue(age)

    def setInfinite(self, infinite: bool):
        self._btnInfinite.setChecked(infinite)

    @overrides
    def setFocus(self):
        self._spinbox.setFocus()

    def minimum(self) -> int:
        return self._spinbox.minimum()

    def _addAction(self, stage: LifeStage):
        self._menuStages.addAction(action(stage.display_name(), slot=partial(self._stageClicked, stage)))

    def _stageClicked(self, stage: LifeStage):
        if self._btnInfinite.isChecked():
            self._btnInfinite.setChecked(False)
            self.infiniteToggled.emit(False)

        range = stage.range()
        age = random.randint(range[0], range[1])
        self._slider.setValue(age)

    def _sliderValueChanged(self, value: int):
        if value != self._spinbox.value():
            if value == self._slider.maximum() and self._spinbox.value() >= value:
                return

            self._spinbox.setValue(value)

    def _spinboxValueChanged(self, value: int):
        if value != self._slider.value():
            if value > self._slider.maximum():
                self._slider.setValue(self._slider.maximum())
            else:
                self._slider.setValue(value)
        self._setStageFromAge(value)
        self.valueChanged.emit(value)

    def _infiniteToggled(self, toggled: bool):
        self._slider.setDisabled(toggled)
        self._spinbox.setDisabled(toggled)

        if toggled:
            self._btnStage.setText('Infinite')
            self._btnStage.setIcon(IconRegistry.from_name('mdi.infinity'))
            self._text.setText(self._btnInfinite.toolTip())
        else:
            self._btnStage.setText('Life stage')
            self._btnStage.setIcon(QIcon())
            self._text.clear()

            self._setStageFromAge(self._spinbox.value())

        self.infiniteToggled.emit(toggled)

    def _setStageFromAge(self, age: int):
        if age > 100:
            self._setStage(LifeStage.Senior)
            return

        for stage in LifeStage:
            range = stage.range()
            if range[0] <= age <= range[1]:
                self._setStage(stage)
                break

    def _setStage(self, stage: LifeStage):
        self._btnStage.setText(stage.display_name())
        self._btnStage.setIcon(IconRegistry.from_name(stage.icon()))
        self._text.setText(stage.description())


class PersonalitySelectorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._selected: Optional[SelectionItem] = None

        self.btnIgnore = push_btn(IconRegistry.from_name('ri.share-forward-fill'), 'Ignore', transparent_=True)
        underline(self.btnIgnore)
        self.btnIgnore.installEventFilter(OpacityEventFilter(self.btnIgnore))

        vbox(self)
        self.layout().addWidget(self.btnIgnore, alignment=Qt.AlignmentFlag.AlignRight)

    def value(self) -> SelectionItem:
        return self._selected

    def setValue(self, value: SelectionItem):
        pass

    def reset(self):
        pass


class EnneagramSelectorWidget(PersonalitySelectorWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.wdgSelector = QWidget()
        hbox(self.wdgSelector, 10, spacing=6)
        margins(self.wdgSelector, top=20, bottom=20)
        self.layout().addWidget(self.wdgSelector)
        self._buttons: Dict[str, QToolButton] = {}
        self.btnGroup = QButtonGroup()

        for item in enneagram_field.selections:
            self._addItem(item)

        self.title = label('', bold=True)
        self.layout().addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.text = QTextBrowser()
        self.layout().addWidget(self.text)

        self.wdgLabels = QWidget()
        flow(self.wdgLabels)
        self.layout().addWidget(self.wdgLabels)

        self.btnSelect = push_btn(IconRegistry.ok_icon('white'), 'Select enneagram', properties=['highlighted', 'base'])
        self.layout().addWidget(self.btnSelect, alignment=Qt.AlignmentFlag.AlignRight)

        self.btnGroup.buttons()[0].setChecked(True)

    @overrides
    def setValue(self, value: SelectionItem):
        self._selected = value
        self._buttons[value.text].setChecked(True)

    @overrides
    def reset(self):
        self.btnGroup.buttons()[0].setChecked(True)

    def _addItem(self, item: SelectionItem):
        btn = tool_btn(IconRegistry.from_name(item.icon, 'lightgrey', item.icon_color), checkable=True,
                       transparent_=True)
        btn.setIconSize(QSize(32, 32))
        btn.installEventFilter(OpacityEventFilter(btn, leaveOpacity=0.5, ignoreCheckedButton=True))
        btn.toggled.connect(partial(self._clicked, item))
        self.btnGroup.addButton(btn)
        self._buttons[item.text] = btn
        self.wdgSelector.layout().addWidget(btn)

    def _clicked(self, item: SelectionItem, checked: bool):
        if not checked:
            return

        self._selected = item
        self.title.setText(item.text)
        self.text.setText(enneagram_help.get(item.text, ''))
        clear_layout(self.wdgLabels)
        if 'positive' in item.meta.keys():
            for trait in item.meta['positive']:
                label = TraitLabel(trait)
                decr_font(label)
                self.wdgLabels.layout().addWidget(label)
        if 'negative' in item.meta.keys():
            for trait in item.meta['negative']:
                label = TraitLabel(trait, positive=False)
                decr_font(label)
                self.wdgLabels.layout().addWidget(label)


class MbtiSelectorWidget(PersonalitySelectorWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout().addWidget(label('mbti'))


class PersonalitySelector(SecondaryActionPushButton):
    selected = pyqtSignal(SelectionItem)
    ignored = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ignored = False

        self._selected: Optional[SelectionItem] = None
        self._items: Dict[str, SelectionItem] = {}
        for item in self.field().selections:
            self._items[item.text] = item

        self._menu = MenuWidget(self)
        apply_white_menu(self._menu)

    def value(self) -> Optional[str]:
        if self._ignored:
            return None
        return self._selected.text if self._selected else ''

    def setValue(self, value: str):
        self._selected = self._items.get(value)
        if self._selected:
            self.selector().setValue(self._selected)
            self._updateValue()
        else:
            self.selector().reset()
            self.setText(f'{self.field().name}...')
            self.setIcon(IconRegistry.empty_icon())

        self._ignored = False
        if value is None:
            self._updateIgnoredValue()

    @abstractmethod
    def field(self) -> TemplateField:
        pass

    @abstractmethod
    def selector(self) -> PersonalitySelectorWidget:
        pass

    def _updateValue(self):
        self.setText(self._selected.text)
        self.setIcon(IconRegistry.from_name(self._selected.icon, self._selected.icon_color))
        self.initStyleSheet(self._selected.icon_color, 'solid', 'black')

    def _updateIgnoredValue(self):
        self._ignored = True
        self.setIcon(IconRegistry.from_name('ei.remove-circle', 'grey'))
        self.initStyleSheet()

    def _ignoreClicked(self):
        self._menu.close()
        self._updateIgnoredValue()
        self.ignored.emit()

    def _selectionClicked(self):
        self._ignored = False
        self._menu.close()
        value = self.selector().value()
        self._selected = value
        self._updateValue()
        self.selected.emit(value)


class EnneagramSelector(PersonalitySelector):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._selector = EnneagramSelectorWidget(self)
        self._menu.addWidget(self._selector)
        self._selector.btnIgnore.clicked.connect(self._ignoreClicked)
        self._selector.btnIgnore.setToolTip('Ignore Enneagram personality type for this character')
        self._selector.btnSelect.clicked.connect(self._selectionClicked)

        self.setText('Enneagram...')

    @overrides
    def field(self) -> TemplateField:
        return enneagram_field

    @overrides
    def selector(self) -> PersonalitySelectorWidget:
        return self._selector


class MbtiSelector(PersonalitySelector):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._selector = MbtiSelectorWidget(self)
        self._menu.addWidget(self._selector)
        self._selector.btnIgnore.clicked.connect(self._ignoreClicked)

    @overrides
    def field(self) -> TemplateField:
        return mbti_field

    @overrides
    def selector(self) -> PersonalitySelectorWidget:
        return self._selector
