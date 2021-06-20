from PyQt5.QtChart import QPieSeries, QChart, QChartView
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget

from novel_outliner.core.client import client
from novel_outliner.core.domain import Novel, Scene
from novel_outliner.model.novel import NovelStoryLinesListModel
from novel_outliner.view.generated.reports_view_ui import Ui_ReportsView
from novel_outliner.view.icons import IconRegistry


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
        self.ui.btnAct1.setIcon(IconRegistry.act_one_icon())
        self.ui.btnAct2.setIcon(IconRegistry.act_two_icon())
        self.ui.btnAct3.setIcon(IconRegistry.act_three_icon())
        self.ui.btnAct1.toggled.connect(self._update_characters_chart)
        self.ui.btnAct2.toggled.connect(self._update_characters_chart)
        self.ui.btnAct3.toggled.connect(self._update_characters_chart)

        self.pov_number = {}

        self.chart = QChart()
        self.chart.legend().hide()
        # self.chart.addSeries(series)
        self._update_characters_chart()
        self.chart.createDefaultAxes()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setTitle("POV Distribution")

        chartview = QChartView(self.chart)
        chartview.setRenderHint(QPainter.Antialiasing)

        self.ui.tabCharacters.layout().addWidget(chartview)

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

    def _update_characters_chart(self):
        for k in self.pov_number.keys():
            self.pov_number[k] = 0

        include_act1 = self.ui.btnAct1.isChecked()
        include_act2 = self.ui.btnAct2.isChecked()
        include_act3 = self.ui.btnAct3.isChecked()
        in_act_2 = False
        in_act_3 = False
        for scene in self.novel.scenes:
            if (include_act1 and not include_act2) or (include_act2 and in_act_2) or (include_act3 and in_act_3):
                if scene.pov and scene.pov.name not in self.pov_number.keys():
                    self.pov_number[scene.pov.name] = 0
                if scene.pov:
                    self.pov_number[scene.pov.name] += 1

            if scene.pivotal == 'First plot point':
                in_act_2 = True
            elif scene.pivotal == 'Dark moment':
                in_act_3 = True

        series = QPieSeries()
        for k, v in self.pov_number.items():
            slice = series.append(k, v)
            slice.setLabelVisible(True)

        for slice in series.slices():
            slice.setLabel(slice.label() + " {:.1f}%".format(100 * slice.percentage()))

        self.chart.removeAllSeries()
        self.chart.addSeries(series)
