from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPaintEvent, QPainter, QPen
from PyQt5.QtWidgets import QWidget, QHeaderView
from overrides import overrides

from novel_outliner.core.domain import Novel
from novel_outliner.model.report import StoryLinesScenesDistributionTableModel
from novel_outliner.view.generated.reports_view_ui import Ui_ReportsView


class ReportsView:
    def __init__(self, novel: Novel):
        self.widget = QWidget()
        self.ui = Ui_ReportsView()
        self.ui.setupUi(self.widget)

        self.story_line_report_model = StoryLinesScenesDistributionTableModel(novel)
        self.ui.tblStoryMap.setModel(self.story_line_report_model)

        self.ui.tblStoryMap.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        self.ui.tabWidget.addTab(StoryLinesMapWidget(novel), 'Story Lines Map')
        self.ui.tabWidget.setCurrentIndex(2)


class StoryLinesMapWidget(QWidget):

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent=None)
        self.setMouseTracking(True)
        self.novel = novel

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
            painter.setPen(QPen(Qt.red, 4, Qt.SolidLine))
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

        # painter.drawPixmap(0, 0, 32, 32,
        #                    avatars.pixmap(self.novel.characters[0]).scaled(32, 32, Qt.KeepAspectRatio,
        #                                                                    Qt.SmoothTransformation))
