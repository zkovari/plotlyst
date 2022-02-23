from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin
from overrides import overrides

from plugins import PluginBase
from src.main.python.plotlyst.view.widget.characters import CharacterAvatar


class CharacterPluginBase(PluginBase):

    def group(self):
        return "Plotlyst character"

    def includeFile(self):
        return "src.main.python.plotlyst.view.widget.characters"


class CharacterAvatarPlugin(QPyDesignerCustomWidgetPlugin, CharacterPluginBase):
    @overrides
    def createWidget(self, parent):
        return CharacterAvatar(parent=parent)

    @overrides
    def name(self):
        return "CharacterAvatar"

    @overrides
    def toolTip(self):
        return "CharacterAvatar widget"

    @overrides
    def domXml(self):
        return '<widget class="CharacterAvatar" name="avatar">\n</widget>'
