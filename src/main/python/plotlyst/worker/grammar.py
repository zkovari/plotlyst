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
from typing import Optional

import language_tool_python
from PyQt5.QtCore import QRunnable
from PyQt5.QtGui import QSyntaxHighlighter
from language_tool_python import LanguageTool
from overrides import overrides

from src.main.python.plotlyst.event.core import emit_event, emit_critical, emit_info
from src.main.python.plotlyst.events import LanguageToolSet


class LanguageToolServerSetupWorker(QRunnable):

    @overrides
    def run(self) -> None:
        try:
            tool = language_tool_python.LanguageTool('en-US')
            tool.check('Test sentence.')
            language_tool_proxy.set(tool)
        except Exception as e:
            language_tool_proxy.set_error(str(e))


class LanguageToolProxy:
    def __init__(self):
        self._language_tool: Optional[LanguageTool] = None
        self._error: Optional[str] = None

    def set(self, language_tool: LanguageTool):
        self._language_tool = language_tool
        self._error = None
        emit_info('Grammar checker was set up.')
        emit_event(LanguageToolSet(self, self._language_tool))

    def set_error(self, error_msg: str):
        self._error = error_msg
        emit_critical('Could not initialize LanguageTool grammar checker', self._error)

    def is_set(self) -> bool:
        return self._language_tool is not None

    def is_failed(self) -> bool:
        return self._error is not None

    @property
    def error(self) -> Optional[str]:
        return self._error

    @property
    def tool(self) -> LanguageTool:
        if self.is_set():
            return self._language_tool
        else:
            raise IOError('LanguageTool local server was not initialized yet')


language_tool_proxy = LanguageToolProxy()


class GrammarChecker(QRunnable):

    def __init__(self, highlighter: QSyntaxHighlighter):
        super(GrammarChecker, self).__init__()
        self.highlighter = highlighter

    @overrides
    def run(self) -> None:
        print('check in worker')
        self.highlighter.rehighlight()
