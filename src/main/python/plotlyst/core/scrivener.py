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
from pathlib import Path
from typing import List, Optional
from uuid import UUID
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from src.main.python.plotlyst.core.client import load_image
from src.main.python.plotlyst.core.domain import Novel, Scene, Chapter, Character, Location


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

        return self._parse_scrivx(Path(folder).joinpath(scrivener_file), Path(folder).joinpath('Files/Data'))

    def _parse_scrivx(self, scrivener_path: Path, data_folder: Path) -> Novel:
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
                children_item = chapter_item.find('Children')
                if not children_item:
                    continue
                for scene_item in children_item.findall('BinderItem'):
                    scene = self._parse_scene(scene_item, data_folder)
                    scene.chapter = chapter
                    scenes.append(scene)
        else:
            for scene_item in draft_binder.findall('.//BinderItem[@Type="Text"]'):
                scenes.append(self._parse_scene(scene_item, data_folder))

        characters: List[Character] = []
        locations: List[Location] = []
        for item in binder.findall('BinderItem'):
            if item.attrib.get('Type') == 'Folder':
                title_item = item.find('Title')
                if title_item is not None and title_item.text.lower().startswith('character'):
                    children_item = item.find('Children')
                    if not children_item:
                        continue
                    for character_item in children_item.findall('BinderItem'):
                        character = self._parse_character(character_item, data_folder)
                        if character:
                            characters.append(character)
                if title_item is not None and (
                        title_item.text.lower().startswith('places') or title_item.text.lower().startswith('settings')):
                    children_item = item.find('Children')
                    if not children_item:
                        continue
                    for location_item in children_item.findall('BinderItem'):
                        location = self._parse_location(location_item)
                        if location:
                            locations.append(location)

        return Novel(title='Importer project', id=UUID(novel_id), characters=characters, scenes=scenes,
                     chapters=chapters, locations=locations)

    def _parse_chapter(self, element: Element) -> Chapter:
        uuid = element.attrib.get('UUID')
        if not uuid:
            raise ScrivenerParsingError('Could not extract chapter id as UUID attribute was not found')
        title = self._find_title(element)
        return Chapter(title, id=UUID(uuid))

    def _parse_scene(self, element: Element, data_folder: Path) -> Scene:
        uuid = element.attrib.get('UUID')
        if not uuid:
            raise ScrivenerParsingError('Could not extract scene id as UUID attribute was not found')

        title = self._find_title(element)

        scene = Novel.new_scene(title)
        scene.id = UUID(uuid)
        scene.synopsis = self._find_synopsis(scene.id, data_folder)
        return scene

    def _parse_character(self, element: Element, data_folder: Path) -> Optional[Character]:
        uuid = element.attrib.get('UUID')
        if not uuid:
            return None
        name = self._find_title(element)
        character = Character(name, id=UUID(uuid))
        character.avatar = self._find_image(character.id, data_folder)
        return character

    def _parse_location(self, element: Element) -> Optional[Location]:
        uuid = element.attrib.get('UUID')
        if not uuid:
            return None
        name = self._find_title(element)
        return Location(name, id=UUID(uuid))

    def _find_title(self, element) -> str:
        title_el = element.find('Title')
        if title_el is None:
            title = ''
        else:
            title = title_el.text
        return title

    def _find_image(self, id: UUID, data_folder: Path):
        id_folder = data_folder.joinpath(str(id).upper())
        if id_folder.exists():
            image_path = id_folder.joinpath('card-image.jpeg')
            if image_path.exists():
                return load_image(image_path)

    def _find_synopsis(self, id: UUID, data_folder: Path) -> str:
        id_folder = data_folder.joinpath(str(id).upper())
        if id_folder.exists():
            synopsis_path = id_folder.joinpath('synopsis.txt')
            if synopsis_path.exists():
                with open(synopsis_path, encoding='utf8') as synopsis_file:
                    return synopsis_file.read()

        return ''
