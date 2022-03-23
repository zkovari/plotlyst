from abc import abstractmethod

from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin
from overrides import overrides

from plugins import PluginBase
from src.main.python.plotlyst.view.widget.button import SelectionItemPushButton, SecondaryActionPushButton, \
    SecondaryActionToolButton


class ButtonPluginBase(PluginBase):

    def group(self):
        return "Plotlyst buttons"

    def includeFile(self):
        return "src.main.python.plotlyst.view.widget.button"

    @abstractmethod
    def classType(self):
        pass


class SelectionItemPushButtonPlugin(QPyDesignerCustomWidgetPlugin, ButtonPluginBase):

    @overrides
    def classType(self):
        return SelectionItemPushButton


class SecondaryActionPushButtonPlugin(QPyDesignerCustomWidgetPlugin, ButtonPluginBase):

    @overrides
    def classType(self):
        return SecondaryActionPushButton


class SecondaryActionToolButtonPlugin(QPyDesignerCustomWidgetPlugin, ButtonPluginBase):

    @overrides
    def classType(self):
        return SecondaryActionToolButton
