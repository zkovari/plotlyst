from abc import abstractmethod

from PyQt6.QtDesigner import QPyDesignerCustomWidgetPlugin
from overrides import overrides

from plugins import PluginBase
from src.main.python.plotlyst.view.widget.characters import CharacterAvatar


class CharacterPluginBase(PluginBase):

    def group(self):
        return "Plotlyst character"

    def includeFile(self):
        return "src.main.python.plotlyst.view.widget.characters"

    @abstractmethod
    def classType(self):
        pass


class CharacterAvatarPlugin(QPyDesignerCustomWidgetPlugin, CharacterPluginBase):

    @overrides
    def classType(self):
        return CharacterAvatar
