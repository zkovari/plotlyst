"""
Plotlyst
Copyright (C) 2021-2023  Zsolt Kovari

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
import os
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, List

from atomicwrites import atomic_write
from dataclasses_json import Undefined, dataclass_json
from fbs_runtime.application_context.PyQt6 import ApplicationContext
from overrides import overrides
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import EventListener, Event
from src.main.python.plotlyst.event.handler import event_dispatcher


class ResourceRegistry:

    def __init__(self):
        self._cork = None
        self._frame1 = None
        self._cover1 = None
        self._banner = None
        self._circular_frame1 = None

    def set_up(self, app_context: ApplicationContext):
        self._cork = app_context.get_resource('cork.wav')
        self._frame1 = app_context.get_resource('frame_1.png')
        self._cover1 = app_context.get_resource('cover_1.jpg')
        self._banner = app_context.get_resource('plotlyst_banner.jpg')
        self._circular_frame1 = app_context.get_resource('circular_frame1.png')

    @property
    def cork(self):
        return self._cork

    @property
    def frame1(self):
        return self._frame1

    @property
    def cover1(self):
        return self._cover1

    @property
    def banner(self):
        return self._banner

    @property
    def circular_frame1(self):
        return self._circular_frame1


resource_registry = ResourceRegistry()


class ResourceType(str, Enum):
    NLTK_PUNKT_TOKENIZER = 'nltk_punkt_tokenizer'
    NLTK_AVERAGED_PERCEPTRON_TAGGER = 'nltk_averaged_perceptron_tagger'
    JRE_8 = 'jre_8'


@dataclass
class ResourceDescriptor:
    name: str
    folder: str
    web_url: str
    extension: str = 'zip'
    version: str = ''
    human_name: str = ''
    description: str = ''

    def filename(self) -> str:
        return f'{self.name}.{self.extension}'


_punkt_nltk_resource = ResourceDescriptor('punkt', 'tokenizers',
                                          'https://github.com/nltk/nltk_data/raw/gh-pages/packages/tokenizers/punkt.zip',
                                          human_name='Punctuation tokenizer',
                                          description='Necessary for a precise sentence number calculation')
__avg_tagger_url = 'https://github.com/nltk/nltk_data/raw/gh-pages/packages/taggers/averaged_perceptron_tagger.zip'
_avg_tagger_nltk_resource = ResourceDescriptor('averaged_perceptron_tagger', 'taggers', __avg_tagger_url,
                                               human_name='Tagger', description='Necessary for adverb highlight')

_nltk_resources: Dict[ResourceType, ResourceDescriptor] = {
    ResourceType.NLTK_PUNKT_TOKENIZER: _punkt_nltk_resource,
    ResourceType.NLTK_AVERAGED_PERCEPTRON_TAGGER: _avg_tagger_nltk_resource
}


@dataclass
class ResourceDownloadedEvent(Event):
    type: ResourceType


class ResourceStatus(Enum):
    MISSING = 'missing'
    PENDING = 'pending'
    DOWNLOADED = 'downloaded'


@dataclass
class ResourceInfo:
    resource: ResourceDescriptor
    status: ResourceStatus = ResourceStatus.MISSING
    updated: str = str(date.today())


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ResourcesConfig:
    resources: Dict[ResourceType, ResourceInfo] = field(default_factory=dict)


class ResourceManager(EventListener):
    def __init__(self):
        self._resources_config: Optional[ResourcesConfig] = None
        self._path = None

    def init(self):
        cache = app_env.cache_dir
        self._path = Path(cache).joinpath('resources.json')
        if self._path.exists():
            with open(self._path, encoding='utf8') as json_file:
                data = json_file.read()
                self._resources_config = ResourcesConfig.from_json(data)
        else:
            self._resources_config = ResourcesConfig()

        jre = self.resource(ResourceType.JRE_8)
        if app_env.is_mac():
            os.environ['LTP_JAVA_PATH'] = os.path.join(app_env.cache_dir,
                                                       f'jre/{jre.version}-jre/Contents/Home/bin/java')
        elif app_env.is_linux():
            os.environ['LTP_JAVA_PATH'] = os.path.join(app_env.cache_dir, f'jre/{jre.version}-jre/bin/java')

        event_dispatcher.register(self, ResourceDownloadedEvent)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, ResourceDownloadedEvent):
            self._update_resource_status(event.type, ResourceStatus.DOWNLOADED)

    def has_resource(self, resource_type: ResourceType) -> bool:
        if self._resources_config is None:
            raise ValueError('Resources were not initialized yet')

        resource_info = self._resources_config.resources.get(resource_type)
        if resource_info:
            return resource_info.status == ResourceStatus.DOWNLOADED

        return False

    def resource(self, resource_type: ResourceType) -> ResourceDescriptor:
        if resource_type.name.startswith('NLTK'):
            return _nltk_resources[resource_type]
        if resource_type == ResourceType.JRE_8:
            version = 'jdk8u362-b09'
            if app_env.is_linux():
                distr = 'OpenJDK8U-jre_x64_linux_hotspot_8u362b09.tar.gz'
            elif app_env.is_mac():
                distr = 'OpenJDK8U-jre_x64_mac_hotspot_8u362b09.tar.gz'
            else:
                raise IOError('Not supported platform for JRE')
            url = f'https://github.com/adoptium/temurin8-binaries/releases/download/{version}/{distr}'
            return ResourceDescriptor('jre', 'jre', url, extension='tar.gz', version=version, human_name='Java',
                                      description='Necessary for local grammar checking')

    def nltk_resource_types(self) -> List[ResourceType]:
        return [x for x in ResourceType if x.name.startswith('NLTK')]

    def save(self):
        with atomic_write(self._path, overwrite=True) as f:
            f.write(self._resources_config.to_json())

    def _update_resource_status(self, type_: ResourceType, status: ResourceStatus):
        info = self.__get_resource_info(type_)
        info.status = status
        self.save()

    def __get_resource_info(self, resource_type: ResourceType) -> ResourceInfo:
        if resource_type not in self._resources_config.resources.keys():
            self._resources_config.resources[resource_type] = ResourceInfo(self.resource(resource_type))
        return self._resources_config.resources[resource_type]


resource_manager = ResourceManager()
