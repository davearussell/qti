from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractScrollArea
from PySide6.QtWidgets import QWidget, QLabel, QComboBox, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QAbstractTableModel

from .common import DataDialogWidget
from ..line_edit import LineEdit


class Model(QAbstractTableModel):
    def __init__(self, table, keys, font):
        super().__init__()
        self.table = table
        self.keys = keys
        self.dirty = False
        self.header_font = font
        self.header_font.setBold(True)

    def headerData(self, idx, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.keys[idx].title()
            elif role == Qt.FontRole:
                return self.header_font
        return super().headerData(idx, orientation, role)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.table[index.row()][self.keys[index.column()]]

    def rowCount(self, index):
        return len(self.table)

    def columnCount(self, index):
        return len(self.table[0])


class Editor(QWidget):
    commit = Signal(str, str)
    def __init__(self, keys):
        super().__init__()
        self.keys = keys
        self.setLayout(QHBoxLayout())

        self.label = QLabel("Update key:")
        self.combo = QComboBox()
        for key in keys:
            self.combo.addItem(key)
        self.box = LineEdit(commit_cb=self._commit)

        self.layout().addWidget(self.label)
        self.layout().addWidget(self.combo)
        self.layout().addWidget(self.box)

    def _commit(self):
        self.commit.emit(self.combo.currentText(), self.box.text())


class Table(QTableView):
    def __init__(self, model, editor):
        self.editor = editor
        super().__init__()
        self.setModel(model)
        for i in range(model.columnCount(0)):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            self.editor.combo.setFocus()
        else:
            super().keyPressEvent(event)


class BulkEditDialogWidget(DataDialogWidget):
    def __init__(self, keys, table, update_cb, **kwargs):
        super().__init__(**kwargs)
        self.keys = keys
        self.table = table
        self.update_cb = update_cb

        self.editor = Editor(self.keys)
        self.editor.commit.connect(self.handle_update)

        self.model = Model(self.table, self.keys, self.font())
        self.table = Table(self.model, self.editor)

        self.layout().addWidget(self.editor)
        self.layout().addWidget(self.table)
        self.add_action_buttons()

    def refresh(self):
        self.table.resizeColumnsToContents()

    def handle_update(self, key, value):
        self.table.setFocus()
        self.update_cb(key, value)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
