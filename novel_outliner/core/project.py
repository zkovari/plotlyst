import json

from novel_outliner.core.domain import Novel


class ProjectFinder:

    def __init__(self):
        self.path = '/home/zkovari/novels/craft_of_gem'
        self._novel = None
        with open(f'{self.path}/novel.json') as json_file:
            data = json.load(json_file)
            self._novel = Novel.from_json(data)
        for scene in self.novel.scenes:
            if scene.pov:
                match = [x for x in self.novel.characters if x.name == scene.pov.name]
                if match:
                    scene.pov = match[0]
            for i, char in enumerate(scene.characters):
                match = [x for x in self.novel.characters if x.name == char.name]
                if match:
                    scene.characters[i] = match[0]

    @property
    def novel(self) -> Novel:
        return self._novel
