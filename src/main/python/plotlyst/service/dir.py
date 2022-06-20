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
from typing import Optional

from PyQt5.QtWidgets import QMessageBox, QFileDialog


def select_new_project_directory() -> Optional[str]:
    workspace = QFileDialog.getExistingDirectory(None, 'Choose directory')

    if not workspace:
        return None

    if not os.path.exists(workspace):
        QMessageBox.warning(None, 'Invalid project directory',
                            f"The chosen directory doesn't exist: {workspace}")
    elif os.path.isfile(workspace):
        QMessageBox.warning(None, 'Invalid project directory',
                            f"The chosen path should be a directory, not a file: {workspace}")
    elif not os.access(workspace, os.W_OK):
        QMessageBox.warning(None, 'Invalid project directory',
                            f"The chosen directory cannot be written: {workspace}")
    else:
        return workspace
