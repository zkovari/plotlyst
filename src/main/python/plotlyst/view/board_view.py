from overrides import overrides
from qthandy import vbox

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.view._view import AbstractNovelView


class BoardView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel)
        vbox(self.widget)

    @overrides
    def refresh(self):
        pass
