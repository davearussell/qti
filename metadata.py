import copy

from PySide6.QtWidgets import QDialog, QWidget, QVBoxLayout, QGridLayout
from PySide6.QtWidgets import QLabel, QCheckBox, QPushButton
from PySide6.QtWidgets import QStyle, QCommonStyle
from PySide6.QtCore import Qt, Signal

from line_edit import LineEdit
import keys


class CheckBox(QCheckBox):
    updated = Signal(bool, object)

    def __init__(self, label, selected, ctx=None, cb=None):
        super().__init__(label)
        self.setChecked(selected)
        self.ctx = ctx
        self.stateChanged.connect(self._updated)
        if cb:
            self.updated.connect(cb)

    def _updated(self, value):
        self.updated.emit(value, self.ctx)


class ActionButton(QPushButton):
    act = Signal(str, object)

    def __init__(self, action, ctx=None, cb=None):
        super().__init__()
        self.action = action
        self.ctx = ctx
        style = QCommonStyle()
        icon = {
            'up': QStyle.SP_ArrowUp,
            'down': QStyle.SP_ArrowDown,
            'delete': QStyle.SP_TrashIcon,
        }[action]
        self.setIcon(style.standardIcon(icon))
        self.clicked.connect(self._clicked)
        if cb:
            self.act.connect(cb)

    def _clicked(self):
        self.act.emit(self.action, self.ctx)


class MetadataGrid(QWidget):
    rename_key = Signal(str, str)
    delete_key = Signal(str)
    new_key = Signal(str)
    reorder_keys = Signal(list)
    set_key_multi = Signal(str, bool)
    set_hierarchy = Signal(list)

    def __init__(self, metadata_keys):
        super().__init__()
        self.metadata_keys = copy.deepcopy(metadata_keys)
        self.do_layout()

    def do_layout(self):
        QWidget().setLayout(self.layout()) # clears any existing layout
        self.setLayout(QGridLayout())
        for i, row in enumerate(self.make_grid(self.metadata_keys)):
            for j, cell in enumerate(row):
                if cell:
                    self.layout().addWidget(cell, i, j)
        self.layout().setRowStretch(i + 1, 1)

    def button_cb(self, action, i):
        if action == 'delete':
            mk = self.metadata_keys.pop(i)
            self.delete_key.emit(mk['name'])
            if mk.get('in_hierarchy'):
                self.refresh_hierarchy()
        else:
            j = i + (1 if action == 'down' else -1)
            m = self.metadata_keys
            m[i], m[j] = m[j], m[i]
            self.reorder_keys.emit([key['name'] for key in self.metadata_keys])
        self.do_layout()

    def new_row(self, name):
        is_valid = name and name not in [key['name'] for key in self.metadata_keys]
        if is_valid:
            self.metadata_keys.append({'name': name})
            self.new_key.emit(name)
        self.setFocus()
        self.do_layout()

    def update_name(self, name, i):
        is_valid = name and name not in [key['name'] for key in self.metadata_keys]
        if is_valid:
            self.rename_key.emit(self.metadata_keys[i]['name'], name)
            self.metadata_keys[i]['name'] = name
        self.do_layout()

    def update_multi(self, value, i):
        assert isinstance(value, bool), (value, i)
        self.metadata_keys[i]['multi'] = value
        self.set_key_multi.emit(self.metadata_keys[i]['name'], value)

    def refresh_hierarchy(self):
        keys = [mk['name'] for mk in self.metadata_keys if mk.get('in_hierarchy')]
        self.set_hierarchy.emit(keys)

    def update_hierarchy(self, value, i):
        assert isinstance(value, bool), (value, i)
        self.metadata_keys[i]['in_hierarchy'] = value
        self.refresh_hierarchy()

    def make_grid(self, metadata_keys):
        grid = []
        is_first = True
        for i, key in enumerate(metadata_keys):
            is_last = i == len(metadata_keys) - 1

            edit = LineEdit(key['name'], read_only=key.get('builtin'),
                            ctx=i, commit_cb=self.update_name)
            row = [edit, None, None, None, None, None]
            if not key.get('builtin'):
                row[1] = CheckBox('Multi-value', bool(key.get('multi')),
                                  ctx=i, cb=self.update_multi)
                row[2] = CheckBox('In hierarchy', bool(key.get('in_hierarchy')),
                                  ctx=i, cb=self.update_hierarchy)
                row[5] = ActionButton('delete', i, self.button_cb)
                if not is_first:
                    row[3] = ActionButton('up', i, self.button_cb)
                if not is_last:
                    row[4] = ActionButton('down', i, self.button_cb)
                is_first = False
            grid.append(row)

        grid.append([QLabel("<b>Add new key<b>"),
                     LineEdit(commit_cb=self.new_row)])
        return grid


class MetadataEditorDialog(QDialog):
    def __init__(self, app):
        super().__init__(app.window)
        self.setWindowTitle("Metadata Editor")
        self.app = app
        self.app.library.refresh_images()
        self.setLayout(QVBoxLayout())
        self.grid = MetadataGrid(self.app.library.metadata_keys())
        self.grid.rename_key.connect(self.app.library.rename_key)
        self.grid.delete_key.connect(self.app.library.delete_key)
        self.grid.new_key.connect(self.app.library.new_key)
        self.grid.reorder_keys.connect(self.app.library.reorder_keys)
        self.grid.set_key_multi.connect(self.app.library.set_key_multi)
        self.grid.set_hierarchy.connect(self.app.library.set_hierarchy)
        self.layout().addWidget(self.grid)
        done = QPushButton("Done")
        done.setDefault(True)
        done.clicked.connect(self.accept)
        self.layout().addWidget(done)

    def keyPressEvent(self, event):
        if keys.get_action(event) == 'select':
            self.accept()
        else:
            event.ignore()
