import copy

from PySide6.QtWidgets import QDialog, QWidget, QVBoxLayout, QGridLayout
from PySide6.QtWidgets import QLabel, QCheckBox, QPushButton
from PySide6.QtWidgets import QStyle, QCommonStyle
from PySide6.QtCore import Qt, Signal, QTimer

from dialog import DataDialog
from line_edit import LineEdit


class CheckBox(QCheckBox):
    updated = Signal(bool, object)

    def __init__(self, label, selected, ctx=None, cb=None):
        super().__init__(label)
        self.setChecked(selected)
        self.setFocusPolicy(Qt.NoFocus)
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
        self.setFocusPolicy(Qt.NoFocus)
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
    data_updated = Signal()

    def __init__(self, metadata_keys):
        super().__init__()
        self.metadata_keys = copy.deepcopy(metadata_keys)
        self.do_layout()
        self.actions = []

    def do_layout(self):
        QWidget().setLayout(self.layout()) # clears any existing layout
        self.setLayout(QGridLayout())
        for i, row in enumerate(self.make_grid(self.metadata_keys)):
            for j, cell in enumerate(row):
                if cell:
                    self.layout().addWidget(cell, i, j)
        self.layout().setRowStretch(i + 1, 1)

    def action(self, action, *args):
        self.actions.append((action, args))
        self.data_updated.emit()

    def button_cb(self, action, i):
        if action == 'delete':
            mk = self.metadata_keys.pop(i)
            self.action('delete', mk['name'])
        else:
            j = i + (1 if action == 'down' else -1)
            m = self.metadata_keys
            m[i], m[j] = m[j], m[i]
            self.action('reorder', [key['name'] for key in m])
        self.do_layout()

    def new_row(self, name):
        is_valid = name and name not in [key['name'] for key in self.metadata_keys]
        if is_valid:
            self.metadata_keys.append({'name': name})
            self.action('append', name)
        self.setFocus()
        # This function is called from the context of a QLineEdit event callback.
        # self.do_layout will destroy the QLineEdit so we delay calling it until
        # the callback has returned
        QTimer.singleShot(0, self.do_layout)

    def update_name(self, name, i):
        is_valid = name and name not in [key['name'] for key in self.metadata_keys]
        if is_valid:
            old_name = self.metadata_keys[i]['name']
            if self.actions: # Merge consecutive renames of the same key
                action, args = self.actions[-1]
                if action == 'rename' and args[1] == old_name:
                    old_name = args[0]
                    self.actions.pop()
            self.action('rename', old_name, name)
            self.metadata_keys[i]['name'] = name

    def update_multi(self, value, i):
        assert isinstance(value, bool), (value, i)
        self.metadata_keys[i]['multi'] = value
        self.action('multi', self.metadata_keys[i]['name'], value)

    def update_hierarchy(self, value, i):
        assert isinstance(value, bool), (value, i)
        self.metadata_keys[i]['in_hierarchy'] = value
        self.action('hierarchy', self.metadata_keys[i]['name'], value)

    def make_grid(self, metadata_keys):
        grid = []
        is_first = True
        for i, key in enumerate(metadata_keys):
            is_last = i == len(metadata_keys) - 1

            edit = LineEdit(key['name'], read_only=key.get('builtin'), ctx=i)
            edit.updated.connect(self.update_name)
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


class MetadataEditorDialog(DataDialog):
    title = 'Metadata Editor'

    def __init__(self, app):
        super().__init__(app)
        self.grid = MetadataGrid(self.app.library.metadata_keys())
        self.grid.data_updated.connect(self.data_updated)
        self.layout().addWidget(self.grid)
        self.add_buttons()

    def dirty(self):
        return bool(self.grid.actions)

    def commit(self):
        handlers = {
            'rename': self.rename_key,
            'delete': self.app.library.delete_key,
            'append': self.app.library.new_key,
            'reorder': self.app.library.reorder_keys,
            'multi': self.app.library.set_key_multi,
            'hierarchy': self.app.library.set_key_in_hierarchy,
        }
        for action, args in self.grid.actions:
            handlers[action](*args)
        self.grid.actions = []

    def rename_key(self, old_name, new_name):
        self.app.library.rename_key(old_name, new_name)
        self.app.filter_config.rename_key(old_name, new_name)
        for node in self.app.browser.node.root.descendants():
            if node.type == old_name:
                node.type = new_name
