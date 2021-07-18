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

import pytest

from src.main.python.plotlyst.core.client import context
from src.main.python.plotlyst.view.main_window import MainWindow


@pytest.fixture
def test_client(tmp_path):
    context.init(tmp_path)


@pytest.fixture
def window(qtbot, test_client):
    main_window = MainWindow()
    main_window.show()
    qtbot.addWidget(main_window)
    qtbot.waitExposed(main_window, timeout=5000)

    return main_window
