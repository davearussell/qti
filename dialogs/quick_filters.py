from .list_manager import ListManagerDialog
from .fields import SetField, TypedField
from expr import parse_expr
from tree import SORT_TYPES


class QuickFilterDialog(ListManagerDialog):
    title = 'Quick Filters'

    def __init__(self, app):
        super().__init__(app, app.library.quick_filters)

    def item_defaults(self):
        return {'group': [], 'order': [], 'expr': ''}

    def field_types(self):
        return [
            ('group', SetField,   {'completions': self.app.library.metadata.groupable_keys()}),
            ('order', SetField,   {'completions': SORT_TYPES}),
            ('expr',  TypedField, {'parser': parse_expr}),
        ]

    def commit(self):
        for item in self.items.values():
            item['expr'] = str(item['expr']) # TODO: remove this special-case
        for qf in self.app.library.quick_filters:
            self.app.keybinds.delete_action('quick_filter_' + qf)
        self.app.library.quick_filters = self.items
        for qf in self.app.library.quick_filters:
            self.app.keybinds.add_action('quick_filter_' + qf)

