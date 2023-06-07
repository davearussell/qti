import copy

from PySide6.QtWidgets import QDialog, QWidget, QVBoxLayout, QGridLayout
from PySide6.QtWidgets import QLabel, QCheckBox, QPushButton
from PySide6.QtWidgets import QStyle, QCommonStyle
from PySide6.QtCore import Qt, Signal, QTimer

from dialog import DataDialog
from line_edit import LineEdit

class Unspecified: pass

class MetadataKey:
    def __init__(self, name, builtin=False, required=False,
                 default=Unspecified, _type=None, in_hierarchy=False, multi=False):
        self.name = name
        self.builtin = builtin
        self.groupable = not builtin
        self.required = required
        self.type = _type
        if self.type is None:
            self.type = list if multi else str
        self.default = self.type() if default is Unspecified else default
        self.in_hierarchy = in_hierarchy
        self.multi = multi

    def copy(self):
        return type(self)(name=self.name, builtin=self.builtin, required=self.required,
                          default=copy.deepcopy(self.default), _type=self.type,
                          in_hierarchy=self.in_hierarchy, multi=self.multi)

    def json(self):
        return {k: getattr(self, k) for k in ['name', 'in_hierarchy', 'multi']}


BUILTIN_KEYS = [
    {'name': 'name', 'required': True},
    {'name': 'path', 'required': True},
    {'name': 'resolution', 'required': True, '_type': list},
    {'name': 'zoom', 'required': False, 'default': None, '_type': int},
    {'name': 'pan', 'required': False, 'default': None, '_type': list},
]

class Metadata:
    def __init__(self):
        self.keys = []
        self.lut = {}
        for key in BUILTIN_KEYS:
            self.add_key(builtin=True, **key)

    def copy(self):
        new = type(self)()
        new.keys = [key.copy() for key in self.keys]
        new.lut = {key.name: key for key in new.keys}
        return new

    def add_key(self, name, **kwargs):
        assert name not in self.lut
        key = MetadataKey(name, **kwargs)
        self.keys.append(key)
        self.lut[name] = key

    def delete_key(self, name):
        assert name in self.lut
        self.keys.remove(self.lut.pop(name))

    def rename_key(self, old_name, new_name):
        assert old_name in self.lut and new_name not in self.lut
        key = self.lut[new_name] = self.lut.pop(old_name)
        key.name = new_name

    def hierarchy(self):
        return [key.name for key in self.keys if key.in_hierarchy]

    def groupable_keys(self):
        return [key.name for key in self.keys if key.groupable]

    def multi_value_keys(self):
        return [key.name for key in self.keys if key.multi]

    def json(self):
        return [key.json() for key in self.keys if not key.builtin]

    def normalise_image_spec(self, spec):
        for key in [key for key in spec if key not in {key.name for key in self.keys}]:
            del spec[key]
        for key in self.keys:
            if key.name not in spec:
                if key.required:
                    raise Exception("Missing required key '%s'" % (key.name,))
                elif key.default is not None:
                    spec[key.name] = key.default
            elif not isinstance(spec[key.name], key.type):
                raise Exception("Bad value for key %r in %r" % (key.name, spec))


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

    def __init__(self, metadata):
        super().__init__()
        self.metadata = metadata.copy()
        self.do_layout()
        self.actions = []

    def do_layout(self):
        QWidget().setLayout(self.layout()) # clears any existing layout
        self.setLayout(QGridLayout())
        for i, row in enumerate(self.make_grid()):
            for j, cell in enumerate(row):
                if cell:
                    self.layout().addWidget(cell, i, j)
        self.layout().setRowStretch(i + 1, 1)

    def action(self, action, *args):
        self.actions.append((action, args))
        self.data_updated.emit()

    def button_cb(self, action, i):
        if action == 'delete':
            mk = self.metadata.keys.pop(i)
            self.action('delete', mk.name)
        else:
            j = i + (1 if action == 'down' else -1)
            m = self.metadata.keys
            m[i], m[j] = m[j], m[i]
            self.action('reorder', [key.name for key in m])
        self.do_layout()

    def new_row(self, name):
        is_valid = name and name not in self.metadata.lut
        if is_valid:
            self.metadata.add_key(name)
            self.action('append', name)
        self.setFocus()
        # This function is called from the context of a QLineEdit event callback.
        # self.do_layout will destroy the QLineEdit so we delay calling it until
        # the callback has returned
        QTimer.singleShot(0, self.do_layout)

    def update_name(self, name, i):
        is_valid = name and name not in self.metadata.lut
        if is_valid:
            old_name = self.metadata.keys[i].name
            if self.actions: # Merge consecutive renames of the same key
                action, args = self.actions[-1]
                if action == 'rename' and args[1] == old_name:
                    old_name = args[0]
                    self.actions.pop()
            self.action('rename', old_name, name)
            self.metadata.keys[i].name = name

    def update_multi(self, value, i):
        assert isinstance(value, bool), (value, i)
        self.metadata.keys[i].multi = value
        self.action('multi', self.metadata.keys[i].name, value)

    def update_hierarchy(self, value, i):
        assert isinstance(value, bool), (value, i)
        self.metadata.keys[i].in_hierarchy = value
        self.action('hierarchy', self.metadata.keys[i].name, value)

    def make_grid(self):
        grid = []
        is_first = True
        for i, key in enumerate(self.metadata.keys):
            is_last = i == len(self.metadata.keys) - 1

            edit = LineEdit(key.name, read_only=key.builtin, ctx=i)
            edit.updated.connect(self.update_name)
            row = [edit, None, None, None, None, None]
            if not key.builtin:
                row[1] = CheckBox('Multi-value', key.multi,
                                  ctx=i, cb=self.update_multi)
                row[2] = CheckBox('In hierarchy', key.in_hierarchy,
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
        self.metadata = self.app.library.metadata
        self.tree = self.app.browser.node.root
        self.grid = MetadataGrid(self.metadata)
        self.grid.data_updated.connect(self.data_updated)
        self.layout().addWidget(self.grid)
        self.add_buttons()

    def dirty(self):
        return bool(self.grid.actions)

    def commit(self):
        handlers = {
            'rename': self.rename_key,
            'delete': self.delete_key,
            'append': self.new_key,
            'reorder': self.reorder_keys,
            'multi': self.set_key_multi,
            'hierarchy': self.set_key_in_hierarchy,
        }
        hierarchy = self.metadata.hierarchy()
        for action, args in self.grid.actions:
            handlers[action](*args)
        if self.metadata.hierarchy() != hierarchy:
            self.app.status_bar.set_text("WARNING: default grouping updated, app restart"
                                         " required to take effect",
                                         duration_s=10, priority=100)
        self.grid.actions = []

    def rename_key(self, old_name, new_name):
        self.metadata.rename_key(old_name, new_name)
        self.app.filter_config.rename_key(old_name, new_name)
        self.tree.rename_key(old_name, new_name)

    def delete_key(self, name):
        self.metadata.delete_key(name)
        # No need to delete the key from every image at this point. It
        # will be ignored for now, and deleted for good when we normalise
        # it on the next app restart.

    def new_key(self, name):
        self.metadata.add_key(name)
        self.tree.add_key(name, '')

    def reorder_keys(self, order):
        assert set(order) == {key.name for key in self.metadata.keys}
        self.metadata.keys = [self.metadata.lut[name] for name in order]

    def set_key_multi(self, name, multi):
        self.metadata.lut[name].multi = multi
        self.tree.set_key_multi(name, multi)

    def set_key_in_hierarchy(self, name, value):
        self.metadata.lut[name].in_hierarchy = value
