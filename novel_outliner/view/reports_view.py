from PyQt5.QtChart import QPieSeries, QChart, QChartView
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget, QHBoxLayout

from novel_outliner.core.client import client
from novel_outliner.core.domain import Novel, Scene
from novel_outliner.model.novel import NovelStoryLinesListModel
from novel_outliner.view.generated.reports_view_ui import Ui_ReportsView


class ReportsView:
    def __init__(self, novel: Novel):
        self.widget = QWidget()
        self.ui = Ui_ReportsView()
        self.ui.setupUi(self.widget)
        self.novel = novel
        self.scene_selected = None

        self.ui.storyLinesMap.novel = novel
        self.ui.storyLinesLinearMap.novel = novel
        self.ui.storyLinesLinearMap.scene_selected.connect(self._on_scene_selected)
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

        self.ui.tabCharacters.setLayout(layout)

        self.ui.tabWidget.setCurrentIndex(3)
        self.story_line_model = NovelStoryLinesListModel(self.novel)
        self.story_line_model.selection_changed.connect(self._story_line_selection_changed)
        self.ui.listView.setModel(self.story_line_model)

    def _on_scene_selected(self, scene: Scene):
        self.scene_selected = scene
        self.ui.lineEdit.setText(scene.title)
        self.story_line_model.selected.clear()
        for story_line in scene.story_lines:
            self.story_line_model.selected.add(story_line)
        self.story_line_model.modelReset.emit()

    def _story_line_selection_changed(self):
        if not self.scene_selected:
            return
        self.scene_selected.story_lines.clear()
        for story_line in self.story_line_model.selected:
            self.scene_selected.story_lines.append(story_line)

        client.update_scene(self.scene_selected)
        self.ui.storyLinesLinearMap.repaint()
        self.ui.storyLinesMap.repaint()
