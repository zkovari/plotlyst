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
import tarfile
import zipfile
from typing import List

import requests
from PyQt6.QtCore import QRunnable
from overrides import overrides

from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import emit_event
from src.main.python.plotlyst.resources import ResourceType, resource_manager, ResourceDownloadedEvent


def download_file(url, target):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(target, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


class NltkResourceDownloadWorker(QRunnable):

    def __init__(self):
        super(NltkResourceDownloadWorker, self).__init__()
        self.resource_types: List[ResourceType] = resource_manager.nltk_resource_types()

    @overrides
    def run(self) -> None:
        for resource_type in self.resource_types:
            if resource_manager.has_resource(resource_type):
                continue
            resource = resource_manager.resource(resource_type)
            resource_path = os.path.join(app_env.nltk_data, resource.folder)

            os.makedirs(resource_path, exist_ok=True)

            resource_zip_path = os.path.join(resource_path, resource.filename())
            download_file(resource.web_url, resource_zip_path)
            with zipfile.ZipFile(resource_zip_path) as zip_ref:
                zip_ref.extractall(resource_path)

            emit_event(ResourceDownloadedEvent(self, resource_type))
            print(f'Resource {resource.name} was successfully downloaded')


class JreResourceDownloadWorker(QRunnable):

    def __init__(self):
        super(JreResourceDownloadWorker, self).__init__()
        self._type = ResourceType.JRE_8

    @overrides
    def run(self) -> None:
        if resource_manager.has_resource(self._type):
            return
        resource = resource_manager.resource(self._type)
        resource_path = os.path.join(app_env.nltk_data, resource.folder)
        os.makedirs(resource_path, exist_ok=True)

        resource_tar_path = os.path.join(resource_path, resource.filename())
        download_file(resource.web_url, resource_tar_path)

        with tarfile.open(resource_tar_path) as tar_ref:
            tar_ref.extractall(resource_path)

        emit_event(ResourceDownloadedEvent(self, self._type))
