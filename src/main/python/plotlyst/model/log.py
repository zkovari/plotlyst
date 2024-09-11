"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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
from logging import LogRecord

from PyQt6.QtCore import QAbstractTableModel, Qt
from overrides import overrides

from plotlyst.common import RED_COLOR
from plotlyst.view.icons import IconRegistry


class LogTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.log_records = []
        self.max_logs = 1000
        self.errorIcon = IconRegistry.from_name('msc.error', RED_COLOR)
        self.warningIcon = IconRegistry.from_name('msc.warning', '#e9c46a')
        self.infoIcon = IconRegistry.from_name('msc.info')

    @overrides
    def rowCount(self, parent=None):
        return len(self.log_records)

    @overrides
    def columnCount(self, parent=None):
        return 2

    @overrides
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.ToolTipRole:
            row = index.row()
            col = index.column()
            log_record = self.log_records[row]

            if col == 1:
                return log_record.msg
            elif col == 2:
                return log_record.asctime
        if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
            log_record = self.log_records[index.row()]
            if log_record.levelname == 'INFO':
                return self.infoIcon
            elif log_record.levelname == 'WARNING':
                return self.warningIcon
            elif log_record.levelname == 'ERROR':
                return self.errorIcon

    def addLogRecord(self, log_record: LogRecord):
        if len(self.log_records) >= self.max_logs:
            self.beginRemoveRows(self.index(0, 0), 0, 0)
            self.log_records.pop(0)  # Remove the oldest log (at the front of the list)
            self.endRemoveRows()

        # Add the new log record at the end
        self.beginInsertRows(self.index(self.rowCount(), 0), self.rowCount(), self.rowCount())
        self.log_records.append(log_record)
        self.endInsertRows()

    @overrides
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section == 0:
                    return ""
                elif section == 1:
                    return "Message"
                elif section == 2:
                    return "Timestamp"
        return None
