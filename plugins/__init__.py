from PyQt5.QtGui import QIcon


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
