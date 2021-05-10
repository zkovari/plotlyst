from typing import List

from PyQt5.QtWidgets import QWidget

from novel_outliner.core.domain import Novel, Task
from novel_outliner.model.tasks_model import TasksTableModel
from novel_outliner.view.generated.tasks_widget_ui import Ui_TasksWidget


class TasksWidget(QWidget, Ui_TasksWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.novel = novel

        self.tasks: List[Task] = []
        self.model = TasksTableModel(self.tasks)
        self.tblTasks.setModel(self.model)
        self.tblTasks.setColumnWidth(TasksTableModel.ColType, 30)
        self.tblTasks.setColumnWidth(TasksTableModel.ColRef, 200)

        self.updateTasks()

    def updateTasks(self):
        self.tasks.clear()

        for scene in self.novel.scenes:
            if scene.wip:
                continue
            if not scene.pov:
                self.tasks.append(Task(f'POV is missing', reference=scene))
            if not scene.title or scene.title == 'Untitled':
                self.tasks.append(Task(f'Title is not specified', reference=scene))
            if not scene.beginning:
                self.tasks.append(Task(f'Beginning event is missing', reference=scene))
            if not scene.middle:
                self.tasks.append(Task(f'Middle event is missing', reference=scene))
            if not scene.end:
                self.tasks.append(Task(f'End event is missing', reference=scene))

        self.model.modelReset.emit()
