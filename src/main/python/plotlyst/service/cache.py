"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

This file is part of Plotlyst.

Plotlyst is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Plotlyst is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from typing import Optional, Dict, Set

from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel, Scene, StoryBeat
from src.main.python.plotlyst.event.core import EventListener, Event
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import SceneChangedEvent, SceneDeletedEvent


class NovelActsRegistry(EventListener):

    def __init__(self):
        event_dispatcher.register(self, SceneChangedEvent)
        event_dispatcher.register(self, SceneDeletedEvent)
        self.novel: Optional[Novel] = None
        self._acts_per_scenes: Dict[str, int] = {}
        self._beats: Set[StoryBeat] = set()
        self._scenes_per_beats: Dict[StoryBeat, Scene] = {}
        self._acts_endings: Dict[int, int] = {}

    def set_novel(self, novel: Novel):
        self.novel = novel
        self.refresh()

    @overrides
    def event_received(self, event: Event):
        if self.novel:
            self.refresh()

    def refresh(self):
        self._acts_per_scenes.clear()
        self._scenes_per_beats.clear()
        self._beats.clear()
        self._acts_endings.clear()

        for index, scene in enumerate(self.novel.scenes):
            beat = scene.beat(self.novel)
            if beat and beat.act == 1 and beat.ends_act:
                self._acts_endings[1] = index
                self._acts_per_scenes[str(scene.id)] = 1
            elif beat and beat.act == 2 and beat.ends_act:
                self._acts_endings[2] = index
                self._acts_per_scenes[str(scene.id)] = 2
            else:
                self._acts_per_scenes[str(scene.id)] = len(self._acts_endings) + 1
            if beat:
                self._beats.add(beat)
                self._scenes_per_beats[beat] = scene

    def act(self, scene: Scene) -> int:
        return self._acts_per_scenes.get(str(scene.id), 1)

    def occupied_beats(self) -> Set[StoryBeat]:
        return self._beats

    def scene(self, beat: StoryBeat) -> Optional[Scene]:
        return self._scenes_per_beats.get(beat)


acts_registry = NovelActsRegistry()
