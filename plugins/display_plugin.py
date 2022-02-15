from PyQt5 import QtGui
from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin
from PyQt5.QtGui import QIcon
from overrides import overrides

from src.main.python.plotlyst.view.widget.display import Subtitle


class SubtitlePlugin(QPyDesignerCustomWidgetPlugin):
    def __init__(self, parent=None):
        super(SubtitlePlugin, self).__init__(parent)
        self.initialized = False

    def initialize(self, core):
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        return self.initialized

    @overrides
    def createWidget(self, parent):
        return Subtitle(parent=parent)

    @overrides
    def name(self):
        return "Subtitle"

    @overrides
    def group(self):
        return "Plotlyst"

    @overrides
    def toolTip(self):
        return "Subtitle display widget"

    @overrides
    def whatsThis(self) -> str:
        return ''

    @overrides
    def isContainer(self):
        return False

    def icon(self) -> QtGui.QIcon:
        return QIcon()

    @overrides
    def domXml(self):
        return '<widget class="Subtitle" name="subtitle">\n</widget>'

    @overrides
    def includeFile(self):
        return "src.main.python.plotlyst.view.widget.display"
