from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin
from overrides import overrides

from plugins import PluginBase
from src.main.python.plotlyst.view.widget.input import Toggle, RotatedButton


class InputPluginBase(PluginBase):

    def group(self):
        return "Plotlyst input"

    def includeFile(self):
        return "src.main.python.plotlyst.view.widget.input"


class TogglePlugin(QPyDesignerCustomWidgetPlugin, InputPluginBase):

    @overrides
    def createWidget(self, parent):
        return Toggle(parent=parent)

    @overrides
    def name(self):
        return "Toggle"

    @overrides
    def toolTip(self):
        return "Toggle checkbox widget"

    @overrides
    def domXml(self):
        return '<widget class="Toggle" name="toggle">\n</widget>'


class RotatedButtonPlugin(QPyDesignerCustomWidgetPlugin, InputPluginBase):
    @overrides
    def createWidget(self, parent):
        return RotatedButton(parent=parent)

    @overrides
    def name(self):
        return "RotatedButton"

    @overrides
    def toolTip(self):
        return "RotatedButton widget"

    @overrides
    def domXml(self):
        return '<widget class="RotatedButton" name="btn">\n</widget>'
