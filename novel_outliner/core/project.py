import json

from novel_outliner.core.domain import Novel


class ProjectFinder:

    def __init__(self):
        self.path = '/home/zkovari/novels/craft_of_gem'
        self._novel = None
        with open(f'{self.path}/novel.json') as json_file:
            data = json.load(json_file)
            self._novel = Novel.from_json(data)

    @property
    def novel(self) -> Novel:
        return self._novel
