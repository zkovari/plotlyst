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
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsScene, QFrame, QHeaderView
from overrides import overrides

from src.main.python.plotlyst.common import WIP_COLOR, PIVOTAL_COLOR
from src.main.python.plotlyst.core.domain import Novel, Scene
from src.main.python.plotlyst.events import CharacterChangedEvent, SceneChangedEvent, SceneDeletedEvent
from src.main.python.plotlyst.model.scenes_model import ScenesTableModel
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.generated.scene_card_widget_ui import Ui_SceneCardWidget
from src.main.python.plotlyst.view.generated.timeline_view_ui import Ui_TimelineView
from src.main.python.plotlyst.view.icons import avatars
from src.main.python.plotlyst.view.scenes_view import ScenesViewDelegate


class TimelineView(AbstractNovelView):
    colors = [Qt.red, Qt.blue, Qt.green, Qt.magenta, Qt.darkBlue, Qt.darkGreen]

    def __init__(self, novel: Novel):
        super().__init__(novel, [CharacterChangedEvent, SceneChangedEvent, SceneDeletedEvent])
        self.ui = Ui_TimelineView()
        self.ui.setupUi(self.widget)

        self.model = ScenesTableModel(self.novel)
        self.ui.tblScenes.setModel(self.model)
        for col in range(self.model.columnCount()):
            self.ui.tblScenes.hideColumn(col)
        self.ui.tblScenes.showColumn(ScenesTableModel.ColTitle)
        self.ui.tblScenes.showColumn(ScenesTableModel.ColTime)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColTime, 40)
        self.ui.tblScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColTitle, QHeaderView.Stretch)
        self._delegate = ScenesViewDelegate()

        self.ui.tblScenes.setItemDelegate(self._delegate)

        self._delegate.commitData.connect(self.refresh)

        self.refresh()

    @overrides
    def refresh(self):
        self.model.modelReset.emit()
        self._refresh_timeline()

    def _refresh_timeline(self):
        graphics_scene = QGraphicsScene()
        scenes = [x for x in self.novel.scenes if x.day]
        scenes = sorted(scenes, key=lambda x: x.day)
        graphics_scene.addRect(-10, -500, 20, len(scenes) * 100, brush=Qt.darkRed)
        last_day = 0
        left = True
        x = -50
        empty_days_count = 0
        for index, s in enumerate(scenes):
            if s.day != last_day:
                if s.day - 1 > last_day:
                    empty_days_count += 1
                text = graphics_scene.addText(str(s.day))
                x = -50 if left else 50
                text.moveBy(x, -500 + index * 80 + + empty_days_count * 80)
                last_day = s.day
                left = not left
            scene_widget = SceneCardWidget(s)
            if x > 0:
                scene_x = x
            else:
                scene_x = x - scene_widget.size().width()

            item = graphics_scene.addWidget(scene_widget)
            item.moveBy(scene_x, -500 + index * 80 + 30 + empty_days_count * 80)
            item.setToolTip(s.synopsis)
        self.ui.graphicsTimeline.setScene(graphics_scene)


class SceneCardWidget(QFrame, Ui_SceneCardWidget):
    def __init__(self, scene: Scene, parent=None):
        super(SceneCardWidget, self).__init__(parent)
        self.setupUi(self)
        self.setFrameShape(QFrame.StyledPanel)
        self.lblTitle.setText(scene.title)
        self.resize(len(scene.title) * 12, 40)

        if scene.pov:
            self.lblPic.setPixmap(avatars.pixmap(scene.pov).scaled(32, 32, Qt.KeepAspectRatio,
                                                                   Qt.SmoothTransformation))

        self.setMaximumHeight(80)

        border = '4px'
        if scene.wip:
            color = WIP_COLOR
        elif scene.beat:
            color = PIVOTAL_COLOR
        else:
            color = '#8f8f91'
            border = '2px'
        self.setStyleSheet(f'''QFrame {{border: {border} solid {color};
            border-radius: 12px;
            background-color: #9e87de;
            }}
            QLabel {{
            border: 0px;
            border-radius: 0px;
            }}
        ''')
