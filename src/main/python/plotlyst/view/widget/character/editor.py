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
from typing import Tuple, Optional, Dict, List

from PyQt6.QtCore import pyqtSignal, Qt, QSize, QObject, QEvent
from PyQt6.QtGui import QIcon, QColor, QPainter, QPaintEvent, QBrush, QResizeEvent
from PyQt6.QtWidgets import QWidget, QSpinBox, QSlider, QTextBrowser, QButtonGroup, QToolButton, QLabel, QSizePolicy, \
    QLineEdit
from overrides import overrides
from qthandy import vbox, pointy, hbox, sp, vspacer, underline, decr_font, flow, clear_layout, translucent, line, grid, \
    italic, spacer, transparent, ask_confirmation, incr_font, bold, margins, incr_icon
from qthandy.filter import OpacityEventFilter, VisibilityToggleEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import PLOTLYST_MAIN_COLOR, RELAXED_WHITE_COLOR, NEUTRAL_EMOTION_COLOR, \
    EMOTION_COLORS
from src.main.python.plotlyst.core.domain import BackstoryEvent, Character
from src.main.python.plotlyst.core.help import enneagram_help, mbti_help
from src.main.python.plotlyst.core.template import SelectionItem, enneagram_field, TemplateField, mbti_field
from src.main.python.plotlyst.view.common import push_btn, action, tool_btn, label, wrap, open_url, frame, restyle
from src.main.python.plotlyst.view.icons import IconRegistry, set_avatar
from src.main.python.plotlyst.view.style.base import apply_white_menu
from src.main.python.plotlyst.view.widget.button import SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.display import Icon
from src.main.python.plotlyst.view.widget.input import RemovalButton, AutoAdjustableTextEdit
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
        decr_font(self.btnIgnore)
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
        self.layout().addWidget(self.wdgSelector)
        self._buttons: Dict[str, QToolButton] = {}
        self.btnGroup = QButtonGroup()

        for item in enneagram_field.selections:
            self._addItem(item)

        self.layout().addWidget(line(color='lightgrey'))

        self.title = label('', h4=True)
        self.layout().addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.text = QTextBrowser()
        self.text.setProperty('transparent', True)
        self.layout().addWidget(wrap(self.text, margin_left=10, margin_right=10))

        self.wdgLabels = QWidget()
        flow(self.wdgLabels)
        self.layout().addWidget(wrap(self.wdgLabels, margin_left=10, margin_right=10, margin_bottom=10))

        self.btnSelect = push_btn(IconRegistry.ok_icon('white'), 'Select enneagram', properties=['positive', 'base'])
        self.layout().addWidget(self.btnSelect, alignment=Qt.AlignmentFlag.AlignRight)

        self.reset()

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
        btn.toggled.connect(partial(self._toggled, item))
        self.btnGroup.addButton(btn)
        self._buttons[item.text] = btn
        self.wdgSelector.layout().addWidget(btn)

    def _toggled(self, item: SelectionItem, checked: bool):
        if not checked:
            return

        self._selected = item
        self.title.setText(item.text)
        self.text.setText(enneagram_help.get(item.text, ''))
        clear_layout(self.wdgLabels)
        if 'positive' in item.meta.keys():
            for trait in item.meta['positive']:
                label = TraitLabel(trait)
                translucent(label, 0.8)
                decr_font(label)
                self.wdgLabels.layout().addWidget(label)
        if 'negative' in item.meta.keys():
            for trait in item.meta['negative']:
                label = TraitLabel(trait, positive=False)
                translucent(label, 0.8)
                decr_font(label)
                self.wdgLabels.layout().addWidget(label)


