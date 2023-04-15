import copy
import functools

from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QDialogButtonBox
from PySide6.QtWidgets import QGridLayout
from PySide6.QtCore import Qt

from dialog import DataDialog, FieldDialog
from fields import TextField, SetField
from keys import KeyMap


class FilterEditor(FieldDialog):
    def __init__(self, app, filters, qf, mode):
        self.mode = mode
        super().__init__(app)
        self.setWindowTitle("%s quick filter" % (self.mode.title()))
        self.qf = qf
        self.other_names = [name for name, other_qf in filters.items() if other_qf != qf]
        self.filters = filters
        km = KeyMap()
        self.init_fields([
            TextField("name", self.qf['name'], keymap=km),
            SetField("group", self.qf['group'], keymap=km),
            SetField("order", self.qf['order'], keymap=km),
            TextField("expr", self.qf['expr'], keymap=km),
        ])
        self.data_updated()

    def add_buttons(self):
        super().add_buttons(apply=(self.mode == 'edit'))

    def name_valid(self):
        name = self.field_list.fields['name'].get_value()
        return bool(name.strip() and name not in self.other_names)

    def data_updated(self):
        super().data_updated()
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(self.name_valid())

    def apply_field_update(self, field, value):
        self.qf[field.key] = value


class FilterGrid(QWidget):
    def __init__(self, dialog, filters):
        super().__init__()
        self.dialog = dialog
        self.app = dialog.app
        self.filters = filters
        self.do_layout()

    def do_layout(self):
        QWidget().setLayout(self.layout()) # clears any existing layout
        grid = QGridLayout()
        self.setLayout(grid)
        for i, name in enumerate(sorted(self.filters)):
            qf = self.filters[name]
            grid.addWidget(QLabel(name), i, 0)
            for j, action in enumerate(['edit', 'delete']):
                button = QPushButton(action.title())
                button.setFocusPolicy(Qt.NoFocus)
                button.clicked.connect(functools.partial(self.button_cb, action=action, name=name))
                grid.addWidget(button, i, j + 1)

        new = QPushButton("Add new filter")
        new.setFocusPolicy(Qt.NoFocus)
        new.clicked.connect(functools.partial(self.button_cb, action='new'))
        i = len(self.filters)
        grid.addWidget(new, i, 0, 1, 3)
        self.layout().setRowStretch(i + 1, 1)

    def button_cb(self, action, name=None):
        if action == 'edit':
            FilterEditor(self.app, self.filters, self.filters[name], mode='edit').exec()
        elif action == 'delete':
            del self.filters[name]
        elif action == 'new':
            qf = {'name': '', 'group': [], 'order': [], 'expr': '', }
            if FilterEditor(self.app, self.filters, qf, mode='new').exec():
                self.filters[qf['name']] = qf
        else:
            assert 0, action
        self.dialog.data_updated()
        self.do_layout()


class QuickFilterDialog(DataDialog):
    title = 'Quick Filters'

    def __init__(self, app):
        super().__init__(app)
        self.keybinds = self.app.keybinds
        self.library = self.app.library
        self.filters = copy.deepcopy(self.library.quick_filters)
        self.grid = FilterGrid(self, self.filters)
        self.layout().addWidget(self.grid)
        self.add_buttons()

    def dirty(self):
        return self.filters != self.library.quick_filters

    def commit(self):
        for qf in self.library.quick_filters:
            self.keybinds.delete_action('quick_filter_' + qf)
        self.library.quick_filters = self.filters
        for qf in self.library.quick_filters:
            self.keybinds.add_action('quick_filter_' + qf)
