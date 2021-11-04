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
from enum import Enum
from functools import partial

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QObject, QEvent, QTimer, QPoint, QPropertyAnimation, QPointF, QRectF, \
    QSequentialAnimationGroup, QEasingCurve, QSize
from PyQt5.QtGui import QKeySequence, QFont, QTextCursor, QTextBlockFormat, QTextCharFormat, QTextFormat, \
    QKeyEvent, QPaintEvent, QTextListFormat, QPainter, QBrush, QColor, QPen
from PyQt5.QtWidgets import QTextEdit, QFrame, QPushButton, QStylePainter, QStyleOptionButton, QStyle, QToolBar, \
    QAction, QActionGroup, QComboBox, QMenu, QCheckBox
from overrides import overrides

from src.main.python.plotlyst.view.common import line
from src.main.python.plotlyst.view.generated.rich_text_editor_widget_ui import Ui_RichTextEditor
from src.main.python.plotlyst.view.icons import IconRegistry


class AutoAdjustableTextEdit(QTextEdit):
    def __init__(self, parent=None, height: int = 40):
        super(AutoAdjustableTextEdit, self).__init__(parent)
        self.textChanged.connect(self._resizeToContent)
        self._minHeight = height
        self.setMaximumHeight(self._minHeight)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    @overrides
    def setText(self, text: str) -> None:
        self.setPlainText(text)

    @overrides
    def setPlainText(self, text: str) -> None:
        super(AutoAdjustableTextEdit, self).setPlainText(text)
        QTimer.singleShot(50, self._resizeToContent)

    def _resizeToContent(self):
        size = self.document().size()
        self.setMaximumHeight(max(self._minHeight, size.height()))


