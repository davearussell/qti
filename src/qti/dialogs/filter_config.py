from .. import expr
from .common import FieldDialog
from .fields import SetField, TypedField
from ..tree import SORT_TYPES


class FilterConfigDialog(FieldDialog):
    title = "Filtering and grouping"

    def __init__(self, app):
        self.app = app
        self.library = app.library
        self.config = app.filter_config
        super().__init__(app.window, self.choose_fields())

    def choose_fields(self):
        can_group_by = self.library.metadata.groupable_keys()
        values_by_key = self.library.values_by_key()
        all_tags = set()
        for key in self.library.metadata.keys:
            if not (key.in_hierarchy or key.builtin):
                all_tags |= values_by_key[key.name]
        config = self.config.copy()
        return [
            SetField("group_by", config.group_by, can_group_by, keybind='g'),
            SetField("order_by", config.order_by, SORT_TYPES.keys(), keybind='o'),
            SetField('include_tags', config.include_tags, all_tags, keybind='i'),
            SetField('exclude_tags', config.exclude_tags, all_tags, keybind='x'),
            TypedField('custom_expr', config.custom_expr, expr.parse_expr, keybind='u'),
        ]

    def commit(self):
        super().commit()
        self.app.reload_tree()

    def apply_field_update(self, field, value):
        setattr(self.config, field.key, value)
