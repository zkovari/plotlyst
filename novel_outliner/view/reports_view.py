from typing import Dict

from PyQt5.QtChart import QPieSeries, QChart, QChartView
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPaintEvent, QPainter, QPen, QPainterPath, QPixmap
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QMenu, QAction, QApplication, QVBoxLayout
from overrides import overrides

from novel_outliner.core.domain import Novel
from novel_outliner.view.generated.reports_view_ui import Ui_ReportsView


class ReportsView:
    def __init__(self, novel: Novel):
        self.widget = QWidget()
        self.ui = Ui_ReportsView()
        self.ui.setupUi(self.widget)

        layout = QVBoxLayout()
        layout.addWidget(StoryLinesLinearMapWidget(novel))
        layout.addWidget(StoryLinesMapWidget(novel))
        self.ui.tabStoryMap.setLayout(layout)

        pov_number = {}
        for scene in novel.scenes:
            if scene.pov and scene.pov.name not in pov_number.keys():
                pov_number[scene.pov.name] = 0
            if scene.pov:
                pov_number[scene.pov.name] += 1

        series = QPieSeries()
        for k, v in pov_number.items():
            slice = series.append(k, v)
            slice.setLabelVisible(True)

        for slice in series.slices():
            slice.setLabel(slice.label() + " {:.1f}%".format(100 * slice.percentage()))

        chart = QChart()
        chart.legend().hide()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("POV Distribution")

        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)

        layout = QHBoxLayout()
        layout.addWidget(chartview)

        # series.setMarkerShape(QScatterSeries.MarkerShapeCircle)

        # series = QScatterSeries()
        # series.append(0, 6)
        # series.append(2, 4)
        # series.append(3, 8)
        # series.append(7, 4)
        # series.append(10, 5)
        #
        # series << QPointF(11, 1) << QPointF(13, 3) << QPointF(17, 6) << QPointF(18, 3) << QPointF(20, 2)
        #
        # chart2 = QChart()
        # chart2.addSeries(series)
        # # chart2.createDefaultAxes()
        #
        # y_axis = QValueAxis()
        # y_axis.setMin(0)
        # y_axis.setMax(10)
        # x_axis = QValueAxis()
        # x_axis.setMin(0)
        # x_axis.setMax(25)
        # chart2.setAnimationOptions(QChart.SeriesAnimations)
        # chart2.setTitle("Line Chart Example")
        # chart2.addAxis(y_axis, Qt.AlignLeft)
        # chart2.addAxis(x_axis, Qt.AlignBottom)
        # chart2.legend().setVisible(False)
        # chart2.legend().setAlignment(Qt.AlignBottom)
        #
        # chartview2 = QChartView(chart2)
        # chartview2.setRenderHint(QPainter.Antialiasing)
        # layout.addWidget(chartview2)
        self.ui.tabCharacters.setLayout(layout)
        # self.ui.tabWidget.addTab(layout.widget(), 'Characters')

        self.ui.tabWidget.setCurrentIndex(3)


class StoryLinesMapWidget(QWidget):
    colors = [Qt.red, Qt.blue, Qt.green, Qt.magenta, Qt.darkBlue, Qt.darkGreen]

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent=parent)
        self.setMouseTracking(True)
        self.novel = novel
        self._scene_coord_y: Dict[int, int] = {}

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        rect = self.rect()
        h = rect.height()
        w = rect.width()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for i, story in enumerate(self.novel.story_lines):
            y = 75 * (i + 1)
            path = QPainterPath()
            painter.setPen(QPen(self.colors[i], 4, Qt.SolidLine))
            path.moveTo(0, y)
            path.lineTo(5, y)

            for j, scene in enumerate(self.novel.scenes):
                x = 25 * (j + 1)
                if story in scene.story_lines:
                    if j not in self._scene_coord_y.keys():
                        self._scene_coord_y[j] = y
                    if i == 1 and j == 2:
                        path.arcTo(x, self._scene_coord_y[j], 20, 20, 25, 25)
                    else:
                        path.lineTo(x, self._scene_coord_y[j])
                    painter.drawPath(path)

        for j, scene in enumerate(self.novel.scenes):
            x = 25 * (j + 1)
            if not j in self._scene_coord_y.keys():
                continue
            if len(scene.story_lines) == 1:
                painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
                painter.setBrush(Qt.black)
                painter.drawEllipse(x, self._scene_coord_y[j] - 7, 14, 14)
            else:
                painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
                painter.setBrush(Qt.white)
                painter.drawEllipse(x, self._scene_coord_y[j] - 10, 20, 20)


class StoryLinesLinearMapWidget(QWidget):
    colors = [Qt.red, Qt.blue, Qt.green, Qt.magenta, Qt.darkBlue, Qt.darkGreen]

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent=parent)
        self.setMouseTracking(True)
        self.novel = novel

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu_requested)

    # def event(self, event: QEvent) -> bool:
    #     if event.type() == QEvent.ToolTip:
    #         pos: QPoint = event.pos()
    #         print(pos)
    #         index = int((pos.y() / 75) - 1)
    #         self.setToolTip(self.novel.story_lines[index].text)
    #
    #         return super().event(event)
    #     return super().event(event)

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        rect = self.rect()
        h = rect.height()
        w = rect.width()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for i, story in enumerate(self.novel.story_lines):
            y = 75 * (i + 1)
            painter.setPen(QPen(self.colors[i], 4, Qt.SolidLine))
            painter.drawLine(0, y, w, y)
            painter.setPen(QPen(Qt.black, 5, Qt.SolidLine))
            painter.drawText(5, y - 15, story.text)

            for j, scene in enumerate(self.novel.scenes):
                x = 25 * (j + 1)
                if story in scene.story_lines:
                    if len(scene.story_lines) == 1:
                        painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
                        painter.setBrush(Qt.black)
                        painter.drawEllipse(x, y - 7, 14, 14)
                    else:
                        painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
                        painter.setBrush(Qt.white)
                        painter.drawEllipse(x, y - 10, 20, 20)

    def _context_menu_requested(self, pos: QPoint):
        menu = QMenu(self)

        wip_action = QAction('Copy image', menu)
        wip_action.triggered.connect(self._copy_image)
        menu.addAction(wip_action)

        menu.popup(self.mapToGlobal(pos))

    def _copy_image(self):
        clipboard = QApplication.clipboard()
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        clipboard.setPixmap(pixmap)
