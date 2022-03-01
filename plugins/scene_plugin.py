from abc import abstractmethod

from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin
from overrides import overrides

from plugins import PluginBase
from src.main.python.plotlyst.view.widget.scenes import ScenesTreeView


class ScenePluginBase(PluginBase):

    def group(self):
        return "Plotlyst scene"

    def includeFile(self):
        return "src.main.python.plotlyst.view.widget.scenes"

    @abstractmethod
    def classType(self):
        pass


class ScenesTreeViewPlugin(QPyDesignerCustomWidgetPlugin, ScenePluginBase):

    @overrides
    def classType(self):
        return ScenesTreeView
