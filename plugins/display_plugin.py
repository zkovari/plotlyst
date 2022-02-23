from abc import abstractmethod

from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin
from overrides import overrides

from plugins import PluginBase
from src.main.python.plotlyst.view.widget.display import Subtitle, ChartView


class DisplayPluginBase(PluginBase):

    def group(self):
        return "Plotlyst display"

    def includeFile(self):
        return "src.main.python.plotlyst.view.widget.display"

    @abstractmethod
    def classType(self):
        pass


class SubtitlePlugin(QPyDesignerCustomWidgetPlugin, DisplayPluginBase):

    @overrides
    def classType(self):
        return Subtitle


class ChartViewPlugin(QPyDesignerCustomWidgetPlugin, DisplayPluginBase):

    @overrides
    def classType(self):
        return ChartView
