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
from functools import partial
from typing import Dict, Optional

import qtanim
from PyQt6.QtCore import Qt, QEvent, pyqtSignal, QSize
from PyQt6.QtGui import QEnterEvent, QMouseEvent
from PyQt6.QtWidgets import QWidget, QSlider
from overrides import overrides
from qtanim import fade_in
from qthandy import hbox, spacer, sp, retain_when_hidden, bold, vbox, translucent, clear_layout
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.core.domain import Motivation, Novel, Scene
from src.main.python.plotlyst.view.common import push_btn, restyle, label, fade_out_and_gc, tool_btn
from src.main.python.plotlyst.view.generated.scene_goal_stakes_ui import Ui_GoalReferenceStakesEditor
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.style.base import apply_white_menu
from src.main.python.plotlyst.view.widget.button import ChargeButton
from src.main.python.plotlyst.view.widget.input import RemovalButton


class SceneAgendaEmotionEditor(QWidget):
    emotionChanged = pyqtSignal(int)
    emotionReset = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        hbox(self)
        sp(self).h_max()
        self._activated: bool = False

        self._icon = push_btn(IconRegistry.from_name('mdi.emoticon-neutral', 'lightgrey'),
                              transparent_=True)
        self._icon.setIconSize(QSize(32, 32))
        self._opacityFilter = OpacityEventFilter(self._icon)
        self._icon.clicked.connect(self._iconClicked)

        self._slider = QSlider()
        self._slider.setMinimum(0)
        self._slider.setMaximum(10)
        self._slider.setPageStep(1)
        self._slider.setMaximumWidth(100)
        self._slider.setValue(5)
        self._slider.setOrientation(Qt.Orientation.Horizontal)
        self._slider.valueChanged.connect(self._valueChanged)

        self._btnReset = RemovalButton()
        self._btnReset.clicked.connect(self._resetClicked)
        retain_when_hidden(self._btnReset)

        self.layout().addWidget(self._icon)
        self.layout().addWidget(self._slider)
        self.layout().addWidget(spacer(max_stretch=5))
        self.layout().addWidget(self._btnReset, alignment=Qt.AlignmentFlag.AlignTop)
        # self.layout().addWidget(spacer())

        self.reset()

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        if self._activated:
            self._btnReset.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        self._btnReset.setVisible(False)

    def activate(self):
        self._activated = True
        self._slider.setVisible(True)
        self._btnReset.setVisible(True)
        self._icon.setText('')
        self._icon.removeEventFilter(self._opacityFilter)

    def reset(self):
        self._activated = False
        self._slider.setVisible(False)
        self._btnReset.setVisible(False)
        self._icon.setIcon(IconRegistry.from_name('mdi.emoticon-neutral', 'lightgrey'))
        self._icon.setText('Emotion')
        self._icon.installEventFilter(self._opacityFilter)

    def setValue(self, value: int):
        self.activate()
        if self._slider.value() == value:
            self.emotionChanged.emit(value)
        else:
            self._slider.setValue(value)

        self._btnReset.setHidden(True)

    def _iconClicked(self):
        if not self._activated:
            self.setValue(5)
            qtanim.fade_in(self._slider, 150)

    def _resetClicked(self):
        self.reset()
        self.emotionReset.emit()

    def _valueChanged(self, value: int):
        for v in range(0, 11):
            self._slider.setProperty(f'emotion_{v}', False)

        if value == 5:
            self._icon.setIcon(IconRegistry.from_name('mdi.emoticon-neutral', 'grey'))

        elif value <= 1:
            self._icon.setIcon(IconRegistry.from_name('mdi6.emoticon-angry', '#f25c54'))
        elif value == 2:
            self._icon.setIcon(IconRegistry.from_name('mdi6.emoticon-frown', '#f27059'))
        elif value == 3:
            self._icon.setIcon(IconRegistry.from_name('mdi6.emoticon-confused', '#f4845f'))
        elif value == 4:
            self._icon.setIcon(IconRegistry.from_name('mdi6.emoticon-sad', '#f79d65'))
        elif value == 6:
            self._icon.setIcon(IconRegistry.from_name('mdi6.emoticon-happy', '#74c69d'))
        elif value == 7:
            self._icon.setIcon(IconRegistry.from_name('mdi6.emoticon', '#52b788'))
        elif value == 8:
            self._icon.setIcon(IconRegistry.from_name('mdi6.emoticon-excited', '#40916c'))
        elif value >= 9:
            self._icon.setIcon(IconRegistry.from_name('mdi6.emoticon-cool', '#2d6a4f'))

        self._slider.setProperty(f'emotion_{value}', True)
        restyle(self._slider)

        self.emotionChanged.emit(value)


