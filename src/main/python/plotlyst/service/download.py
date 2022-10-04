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
import os
import zipfile
from typing import List

import requests
from PyQt6.QtCore import QRunnable
from overrides import overrides

from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.resources import NltkResource, punkt_nltk_resource, avg_tagger_nltk_resource


def download_file(url, target):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(target, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


class NltkResourceDownloadWorker(QRunnable):

    def __init__(self):
        super(NltkResourceDownloadWorker, self).__init__()
        self.resources: List[NltkResource] = [punkt_nltk_resource, avg_tagger_nltk_resource]

    @overrides
    def run(self) -> None:
        for resource in self.resources:
            resource_path = os.path.join(app_env.nltk_data, resource.folder)
            if os.path.exists(os.path.join(resource_path, resource.name)):
                print(f'Resource {resource.name} is already present. Skip downloading.')
                continue

            os.makedirs(resource_path, exist_ok=True)

            resource_zip_path = os.path.join(resource_path, f'{resource.name}.zip')
            download_file(resource.web_url, resource_zip_path)
            with zipfile.ZipFile(resource_zip_path) as zip_ref:
                zip_ref.extractall(resource_path)

            print(f'Resource {resource.name} was successfully downloaded')
