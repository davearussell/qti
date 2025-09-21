from .. import expr
from xui.widgets import FieldDialog, TypedField, SetField
from ..tree import SORT_TYPES


class FilterConfigDialog(FieldDialog):
    title = "Filtering and grouping"

    def __init__(self):
        super().__init__()
        self.init_fields(self.choose_fields())

    def choose_fields(self):
        can_group_by = self.app.library.metadata.groupable_keys()
        values_by_key = self.app.library.values_by_key()
        all_tags = set()
        for key in self.app.library.metadata.keys:
            if not (key.in_hierarchy or key.builtin):
                all_tags |= values_by_key[key.name]
        config = self.app.filter_config.copy()
        return [
            SetField("group_by", config.group_by, completions=can_group_by, keybind='g'),
            SetField("order_by", config.order_by, completions=SORT_TYPES.keys(), keybind='o'),
            SetField('include_tags', config.include_tags, completions=all_tags, keybind='i'),
            SetField('exclude_tags', config.exclude_tags, completions=all_tags, keybind='x'),
            TypedField('custom_expr', config.custom_expr, expr.parse_expr, keybind='u'),
        ]

    def commit(self):
        super().commit()
        self.app.reload_tree()

    def apply_field_update(self, field, value):
        setattr(self.app.filter_config, field.key, value)
