from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin
from overrides import overrides

from plugins import PluginBase
from src.main.python.plotlyst.view.widget.manuscript import ReadabilityWidget


class ManuscriptPluginBase(PluginBase):

    def group(self):
        return "Plotlyst manuscript"

    def includeFile(self):
        return "src.main.python.plotlyst.view.widget.manuscript"


class ReadabilityWidgetPlugin(QPyDesignerCustomWidgetPlugin, ManuscriptPluginBase):

    @overrides
    def createWidget(self, parent):
        return ReadabilityWidget(parent=parent)

    @overrides
    def name(self):
        return "ReadabilityWidget"

    @overrides
    def toolTip(self):
        return "ReadabilityWidget"

    @overrides
    def domXml(self):
        return '<widget class="ReadabilityWidget" name="wdgReadability">\n</widget>'