class RichTextEditor(QFrame, Ui_RichTextEditor):
    def __init__(self, parent=None):
        super(RichTextEditor, self).__init__(parent)
        self.setupUi(self)

        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet('.QToolBar {background-color: rgb(255, 255, 255);}')
        self.toolbar.layout().setContentsMargins(3, 3, 3, 3)
        self.toolbar.layout().setSpacing(5)
        self.layout().insertWidget(0, self.toolbar)
        self.textTitle = AutoAdjustableTextEdit()
        self.textTitle.setStyleSheet('border: 0px;')
        self.layout().insertWidget(1, self.textTitle)

        self.textEditor.cursorPositionChanged.connect(self._updateFormat)
        self.textEditor.installEventFilter(self)
        self.textEditor.setTabStopDistance(
            QtGui.QFontMetricsF(self.textEditor.font()).horizontalAdvance(' ') * 4)

        self.cbHeading = QComboBox()
        self.cbHeading.setStyleSheet('''
        QComboBox {
            border: 0px;
            padding: 1px 1px 1px 3px;
        }
        ''')

        self.cbHeading.addItem('Normal')
        self.cbHeading.addItem(IconRegistry.heading_1_icon(), '')
        self.cbHeading.addItem(IconRegistry.heading_2_icon(), '')
        self.cbHeading.addItem(IconRegistry.heading_3_icon(), '')
        self.cbHeading.setCurrentText('Normal')
        self.cbHeading.currentIndexChanged.connect(self._setHeading)

        self.actionBold = QAction(IconRegistry.from_name('fa5s.bold'), '')
        self.actionBold.triggered.connect(lambda x: self.textEditor.setFontWeight(QFont.Bold if x else QFont.Normal))
        self.actionBold.setCheckable(True)
        self.actionBold.setShortcut(QKeySequence.Bold)

        self.actionItalic = QAction(IconRegistry.from_name('fa5s.italic'), '')
        self.actionItalic.triggered.connect(self.textEditor.setFontItalic)
        self.actionItalic.setCheckable(True)
        self.actionItalic.setShortcut(QKeySequence.Italic)

        self.actionUnderline = QAction(IconRegistry.from_name('fa5s.underline'), '')
        self.actionUnderline.triggered.connect(self.textEditor.setFontUnderline)
        self.actionUnderline.setCheckable(True)
        self.actionUnderline.setShortcut(QKeySequence.Underline)

        self.actionAlignLeft = QAction(IconRegistry.from_name('fa5s.align-left'), '')
        self.actionAlignLeft.triggered.connect(lambda: self.textEditor.setAlignment(Qt.AlignLeft))
        self.actionAlignLeft.setCheckable(True)
        self.actionAlignLeft.setChecked(True)
        self.actionAlignLeft.setShortcut(QKeySequence.Underline)
        self.actionAlignCenter = QAction(IconRegistry.from_name('fa5s.align-center'), '')
        self.actionAlignCenter.triggered.connect(lambda: self.textEditor.setAlignment(Qt.AlignCenter))
        self.actionAlignCenter.setCheckable(True)
        self.actionAlignCenter.setShortcut(QKeySequence.Underline)
        self.actionAlignRight = QAction(IconRegistry.from_name('fa5s.align-right'), '')
        self.actionAlignRight.triggered.connect(lambda: self.textEditor.setAlignment(Qt.AlignRight))
        self.actionAlignRight.setCheckable(True)
        self.actionAlignRight.setShortcut(QKeySequence.Underline)

        self.actionInsertList = QAction(IconRegistry.from_name('fa5s.list'), '')
        self.actionInsertList.triggered.connect(
            lambda: self.textEditor.textCursor().insertList(QTextListFormat.ListDisc))
        self.actionInsertNumberedList = QAction(IconRegistry.from_name('fa5s.list-ol'), '')
        self.actionInsertNumberedList.triggered.connect(
            lambda: self.textEditor.textCursor().insertList(QTextListFormat.ListDecimal))

        self.actionGroupAlignment = QActionGroup(self.toolbar)
        self.actionGroupAlignment.addAction(self.actionAlignLeft)
        self.actionGroupAlignment.addAction(self.actionAlignCenter)
        self.actionGroupAlignment.addAction(self.actionAlignRight)

        self.toolbar.addWidget(self.cbHeading)
        self.toolbar.addAction(self.actionBold)
        self.toolbar.addAction(self.actionItalic)
        self.toolbar.addAction(self.actionUnderline)
        self.toolbar.addWidget(line(vertical=True))
        self.toolbar.addAction(self.actionAlignLeft)
        self.toolbar.addAction(self.actionAlignCenter)
        self.toolbar.addAction(self.actionAlignRight)
        self.toolbar.addWidget(line(vertical=True))
        self.toolbar.addAction(self.actionInsertList)
        self.toolbar.addAction(self.actionInsertNumberedList)

    def setText(self, content: str, title: str = '', title_read_only: bool = False):
        self.textEditor.setHtml(content)
        self.textEditor.setFocus()
        self.textTitle.setHtml(f'''
                            <style>
                                h1 {{text-align: center;}}
                                </style>
                            <h1>{title}</h1>''')
        self.textTitle.setReadOnly(title_read_only)

    def setTitleVisible(self, visible: bool):
        self.textTitle.setVisible(visible)

    def clear(self):
        self.textEditor.clear()
        self.textTitle.clear()

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(event, QKeyEvent):
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
                cursor = self.textEditor.textCursor()
                _list = cursor.block().textList()
                if _list and _list.count() > 1:
                    cursor.beginEditBlock()
                    block = cursor.block()
                    _list.remove(block)
                    _list.format().setIndent(_list.format().indent() + 1)
                    cursor.insertList(_list.format())

                    cursor.endEditBlock()
                    return True
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Return:
                cursor = self.textEditor.textCursor()
                level = cursor.blockFormat().headingLevel()
                if level > 0:  # heading
                    cursor.insertBlock()
                    self.cbHeading.setCurrentIndex(0)
                    self._setHeading()
                    return True
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Slash:
                self._showCommands()

        return super(RichTextEditor, self).eventFilter(watched, event)

    def _updateFormat(self):
        self.actionBold.setChecked(self.textEditor.fontWeight() == QFont.Bold)
        self.actionItalic.setChecked(self.textEditor.fontItalic())
        self.actionUnderline.setChecked(self.textEditor.fontUnderline())

        self.actionAlignLeft.setChecked(self.textEditor.alignment() == Qt.AlignLeft)
        self.actionAlignCenter.setChecked(self.textEditor.alignment() == Qt.AlignCenter)
        self.actionAlignRight.setChecked(self.textEditor.alignment() == Qt.AlignRight)

        self.cbHeading.blockSignals(True)
        cursor = self.textEditor.textCursor()
        level = cursor.blockFormat().headingLevel()
        self.cbHeading.setCurrentIndex(level)
        self.cbHeading.blockSignals(False)

    def _setHeading(self):
        cursor: QTextCursor = self.textEditor.textCursor()
        cursor.beginEditBlock()

        blockFormat: QTextBlockFormat = cursor.blockFormat()
        blockFormat.setObjectIndex(-1)
        headingLevel = self.cbHeading.currentIndex()
        blockFormat.setHeadingLevel(headingLevel)
        cursor.setBlockFormat(blockFormat)
        sizeAdjustment = 5 - headingLevel if headingLevel else 0

        charFormat = QTextCharFormat()
        charFormat.setFontWeight(QFont.Bold if headingLevel else QFont.Normal)
        charFormat.setProperty(QTextFormat.FontSizeAdjustment, sizeAdjustment)
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.mergeCharFormat(charFormat)
        self.textEditor.mergeCurrentCharFormat(charFormat)

        cursor.endEditBlock()

    def _showCommands(self):
        def trigger(func):
            self.textEditor.textCursor().deletePreviousChar()
            func()

        rect = self.textEditor.cursorRect(self.textEditor.textCursor())

        menu = QMenu(self.textEditor)
        menu.addAction(IconRegistry.heading_1_icon(), '', partial(trigger, lambda: self.cbHeading.setCurrentIndex(1)))
        menu.addAction(IconRegistry.heading_2_icon(), '', partial(trigger, lambda: self.cbHeading.setCurrentIndex(2)))

        menu.popup(self.textEditor.viewport().mapToGlobal(QPoint(rect.x(), rect.y())))


