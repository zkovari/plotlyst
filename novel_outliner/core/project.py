from novel_outliner.core.client import client
from novel_outliner.core.domain import Novel


class ProjectFinder:

    def __init__(self):
        self._novel = client.fetch_novel()

    @property
    def novel(self) -> Novel:
        return self._novel
