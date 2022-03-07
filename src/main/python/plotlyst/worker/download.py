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

import requests
from PyQt5.QtCore import QRunnable
from overrides import overrides

from src.main.python.plotlyst.env import app_env


def download_file(url, target):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(target, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


class NltkResourceDownloadWorker(QRunnable):

    @overrides
    def run(self) -> None:
        tokenizers_path = os.path.join(app_env.nltk_data, 'tokenizers')
        if os.path.exists(os.path.join(tokenizers_path, 'punkt')):
            print('Resource punkt is already present. Skip downloading.')
            return

        os.makedirs(tokenizers_path, exist_ok=True)

        punkt_zip_path = os.path.join(tokenizers_path, 'punkt.zip')
        download_file('https://github.com/nltk/nltk_data/raw/gh-pages/packages/tokenizers/punkt.zip', punkt_zip_path)
        with zipfile.ZipFile(punkt_zip_path) as zip_ref:
            zip_ref.extractall(tokenizers_path)
