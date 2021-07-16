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
from PyQt5.QtWidgets import QWidget, QGraphicsScene, QFrame

from src.main.python.plotlyst.core.domain import Novel, Scene
from src.main.python.plotlyst.view.generated.scene_card_widget_ui import Ui_SceneCardWidget
from src.main.python.plotlyst.view.generated.timeline_view_ui import Ui_TimelineView
from src.main.python.plotlyst.view.icons import avatars


class TimelineView:
    colors = [Qt.red, Qt.blue, Qt.green, Qt.magenta, Qt.darkBlue, Qt.darkGreen]

    def __init__(self, novel: Novel):
        self.widget = QWidget()
        self.ui = Ui_TimelineView()
        self.ui.setupUi(self.widget)
        self.novel = novel

        self.refresh()

    def refresh(self):
        self._refresh_timeline()
        # self._refresh_events()

    def _refresh_timeline(self):
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
        self.ui.graphicsTimeline.setScene(scene)

    # def _refresh_events(self):
    #     scene = QGraphicsScene()
    #     scene.setSceneRect(0, 0, 5000, 5000)
    #
    #     sl_size = len(self.novel.story_lines)
    #     if not sl_size:
    #         return
    #     step = 500 / sl_size
    #     x = sl_size / 2 * -step
    #     for i, sl in enumerate(self.novel.story_lines):
    #         scene.addRect(x, 0, 20, 500, brush=self.colors[i])
    #         x += step

    # self.ui.graphicsEvents.setScene(scene)


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
            color = 'yellow'
        elif scene.pivotal:
            color = 'red'
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
