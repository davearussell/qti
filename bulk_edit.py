from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractScrollArea
from PySide6.QtWidgets import QWidget, QLabel, QComboBox, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QAbstractTableModel

import template
from dialog import DataDialog
from line_edit import LineEdit


class Model(QAbstractTableModel):
    def __init__(self, node, keys, font):
        super().__init__()
        self.library = node.library
        self.parent_node = node
        self.keys = keys
        self.table = [
            [self.get_value(node, key) for key in self.keys]
            for node in self.parent_node.children
        ]
        self.dirty = False
        self.header_font = font
        self.header_font.setBold(True)

    def get_value(self, node, key):
        if key == 'name':
            return node.name
        elif key in self.library.hierarchy:
            return next(node.leaves()).spec[key]
        else:
            values = {leaf.spec[key] for leaf in node.leaves()}
            if len(values) == 1:
                return values.pop()
            else:
                return '...'

    def set_value(self, key, value):
        col = self.keys.index(key)
        for row, node in zip(self.table, self.parent_node.children):
            row[col] = template.evaluate(node, value)
        self.dirty = True
        self.dataChanged.emit(self.createIndex(0, col),
                              self.createIndex(len(self.table) - 1, col))

    def commit(self):
        for node, row in zip(self.parent_node.children, self.table):
            for key, value in zip(self.keys, row):
                if node.type == 'image':
                    assert key in node.spec
                    node.spec[key] = value
                else:
                    if key == 'name':
                        key = node.type
                    for leaf in node.leaves():
                        leaf.spec[key] = value

    def headerData(self, idx, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.keys[idx].title()
            elif role == Qt.FontRole:
                return self.header_font
        return super().headerData(idx, orientation, role)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.table[index.row()][index.column()]

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
        self.combo.setFocusPolicy(Qt.NoFocus)
        for key in keys:
            self.combo.addItem(key)
        self.box = LineEdit(commit_on_unfocus=False)
        self.box.commit.connect(self._commit)


        self.layout().addWidget(self.label)
        self.layout().addWidget(self.combo)
        self.layout().addWidget(self.box)

    def _commit(self, value):
        self.commit.emit(self.combo.currentText(), value)


class BulkEditDialog(DataDialog):
    title = 'Bulk edit'

    def __init__(self, app, node):
        super().__init__(app)
        self.node = node
        self.updates = {}
        self.library = self.app.library
        self.edit_type = self.node.children[0].type
        self.setWindowTitle("Bulk %s edit" % (self.edit_type,))

        self.keys = self.choose_keys()
        self.editor = Editor(self.keys)
        self.editor.commit.connect(self.update_key)

        self.model = Model(self.node, self.keys, self.font())
        self.table = QTableView()
        self.table.setModel(self.model)
        for i in range(len(self.keys)):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        self.layout().addWidget(self.editor)
        self.layout().addWidget(self.table)
        self.add_buttons()

    def choose_keys(self):
        if self.edit_type == 'image':
            parents = self.library.hierarchy
        elif self.edit_type in self.library.hierarchy:
            i = self.library.hierarchy.index(self.edit_type)
            parents = self.library.hierarchy[:i]
        else:
            parents = []
        keys = ['name']
        for key in self.library.metadata_keys():
            if key.get('builtin') or key.get('multi'):
                continue
            if key.get('in_hierarchy') and key['name'] not in parents:
                continue
            keys.append(key['name'])
        return keys

    def update_key(self, key, value):
        self.model.set_value(key, value)
        self.data_updated()

    def dirty(self):
        return self.model.dirty

    def commit(self):
        self.model.commit()
        self.node.library.refresh_images()
        self.app.reload_tree()
