"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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
from pathlib import Path
from typing import List
from uuid import UUID
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel, Scene, Chapter


class ScrivenerParsingError(Exception):
    pass


class ScrivenerImporter:

    def import_project(self, folder: str) -> Novel:
        if not os.path.exists(folder):
            raise ValueError(f'Input folder does not exist: {folder}')
        if not os.path.isdir(folder):
            raise ValueError(f'Input path is not a directory: {folder}')

        scrivener_file = ''
        for file in os.listdir(folder):
            if file.endswith('.scrivx'):
                scrivener_file = file
                break
        if not scrivener_file:
            raise ValueError(f'Could not find main Scrivener file with .scrivx extension under given folder: {folder}')

        novel = self._parse_scrivx(Path(folder).joinpath(scrivener_file))
        if client.has_novel(novel.id):
            raise ValueError('Cannot import Scrivener project again because it is already imported in Plotlyst')

        return novel

    def _parse_scrivx(self, scrivener_path: Path) -> Novel:
        tree = ElementTree.parse(scrivener_path)
        root = tree.getroot()
        novel_id = root.attrib.get('Identifier')
        if not novel_id:
            raise ScrivenerParsingError('Could not extract novel id as Identifier attribute was not found')

        binder = root.find('Binder')
        if not binder:
            raise ScrivenerParsingError('Could not find Binder element')
        draft_binder = None
        for item in binder.findall('BinderItem'):
            if item.attrib.get('Type') == 'DraftFolder':
                draft_binder = item
                break
        if not draft_binder:
            raise ScrivenerParsingError('Could not locate scenes element')
        chapters_el = draft_binder.findall('.//BinderItem[@Type="Text"]/../..[@Type="Folder"]')

        chapters: List[Chapter] = []
        scenes: List[Scene] = []
        if chapters_el:
            for chapter_item in chapters_el:
                chapter: Chapter = self._parse_chapter(chapter_item)
                chapters.append(chapter)
                for scene_item in chapter_item.find('Children').findall('BinderItem'):
                    scene = self._parse_scene(scene_item)
                    scene.chapter = chapter
                    scenes.append(scene)
        else:
            for scene_item in draft_binder.findall('.//BinderItem[@Type="Text"]'):
                scenes.append(self._parse_scene(scene_item))

        return Novel(title='Importer project', id=UUID(novel_id), scenes=scenes, chapters=chapters)

    def _parse_chapter(self, element: Element) -> Chapter:
        uuid = element.attrib.get('UUID')
        if not uuid:
            raise ScrivenerParsingError('Could not extract chapter id as UUID attribute was not found')
        title = self._find_title(element)
        return Chapter(title, id=UUID(uuid))

    def _parse_scene(self, element: Element) -> Scene:
        uuid = element.attrib.get('UUID')
        if not uuid:
            raise ScrivenerParsingError('Could not extract scene id as UUID attribute was not found')

        title = self._find_title(element)

        return Scene(id=UUID(uuid), title=title)

    def _find_title(self, element):
        title_el = element.find('Title')
        if title_el is None:
            title = ''
        else:
            title = title_el.text
        return title
