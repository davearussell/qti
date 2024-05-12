import copy

from .common import DataDialog, FieldDialog
from .fields import ValidatedTextField, SetField, TypedField
from qt.dialogs.quick_filters import QuickFilterDialogWidget
from expr import parse_expr
from tree import SORT_TYPES


class QFEditDialog(FieldDialog):
    def __init__(self, parent, qf):
        self.qf = qf
        banned_names = {name for name in parent.filters if name != qf['name']}
        group_keys = parent.app.library.metadata.groupable_keys()
        super().__init__(parent.ui, [
            ValidatedTextField('name', qf['name'], lambda n : n not in banned_names),
            SetField('group', qf['group'], group_keys),
            SetField('order', qf['order'], SORT_TYPES),
            TypedField('expr', qf['expr'], parse_expr),
        ])

    def apply_field_update(self, field, value):
        if field.key == 'expr': # TODO: avoid this special-case
            value = str(value)
        self.qf[field.key] = value


class QFAddDialog(QFEditDialog):
    actions = {'accept': True, 'cancel': True}


class QuickFilterDialog(DataDialog):
    title = 'Quick Filters'
    ui_cls = QuickFilterDialogWidget

    def __init__(self, app):
        self.app = app
        self.metadata = app.library.metadata
        self.filters = copy.deepcopy(app.library.quick_filters)
        super().__init__(app.window)

    @property
    def ui_args(self):
        return {
            'filter_names': self.filters.keys(),
            'new_cb': self.new_filter,
            'edit_cb': self.edit_filter,
            'delete_cb': self.delete_filter,
        }

    def refresh(self):
        self.data_updated()
        self.ui.load_filters()

    def new_filter(self):
        qf = {'name': '', 'group': [], 'order': [], 'expr': ''}
        if QFAddDialog(self, qf).run():
            self.filters[qf['name']] = qf
            self.refresh()

    def edit_filter(self, filter_name):
        if QFEditDialog(self, self.filters[filter_name]).run():
            qf = self.filters.pop(filter_name)
            self.filters[qf['name']] = qf
            self.refresh()

    def delete_filter(self, filter_name):
        del self.filters[filter_name]
        self.refresh()

    def dirty(self):
        return self.filters != self.app.library.quick_filters

    def commit(self):
        for qf in self.app.library.quick_filters:
            self.app.keybinds.delete_action('quick_filter_' + qf)
        self.app.library.quick_filters = self.filters
        for qf in self.app.library.quick_filters:
            self.app.keybinds.add_action('quick_filter_' + qf)
