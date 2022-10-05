from abc import abstractmethod

from PyQt6.QtDesigner import QPyDesignerCustomWidgetPlugin
from overrides import overrides

from plugins import PluginBase
from src.main.python.plotlyst.view.widget.manuscript import ReadabilityWidget


class ManuscriptPluginBase(PluginBase):

    def group(self):
        return "Plotlyst manuscript"

    def includeFile(self):
        return "src.main.python.plotlyst.view.widget.manuscript"

    @abstractmethod
    def classType(self):
        pass


class ReadabilityWidgetPlugin(QPyDesignerCustomWidgetPlugin, ManuscriptPluginBase):

    @overrides
    def classType(self):
        return ReadabilityWidget
