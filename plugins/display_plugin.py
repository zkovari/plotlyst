from abc import abstractmethod

from PyQt6.QtDesigner import QPyDesignerCustomWidgetPlugin
from overrides import overrides

from plugins import PluginBase
from src.main.python.plotlyst.view.widget.display import Subtitle, ChartView, MajorRoleIcon, SecondaryRoleIcon, \
    MinorRoleIcon, RoleIcon, Icon, IconText, WordsDisplay


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


class MajorRoleIconPlugin(QPyDesignerCustomWidgetPlugin, DisplayPluginBase):

    @overrides
    def classType(self):
        return MajorRoleIcon


class SecondaryRoleIconPlugin(QPyDesignerCustomWidgetPlugin, DisplayPluginBase):

    @overrides
    def classType(self):
        return SecondaryRoleIcon


class MinorRoleIconPlugin(QPyDesignerCustomWidgetPlugin, DisplayPluginBase):

    @overrides
    def classType(self):
        return MinorRoleIcon


class RoleIconPlugin(QPyDesignerCustomWidgetPlugin, DisplayPluginBase):

    @overrides
    def classType(self):
        return RoleIcon


class IconPlugin(QPyDesignerCustomWidgetPlugin, DisplayPluginBase):

    @overrides
    def classType(self):
        return Icon


class IconTextPlugin(QPyDesignerCustomWidgetPlugin, DisplayPluginBase):

    @overrides
    def classType(self):
        return IconText


class WordsDisplayPlugin(QPyDesignerCustomWidgetPlugin, DisplayPluginBase):

    @overrides
    def classType(self):
        return WordsDisplay