class MbtiSelectorWidget(PersonalitySelectorWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.wdgSelector = QWidget()
        grid(self.wdgSelector)
        self.layout().addWidget(self.wdgSelector)

        self._buttons: Dict[str, QToolButton] = {}
        self.btnGroup = QButtonGroup()

        for i, item in enumerate(mbti_field.selections):
            self._addItem(item, i)

        self.text = QTextBrowser()
        self.text.setProperty('transparent', True)
        self.layout().addWidget(wrap(self.text, margin_left=10, margin_right=10))

        self.btnSelect = push_btn(IconRegistry.ok_icon('white'), 'Select MBTI', properties=['positive', 'base'])

        self.wdgBottom = QWidget()
        hbox(self.wdgBottom)
        ref = push_btn(text='Source: truity.com', properties=['transparent', 'no-menu'])
        italic(ref)
        decr_font(ref)
        ref_menu = MenuWidget(ref)
        ref_menu.addSection('Browse personality types and tests on truity')
        ref_menu.addSeparator()
        ref_menu.addAction(action('Visit truity.com', IconRegistry.from_name('fa5s.external-link-alt'),
                                  slot=lambda: open_url('https://www.truity.com/')))
        ref.installEventFilter(OpacityEventFilter(ref, 0.8, 0.5))
        self.wdgBottom.layout().addWidget(ref, alignment=Qt.AlignmentFlag.AlignLeft)
        self.wdgBottom.layout().addWidget(self.btnSelect, alignment=Qt.AlignmentFlag.AlignRight)
        self.layout().addWidget(self.wdgBottom)

        self.reset()

    @overrides
    def reset(self):
        self.btnGroup.buttons()[0].setChecked(True)

    def _addItem(self, item: SelectionItem, index: int):
        btn = tool_btn(IconRegistry.from_name(item.icon, 'grey', item.icon_color), transparent_=True, checkable=True)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn.setText(item.text)
        btn.setIconSize(QSize(32, 32))
        btn.installEventFilter(OpacityEventFilter(btn, leaveOpacity=0.5, ignoreCheckedButton=True))
        btn.toggled.connect(partial(self._toggled, item))
        self.btnGroup.addButton(btn)
        self._buttons[item.text] = btn

        cluster = index // 4
        row = index % 2
        col = index % 4 // 2
        self.wdgSelector.layout().addWidget(btn, row, col + cluster * 2)

    def _toggled(self, item: SelectionItem, checked: bool):
        if not checked:
            return

        self._selected = item
        self.text.setText(mbti_help.get(item.text, ''))


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
        self._selector.btnIgnore.setToolTip('Ignore MBTI personality type for this character')
        self._selector.btnSelect.clicked.connect(self._selectionClicked)

        self.setText('MBTI...')

    @overrides
    def field(self) -> TemplateField:
        return mbti_field

    @overrides
    def selector(self) -> PersonalitySelectorWidget:
        return self._selector


class EmotionEditorSlider(QSlider):
    def __init__(self, parent=None):
        super().__init__(parent)

        pointy(self)
        self.setMinimum(0)
        self.setMaximum(10)
        self.setPageStep(1)
        self.setMaximumWidth(100)
        self.setValue(5)
        self.setOrientation(Qt.Orientation.Horizontal)
        self.valueChanged.connect(self._valueChanged)

    def _valueChanged(self, value: int):
        for v in range(0, 11):
            self.setProperty(f'emotion_{v}', False)

        self.setProperty(f'emotion_{value}', True)
        restyle(self)


class BackstoryEditorMenu(MenuWidget):
    emotionChanged = pyqtSignal(int)
    iconSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        wdgEmotion = QWidget()
        vbox(wdgEmotion, 1, 1)
        self._iconEmotion = Icon()
        self._iconEmotion.setIconSize(QSize(32, 32))
        self._iconEmotion.setIcon(IconRegistry.emotion_icon_from_feeling(5))
        self.emotionSlider = EmotionEditorSlider()
        self.emotionSlider.setMaximumWidth(200)
        self.emotionSlider.valueChanged.connect(self._emotionChanged)
        sp(self.emotionSlider).h_exp()
        wdgEmotion.layout().addWidget(self._iconEmotion, alignment=Qt.AlignmentFlag.AlignCenter)
        wdgEmotion.layout().addWidget(self.emotionSlider)
        self.wdgIcons = QWidget()
        self.wdgIcons.setMaximumHeight(200)
        flow(self.wdgIcons)
        self._addIcon('ri.calendar-event-fill')
        self._addIcon('fa5s.birthday-cake')
        self._addIcon('fa5s.graduation-cap')
        self._addIcon('fa5s.briefcase')
        self._addIcon('ei.heart')
        self._addIcon('fa5s.user-friends')
        self._addIcon('fa5s.skull-crossbones')
        self._addIcon('mdi.knife-military')
        self._addIcon('fa5s.car-crash')
        self._addIcon('mdi.ladder')
        self._addIcon('fa5s.heart-broken')
        self._addIcon('fa5s.award')
        self._addIcon('mdi6.human-male-female-child')
        self._addIcon('fa5s.home')
        self._addIcon('fa5s.gavel')
        self._addIcon('fa5s.gift')
        self._addIcon('fa5s.medkit')
        self._addIcon('ph.coin-fill')
        self._addIcon('fa5s.user-injured')
        self._addIcon('mdi.trophy-broken')

        self.addWidget(wdgEmotion)
        self.addWidget(self.wdgIcons)
        self.addSeparator()
        self.addAction(action('Custom icon...', IconRegistry.icons_icon()))

        self._freeze = False

    def setEmotion(self, value: int):
        self._freeze = True
        self.emotionSlider.setValue(value)
        self._freeze = False

    def _addIcon(self, icon: str):
        def select():
            self.iconSelected.emit(icon)
            self.close()

        btn = tool_btn(IconRegistry.from_name(icon), transparent_=True)
        btn.clicked.connect(select)
        incr_icon(btn, 4)
        self.wdgIcons.layout().addWidget(btn)

    def _emotionChanged(self, value: int):
        self._iconEmotion.setIcon(IconRegistry.emotion_icon_from_feeling(value))
        if not self._freeze:
            self.emotionChanged.emit(value)


class CharacterBackstoryCard(QWidget):
    edited = pyqtSignal()
    deleteRequested = pyqtSignal(object)
    relationChanged = pyqtSignal()

    def __init__(self, backstory: BackstoryEvent, parent=None):
        super(CharacterBackstoryCard, self).__init__(parent)
        self.backstory = backstory

        vbox(self)
        margins(self, top=18)

        self.cardFrame = frame()
        vbox(self.cardFrame)

        self.btnType = tool_btn(QIcon(), parent=self)
        self.btnType.setIconSize(QSize(24, 24))

        self.menu = BackstoryEditorMenu(self.btnType)
        self.menu.emotionChanged.connect(self._emotionChanged)
        self.menu.iconSelected.connect(self._iconChanged)

        self.btnRemove = RemovalButton()
        self.btnRemove.setVisible(False)
        self.btnRemove.clicked.connect(self._remove)

        self.lineKeyPhrase = QLineEdit()
        self.lineKeyPhrase.setPlaceholderText('Keyphrase')
        self.lineKeyPhrase.setProperty('transparent', True)
        self.lineKeyPhrase.textEdited.connect(self._keyphraseEdited)
        incr_font(self.lineKeyPhrase)
        bold(self.lineKeyPhrase)

        self.textSummary = AutoAdjustableTextEdit(height=40)
        self.textSummary.setPlaceholderText("Summarize this event")
        self.textSummary.setProperty('transparent', True)
        self.textSummary.setProperty('rounded', True)
        self.textSummary.textChanged.connect(self._synopsisChanged)

        wdgTop = QWidget()
        hbox(wdgTop, 0, 0)
        wdgTop.layout().addWidget(self.lineKeyPhrase)
        wdgTop.layout().addWidget(self.btnRemove, alignment=Qt.AlignmentFlag.AlignTop)
        self.cardFrame.layout().addWidget(wdgTop)
        self.cardFrame.setObjectName('cardFrame')
        self.cardFrame.layout().addWidget(self.textSummary)
        self.layout().addWidget(self.cardFrame)

        self.cardFrame.installEventFilter(VisibilityToggleEventFilter(self.btnRemove, self.cardFrame))

        self.btnType.raise_()

        self.setMinimumWidth(60)
        self.refresh()

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.btnType.setGeometry(self.width() // 2 - 18, 2, 36, 36)

    def refresh(self):
        self._refreshStyle()
        self.lineKeyPhrase.setText(self.backstory.keyphrase)
        self.textSummary.setPlainText(self.backstory.synopsis)
        self.menu.setEmotion(self.backstory.emotion)

    def _refreshStyle(self):
        bg_color = EMOTION_COLORS.get(self.backstory.emotion, NEUTRAL_EMOTION_COLOR)
        self.cardFrame.setStyleSheet(f'''
                            #cardFrame {{
                                border-top: 8px solid {bg_color};
                                border-bottom-left-radius: 12px;
                                border-bottom-right-radius: 12px;
                                background-color: #ffe8d6;
                                }}
                            ''')
        self.btnType.setStyleSheet(
            f'''
                    QToolButton {{
                            background-color: {RELAXED_WHITE_COLOR}; border: 3px solid {bg_color};
                            border-radius: 18px;
                            padding: 4px;
                        }}
                    QToolButton:hover {{
                        padding: 2px;
                    }}
                    ''')

        self.btnType.setIcon(IconRegistry.from_name(self.backstory.type_icon, bg_color))

    def _synopsisChanged(self):
        self.backstory.synopsis = self.textSummary.toPlainText()
        self.edited.emit()

    def _keyphraseEdited(self):
        self.backstory.keyphrase = self.lineKeyPhrase.text()
        self.edited.emit()

    def _emotionChanged(self, value: int):
        self.backstory.emotion = value
        self._refreshStyle()
        self.edited.emit()

    def _iconChanged(self, icon: str):
        self.backstory.type_icon = icon
        self.btnType.setIcon(IconRegistry.from_name(self.backstory.type_icon, EMOTION_COLORS[self.backstory.emotion]))
        self.edited.emit()

    def _remove(self):
        if self.backstory.synopsis and not ask_confirmation(f'Remove event "{self.backstory.keyphrase}"?'):
            return
        self.deleteRequested.emit(self)


class CharacterBackstoryEvent(QWidget):
    def __init__(self, backstory: BackstoryEvent, alignment: int = Qt.AlignmentFlag.AlignRight, parent=None):
        super(CharacterBackstoryEvent, self).__init__(parent)
        self.alignment = alignment
        self.card = CharacterBackstoryCard(backstory)

        self._layout = hbox(self, 0, 3)
        self.spacer = spacer()
        self.spacer.setFixedWidth(self.width() // 2 + 3)
        if self.alignment == Qt.AlignmentFlag.AlignRight:
            self.layout().addWidget(self.spacer)
            self._layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignLeft)
        elif self.alignment == Qt.AlignmentFlag.AlignLeft:
            self._layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignRight)
            self.layout().addWidget(self.spacer)
        else:
            self.layout().addWidget(self.card)

    def toggleAlignment(self):
        if self.alignment == Qt.AlignmentFlag.AlignLeft:
            self.alignment = Qt.AlignmentFlag.AlignRight
            self._layout.takeAt(0)
            self._layout.addWidget(self.spacer)
            self._layout.setAlignment(self.card, Qt.AlignmentFlag.AlignRight)
        else:
            self.alignment = Qt.AlignmentFlag.AlignLeft
            self._layout.takeAt(1)
            self._layout.insertWidget(0, self.spacer)
            self._layout.setAlignment(self.card, Qt.AlignmentFlag.AlignLeft)


class _ControlButtons(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        vbox(self)

        self.btnPlaceholderCircle = QToolButton(self)
        self.btnPlus = tool_btn(IconRegistry.plus_icon('white'), tooltip='Add new event')

        self.layout().addWidget(self.btnPlaceholderCircle)
        self.layout().addWidget(self.btnPlus)

        self.btnPlus.setHidden(True)

        bg_color = '#1d3557'
        for btn in [self.btnPlaceholderCircle, self.btnPlus]:
            btn.setStyleSheet(f'''
                QToolButton {{ background-color: {bg_color}; border: 1px;
                        border-radius: 13px; padding: 2px;}}
                QToolButton:pressed {{background-color: grey;}}
            ''')

        self.installEventFilter(self)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            self.btnPlaceholderCircle.setHidden(True)
            self.btnPlus.setVisible(True)
        elif event.type() == QEvent.Type.Leave:
            self.btnPlaceholderCircle.setVisible(True)
            self.btnPlus.setHidden(True)

        return super().eventFilter(watched, event)


class CharacterTimelineWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent=None):
        self._spacers: List[QWidget] = []
        super(CharacterTimelineWidget, self).__init__(parent)
        self.character: Optional[Character] = None
        self._layout = vbox(self, spacing=0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def setCharacter(self, character: Character):
        self.character = character
        self.refresh()

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        for sp in self._spacers:
            sp.setFixedWidth(self.width() // 2 + 3)

    def refreshCharacter(self):
        item = self._layout.itemAt(0)
        if item:
            wdg = item.widget()
            if isinstance(wdg, QLabel):
                set_avatar(wdg, self.character, 64)

    def refresh(self):
        if self.character is None:
            return
        self._spacers.clear()
        clear_layout(self.layout())

        lblCharacter = QLabel(self)
        lblCharacter.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        transparent(lblCharacter)
        set_avatar(lblCharacter, self.character, 64)

        self._layout.addWidget(lblCharacter, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        prev_alignment = None
        for i, backstory in enumerate(self.character.backstory):
            if prev_alignment is None:
                alignment = Qt.AlignmentFlag.AlignRight
            elif backstory.follow_up and prev_alignment:
                alignment = prev_alignment
            elif prev_alignment == Qt.AlignmentFlag.AlignLeft:
                alignment = Qt.AlignmentFlag.AlignRight
            else:
                alignment = Qt.AlignmentFlag.AlignLeft
            prev_alignment = alignment
            event = CharacterBackstoryEvent(backstory, alignment, parent=self)
            event.card.deleteRequested.connect(self._remove)

            self._spacers.append(event.spacer)
            event.spacer.setFixedWidth(self.width() // 2 + 3)

            self._addControlButtons(i)
            self._layout.addWidget(event)

            event.card.edited.connect(self.changed.emit)
            event.card.relationChanged.connect(self.changed.emit)
            event.card.relationChanged.connect(self.refresh)

        self._addControlButtons(-1)
        spacer_ = spacer(vertical=True)
        spacer_.setMinimumHeight(200)
        self.layout().addWidget(spacer_)

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor('#1d3557')))
        painter.drawRect(int(self.width() / 2) - 3, 64, 6, self.height() - 64)

        painter.end()

    def add(self, pos: int = -1):
        backstory = BackstoryEvent('', '', type_color=NEUTRAL_EMOTION_COLOR)
        if pos >= 0:
            self.character.backstory.insert(pos, backstory)
        else:
            self.character.backstory.append(backstory)
        self.refresh()
        self.changed.emit()

    def _remove(self, card: CharacterBackstoryCard):
        if card.backstory in self.character.backstory:
            self.character.backstory.remove(card.backstory)

        self.refresh()
        self.changed.emit()

    def _addControlButtons(self, pos: int):
        control = _ControlButtons(self)
        control.btnPlus.clicked.connect(partial(self.add, pos))
        self._layout.addWidget(control, alignment=Qt.AlignmentFlag.AlignHCenter)