class RotatedButtonOrientation(Enum):
    VerticalTopToBottom = 0
    VerticalBottomToTop = 1


class RotatedButton(QPushButton):
    def __init__(self, parent=None):
        super(RotatedButton, self).__init__(parent)
        self._orientation = RotatedButtonOrientation.VerticalTopToBottom

    def setOrientation(self, orientation: RotatedButtonOrientation):
        self._orientation = orientation
        self.update()

    @overrides
    def paintEvent(self, event: QPaintEvent):
        painter = QStylePainter(self)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        if self._orientation == RotatedButtonOrientation.VerticalTopToBottom:
            painter.rotate(90)
            painter.translate(0, -1 * self.width())
        else:
            painter.rotate(-90)
            painter.translate(-1 * self.height(), 0)
        option.rect = option.rect.transposed()
        painter.drawControl(QStyle.CE_PushButton, option)

    def sizeHint(self):
        size = super(RotatedButton, self).sizeHint()
        size.transpose()
        return size


class Toggle(QCheckBox):
    _transparent_pen = QPen(Qt.transparent)
    _light_grey_pen = QPen(Qt.lightGray)

    def __init__(self, parent=None, bar_color=Qt.gray, checked_color="#00B0FF", handle_color=Qt.white):
        super().__init__(parent)

        # Save our properties on the object via self, so we can access them later
        # in the paintEvent.
        self._bar_brush = QBrush(bar_color)
        self._bar_checked_brush = QBrush(QColor(checked_color).lighter())

        self._handle_brush = QBrush(handle_color)
        self._handle_checked_brush = QBrush(QColor(checked_color))

        # Setup the rest of the widget.

        self.setContentsMargins(8, 0, 8, 0)
        self._handle_position = 0

        self.stateChanged.connect(self.handle_state_change)

    @overrides
    def sizeHint(self):
        return QSize(58, 45)

    @overrides
    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    @overrides
    def paintEvent(self, e: QPaintEvent):

        contRect = self.contentsRect()
        handleRadius = round(0.24 * contRect.height())

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(self._transparent_pen)
        barRect = QRectF(
            0, 0,
            contRect.width() - handleRadius, 0.40 * contRect.height()
        )
        barRect.moveCenter(contRect.center())
        rounding = barRect.height() / 2

        # the handle will move along this line
        trailLength = contRect.width() - 2 * handleRadius
        xPos = contRect.x() + handleRadius + trailLength * self._handle_position

        if self.isChecked():
            p.setBrush(self._bar_checked_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setBrush(self._handle_checked_brush)

        else:
            p.setBrush(self._bar_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setPen(self._light_grey_pen)
            p.setBrush(self._handle_brush)

        p.drawEllipse(
            QPointF(xPos, barRect.center().y()),
            handleRadius, handleRadius)

        p.end()

    def handle_state_change(self, value):
        self._handle_position = 1 if value else 0

    @property
    def handle_position(self):
        return self._handle_position

    @handle_position.setter
    def handle_position(self, pos):
        """change the property
        we need to trigger QWidget.update() method, either by:
            1- calling it here [ what we're doing ].
            2- connecting the QPropertyAnimation.valueChanged() signal to it.
        """
        self._handle_position = pos
        self.update()

    @property
    def pulse_radius(self):
        return self._pulse_radius

    @pulse_radius.setter
    def pulse_radius(self, pos):
        self._pulse_radius = pos
        self.update()


class AnimatedToggle(Toggle):
    _transparent_pen = QPen(Qt.transparent)
    _light_grey_pen = QPen(Qt.lightGray)

    def __init__(self, *args, pulse_unchecked_color="#44999999",
                 pulse_checked_color="#4400B0EE", **kwargs):

        self._pulse_radius = 0

        super().__init__(*args, **kwargs)

        self.animation = QPropertyAnimation(self, b"handle_position", self)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setDuration(200)  # time in ms

        self.pulse_anim = QPropertyAnimation(self, b"pulse_radius", self)
        self.pulse_anim.setDuration(350)  # time in ms
        self.pulse_anim.setStartValue(10)
        self.pulse_anim.setEndValue(20)

        self.animations_group = QSequentialAnimationGroup()
        self.animations_group.addAnimation(self.animation)
        self.animations_group.addAnimation(self.pulse_anim)

        self._pulse_unchecked_animation = QBrush(QColor(pulse_unchecked_color))
        self._pulse_checked_animation = QBrush(QColor(pulse_checked_color))

    def handle_state_change(self, value):
        self.animations_group.stop()
        if value:
            self.animation.setEndValue(1)
        else:
            self.animation.setEndValue(0)
        self.animations_group.start()

    @overrides
    def paintEvent(self, e: QPaintEvent):
        contRect = self.contentsRect()
        handleRadius = round(0.24 * contRect.height())

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(self._transparent_pen)
        barRect = QRectF(
            0, 0,
            contRect.width() - handleRadius, 0.40 * contRect.height()
        )
        barRect.moveCenter(contRect.center())
        rounding = barRect.height() / 2

        # the handle will move along this line
        trailLength = contRect.width() - 2 * handleRadius

        xPos = contRect.x() + handleRadius + trailLength * self._handle_position

        if self.pulse_anim.state() == QPropertyAnimation.Running:
            p.setBrush(
                self._pulse_checked_animation if
                self.isChecked() else self._pulse_unchecked_animation)
            p.drawEllipse(QPointF(xPos, barRect.center().y()),
                          self._pulse_radius, self._pulse_radius)

        if self.isChecked():
            p.setBrush(self._bar_checked_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setBrush(self._handle_checked_brush)

        else:
            p.setBrush(self._bar_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setPen(self._light_grey_pen)
            p.setBrush(self._handle_brush)

        p.drawEllipse(
            QPointF(xPos, barRect.center().y()),
            handleRadius, handleRadius)

        p.end()
