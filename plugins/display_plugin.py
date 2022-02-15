from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin
from overrides import overrides

from plugins import PluginBase
from src.main.python.plotlyst.view.widget.display import Subtitle


class DisplayPluginBase(PluginBase):

    def group(self):
        return "Plotlyst display"

    def includeFile(self):
        return "src.main.python.plotlyst.view.widget.display"


class SubtitlePlugin(QPyDesignerCustomWidgetPlugin, DisplayPluginBase):

    @overrides
    def createWidget(self, parent):
        return Subtitle(parent=parent)

    @overrides
    def name(self):
        return "Subtitle"

    @overrides
    def toolTip(self):
        return "Subtitle display widget"

    @overrides
    def domXml(self):
        return '<widget class="Subtitle" name="subtitle">\n</widget>'

    @overrides
    def includeFile(self):
        return "src.main.python.plotlyst.view.widget.display"
