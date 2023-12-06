import copy
import functools

from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QDialogButtonBox
from PySide6.QtWidgets import QGridLayout
from PySide6.QtCore import Qt

from dialog import DataDialog, FieldDialog
from fields import TextField, SetField, EnumField
from keys import KeyMap

OPS = ['add', 'remove', 'toggle']


class ActionEditor(FieldDialog):
    def __init__(self, app, actions, qa, mode):
        self.mode = mode
        super().__init__(app)
        self.setWindowTitle("%s quick action" % (self.mode.title()))
        self.qa = qa
        self.other_names = [name for name, other_qa in actions.items() if other_qa != qa]
        self.actions = actions
        km = KeyMap()
        self.name_field = TextField("name", self.qa['name'], keymap=km)
        self.init_fields([
            self.name_field,
            TextField("key", self.qa['key'], keymap=km),
            EnumField("operation", self.qa['operation'], OPS, keymap=km),
            TextField("value", self.qa['value'], keymap=km),
        ])
        self.data_updated()

    def add_buttons(self):
        super().add_buttons(apply=(self.mode == 'edit'))

    def name_valid(self):
        name = self.name_field.get_value()
        return bool(name.strip() and name not in self.other_names)

    def data_updated(self):
        super().data_updated()
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(self.name_valid())

    def apply_field_update(self, field, value):
        self.qa[field.key] = value


class ActionGrid(QWidget):
    def __init__(self, dialog, actions):
        super().__init__()
        self.dialog = dialog
        self.app = dialog.app
        self.actions = actions
        self.do_layout()

    def do_layout(self):
        QWidget().setLayout(self.layout()) # clears any existing layout
        grid = QGridLayout()
        self.setLayout(grid)
        for i, name in enumerate(sorted(self.actions)):
            qa = self.actions[name]
            grid.addWidget(QLabel(name), i, 0)
            for j, verb in enumerate(['edit', 'delete']):
                button = QPushButton(verb.title())
                button.setFocusPolicy(Qt.NoFocus)
                button.clicked.connect(functools.partial(self.button_cb, verb=verb, name=name))
                grid.addWidget(button, i, j + 1)

        new = QPushButton("Add new action")
        new.setFocusPolicy(Qt.NoFocus)
        new.clicked.connect(functools.partial(self.button_cb, verb='new'))
        i = len(self.actions)
        grid.addWidget(new, i, 0, 1, 3)
        self.layout().setRowStretch(i + 1, 1)

    def button_cb(self, verb, name=None):
        if verb == 'edit':
            ActionEditor(self.app, self.actions, self.actions[name], mode='edit').exec()
        elif verb == 'delete':
            del self.actions[name]
        elif verb == 'new':
            qa = {'name': '', 'key': '', 'operation': OPS[0], 'value': '', }
            if ActionEditor(self.app, self.actions, qa, mode='new').exec():
                self.actions[qa['name']] = qa
        else:
            assert 0, verb
        self.dialog.data_updated()
        self.do_layout()


class QuickActionDialog(DataDialog):
    title = 'Quick Actions'

    def __init__(self, app):
        super().__init__(app)
        self.keybinds = self.app.keybinds
        self.library = self.app.library
        self.actions = copy.deepcopy(self.library.quick_actions)
        self.grid = ActionGrid(self, self.actions)
        self.layout().addWidget(self.grid)
        self.add_buttons()

    def dirty(self):
        return self.actions != self.library.quick_actions

    def commit(self):
        for qa in self.library.quick_actions:
            self.keybinds.delete_action('quick_action_' + qa)
        self.library.quick_actions = self.actions
        for qa in self.library.quick_actions:
            self.keybinds.add_action('quick_action_' + qa)
