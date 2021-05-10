from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHeaderView, QGraphicsScene, QFrame

from novel_outliner.core.domain import Novel, Scene
from novel_outliner.model.scenes_model import ScenesTableModel
from novel_outliner.model.timeline_model import TimelineScenesFilterProxyModel
from novel_outliner.view.generated.scene_card_widget_ui import Ui_SceneCardWidget
from novel_outliner.view.generated.timeline_view_ui import Ui_TimelineView


class TimelineView:

    def __init__(self, novel: Novel):
        self.widget = QWidget()
        self.ui = Ui_TimelineView()
        self.ui.setupUi(self.widget)
        self.novel = novel

        self.model = ScenesTableModel(self.novel)
        self._proxy = TimelineScenesFilterProxyModel()
        self._proxy.setSourceModel(self.model)
        self._proxy.setSortCaseSensitivity(Qt.CaseInsensitive)
        self._proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._proxy.sort(ScenesTableModel.ColTime, Qt.AscendingOrder)
        self.ui.tblTimelineScenes.setModel(self._proxy)

        self.ui.tblTimelineScenes.setColumnWidth(ScenesTableModel.ColTitle, 400)
        self.ui.tblTimelineScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColCharacters,
                                                                          QHeaderView.ResizeToContents)
        self.ui.tblTimelineScenes.hideColumn(ScenesTableModel.ColType)
        self.ui.tblTimelineScenes.horizontalHeader().swapSections(ScenesTableModel.ColPov, ScenesTableModel.ColTime)
        self.ui.tblTimelineScenes.horizontalHeader().swapSections(ScenesTableModel.ColTime,
                                                                  ScenesTableModel.ColCharacters)
        self.refresh()

    def refresh(self):
        # for row in range(self._proxy.rowCount()):
        #     self.ui.tblTimelineScenes.setIndexWidget(self._proxy.index(row, ScenesTableModel.ColCharacters),
        #                                              SceneCharactersWidget(
        #                                                  self._proxy.index(row, 0).data(ScenesTableModel.SceneRole)))

        scene = QGraphicsScene()
        scenes = [x for x in self.novel.scenes if x.day]
        scenes = sorted(scenes, key=lambda x: x.day)

        scene.addRect(-10, -500, 20, len(scenes) * 100, brush=Qt.darkRed)

        last_day = 0
        left = True
        x = -50
        for index, s in enumerate(scenes):
            if s.day != last_day:
                text = scene.addText(str(s.day))
                x = -50 if left else 50
                text.moveBy(x, -500 + index * 80)
                last_day = s.day
                left = not left
            scene_widget = SceneCardWidget(s)
            if x > 0:
                scene_x = x
            else:
                scene_x = x - scene_widget.size().width()

            item = scene.addWidget(scene_widget)
            item.moveBy(scene_x, -500 + index * 80 + 30)
            item.setToolTip(s.synopsis)

        self.ui.graphicsView.setScene(scene)


class SceneCardWidget(QFrame, Ui_SceneCardWidget):
    def __init__(self, scene: Scene, parent=None):
        super(SceneCardWidget, self).__init__(parent)
        self.setupUi(self)

        self.lblTitle.setText(scene.title)
        self.resize(len(scene.title) * 12, 40)

        self.setMaximumHeight(80)

        border = '4px'
        if scene.wip:
            color = 'yellow'
        elif scene.pivotal:
            color = 'red'
        else:
            color = '#8f8f91'
            border = '2px'
        self.setStyleSheet(f'''QFrame {{border: {border} solid {color};
            border-radius: 12px;
            background-color: white;
            }}
            QLabel {{
            border: 0px;
            border-radius: 0px;
            }}
        ''')
