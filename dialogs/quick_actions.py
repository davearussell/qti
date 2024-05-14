from .list_manager import ListManagerDialog
from .fields import TextField, EnumField
from expr import parse_expr
from tree import SORT_TYPES


class QuickActionDialog(ListManagerDialog):
    title = 'Quick Actions'
    ops = ['add', 'remove']

    def __init__(self, app):
        super().__init__(app, app.library.quick_actions)

    def item_defaults(self):
        return {'key': '', 'operation': self.ops[0], 'value': ''}

    def field_types(self):
        return [
            ('key'  ,     TextField, {'completions': self.app.library.metadata.editable_keys()}),
            ('operation', EnumField, {'values': self.ops}),
            ('value',     TextField, {})
        ]

    def commit(self):
        for qa in self.app.library.quick_actions:
            self.app.keybinds.delete_action('quick_action_' + qa)
        self.app.library.quick_actions = self.items
        for qa in self.app.library.quick_actions:
            self.app.keybinds.add_action('quick_action_' + qa)

