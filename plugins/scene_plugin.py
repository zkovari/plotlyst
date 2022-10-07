from abc import abstractmethod

from PyQt6.QtDesigner import QPyDesignerCustomWidgetPlugin
from overrides import overrides

from plugins import PluginBase
from src.main.python.plotlyst.view.widget.scenes import ScenesTreeView, SceneStageButton


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


class SceneStageButtonPlugin(QPyDesignerCustomWidgetPlugin, ScenePluginBase):

    @overrides
    def classType(self):
        return SceneStageButton