class MotivationDisplay(QWidget, Ui_GoalReferenceStakesEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._novel: Optional[Novel] = None
        self._scene: Optional[Scene] = None
        bold(self.lblTitle)

        self._sliders: Dict[Motivation, QSlider] = {
            Motivation.PHYSIOLOGICAL: self.sliderPhysiological,
            Motivation.SAFETY: self.sliderSecurity,
            Motivation.BELONGING: self.sliderBelonging,
            Motivation.ESTEEM: self.sliderEsteem,
            Motivation.SELF_ACTUALIZATION: self.sliderActualization,
            Motivation.SELF_TRANSCENDENCE: self.sliderTranscendence,
        }

        for slider in self._sliders.values():
            slider.setEnabled(False)
        translucent(self)

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        pass

    def setNovel(self, novel: Novel):
        self._novel = novel

    def setScene(self, scene: Scene):
        self._scene = scene
        self._refresh()

    def _refresh(self):
        for slider in self._sliders.values():
            slider.setValue(0)
        for scene in self._novel.scenes:
            if scene.agendas and scene.agendas[0].motivations:
                for mot, v in scene.agendas[0].motivations.items():
                    slider = self._sliders[Motivation(mot)]
                    slider.setValue(slider.value() + v)
            if scene is self._scene:
                break


class MotivationChargeLabel(QWidget):
    def __init__(self, motivation: Motivation, simplified: bool = False, parent=None):
        super().__init__(parent)
        self._motivation = motivation
        hbox(self, margin=0 if simplified else 1, spacing=0)
        if simplified:
            self._btn = tool_btn(IconRegistry.from_name(self._motivation.icon(), self._motivation.color()),
                                 icon_resize=False, transparent_=True)
        else:
            self._btn = push_btn(IconRegistry.from_name(self._motivation.icon(), self._motivation.color()),
                                 text=motivation.display_name(), icon_resize=False,
                                 transparent_=True)
        self._btn.setCursor(Qt.CursorShape.ArrowCursor)

        self._lblCharge = label('', description=True, italic=True)

        self.layout().addWidget(self._btn)
        self.layout().addWidget(self._lblCharge)

    def setCharge(self, charge: int):
        bold(self._btn, charge > 0)
        if charge == 0:
            self._lblCharge.clear()
        else:
            self._lblCharge.setText(f'+{charge}')


class MotivationCharge(QWidget):
    charged = pyqtSignal(int)
    MAX_CHARGE: int = 5

    def __init__(self, motivation: Motivation, parent=None):
        super().__init__(parent)
        hbox(self)
        self._motivation = motivation
        self._charge = 0

        self._label = MotivationChargeLabel(self._motivation)
        self._posCharge = ChargeButton(positive=True)
        self._posCharge.clicked.connect(lambda: self._changeCharge(1))
        self._negCharge = ChargeButton(positive=False)
        self._negCharge.clicked.connect(lambda: self._changeCharge(-1))
        self._negCharge.setHidden(True)

        self.layout().addWidget(self._label)
        self.layout().addWidget(spacer())
        self.layout().addWidget(self._negCharge)
        self.layout().addWidget(self._posCharge)

    def setValue(self, value: int):
        self._charge = min(value, self.MAX_CHARGE)
        self._update()

    def _changeCharge(self, charge: int):
        self._charge += charge
        self._update()

        self.charged.emit(self._charge)

    def _update(self):
        self._label.setCharge(self._charge)
        if self._charge == 0:
            self._negCharge.setHidden(True)
        else:
            self._negCharge.setVisible(True)
        if self._charge == self.MAX_CHARGE:
            self._posCharge.setHidden(True)
        else:
            self._posCharge.setVisible(True)


class MotivationEditor(QWidget):
    motivationChanged = pyqtSignal(Motivation, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        vbox(self)
        self.layout().addWidget(label("Does the character's motivation change?"))

        self._editors: Dict[Motivation, MotivationCharge] = {}
        self._addEditor(Motivation.PHYSIOLOGICAL)
        self._addEditor(Motivation.SAFETY)
        self._addEditor(Motivation.BELONGING)
        self._addEditor(Motivation.ESTEEM)
        self._addEditor(Motivation.SELF_ACTUALIZATION)
        self._addEditor(Motivation.SELF_TRANSCENDENCE)

    def _addEditor(self, motivation: Motivation):
        wdg = MotivationCharge(motivation)
        self._editors[motivation] = wdg
        wdg.charged.connect(partial(self.motivationChanged.emit, motivation))
        self.layout().addWidget(wdg)

    def reset(self):
        for editor in self._editors.values():
            editor.setValue(0)

    def setMotivations(self, motivations: Dict[Motivation, int]):
        self.reset()
        for mot, v in motivations.items():
            self._editors[mot].setValue(v)


class SceneAgendaMotivationEditor(QWidget):
    motivationChanged = pyqtSignal(Motivation, int)
    motivationReset = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        hbox(self)
        sp(self).h_max()
        self._activated: bool = False

        self._motivationDisplay = MotivationDisplay()
        self._motivationEditor = MotivationEditor()
        self._motivationEditor.motivationChanged.connect(self._valueChanged)

        self._wdgLabels = QWidget()
        hbox(self._wdgLabels, 0, 0)
        self._labels: Dict[Motivation, MotivationChargeLabel] = {}

        self._icon = push_btn(IconRegistry.from_name('fa5s.fist-raised', 'lightgrey'),
                              properties=['transparent', 'no-menu'])
        self._icon.setIconSize(QSize(32, 32))
        self._opacityFilter = OpacityEventFilter(self._icon)

        self._menu = MenuWidget(self._icon)
        apply_white_menu(self._menu)
        self._menu.addWidget(self._motivationDisplay)
        self._menu.addSeparator()
        self._menu.addWidget(self._motivationEditor)

        self._btnReset = RemovalButton()
        self._btnReset.clicked.connect(self._resetClicked)
        retain_when_hidden(self._btnReset)

        self.layout().addWidget(self._icon)
        self.layout().addWidget(self._wdgLabels)
        self.layout().addWidget(self._btnReset, alignment=Qt.AlignmentFlag.AlignTop)

        self.reset()

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        if self._activated:
            self._btnReset.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        self._btnReset.setVisible(False)

    def setNovel(self, novel: Novel):
        self._motivationDisplay.setNovel(novel)

    def setScene(self, scene: Scene):
        self._motivationDisplay.setScene(scene)

    def activate(self):
        self._activated = True
        self._btnReset.setVisible(True)
        self._icon.setText('')
        self._icon.removeEventFilter(self._opacityFilter)

    def reset(self):
        self._activated = False
        self._btnReset.setVisible(False)
        self._icon.setText('Motivation')
        self._icon.installEventFilter(self._opacityFilter)

        self._motivationEditor.reset()

        self._labels.clear()
        clear_layout(self._wdgLabels)

    def setValues(self, motivations: Dict[Motivation, int]):
        self.activate()
        self._motivationEditor.setMotivations(motivations)
        self._btnReset.setHidden(True)

        self._labels.clear()
        clear_layout(self._wdgLabels)
        for mot, v in motivations.items():
            self._updateLabels(mot, v)

    def _valueChanged(self, motivation: Motivation, value: int):
        self.motivationChanged.emit(motivation, value)
        self._updateLabels(motivation, value)

    def _updateLabels(self, motivation: Motivation, value: int):
        if motivation not in self._labels.keys():
            lbl = MotivationChargeLabel(motivation, simplified=True)
            self._labels[motivation] = lbl
            translucent(lbl, 0.8)
            self._wdgLabels.layout().addWidget(lbl)
            fade_in(lbl, 150)
        if value:
            self._labels[motivation].setCharge(value)
        else:
            fade_out_and_gc(self._wdgLabels, self._labels.pop(motivation))
        if self._labels and not self._activated:
            self.activate()
        elif not self._labels and self._activated:
            self.reset()

    def _resetClicked(self):
        self.reset()
        self.motivationReset.emit()