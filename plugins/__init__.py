from abc import abstractmethod

from PyQt6.QtGui import QIcon


class PluginBase:

    def __init__(self):
        self.initialized = False

    def initialize(self, core):
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def whatsThis(self) -> str:
        return ''

    def isContainer(self):
        return False

    def icon(self) -> QIcon:
        return QIcon()

    def createWidget(self, parent):
        return self.classType()(parent=parent)

    def name(self):
        return self.classType().__name__

    def toolTip(self):
        return f"{self.classType().__name__} widget"

    def domXml(self):
        return f'<widget class="{self.classType().__name__}" name="{self.classType().__name__.lower()}">\n</widget>'

    @abstractmethod
    def classType(self):
        pass
