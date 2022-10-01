from fields import FieldDialog, SetField, TextField
import expr


def validate_expr(text):
    try:
        expr.parse_expr(text)
    except expr.BadExpr:
        return False
    return True


def normalize_expr(text):
    return str(expr.parse_expr(text)) if text else text


class ViewConfigDialog(FieldDialog):
    title = "Config"

    def __init__(self, app, library, config):
        super().__init__(app)
        self.library = library
        self.config = config
        self.init_fields(self.choose_fields())

    def choose_fields(self):
        all_tags = set()
        for _set in self.library.sets.values():
            all_tags |= _set
        sort_types = list(self.library.sort_types.keys())
        config = self.config.copy()
        return [
            SetField("group_by", config.group_by, self.library.custom_keys, keybind='G'),
            SetField("order_by", config.order_by, sort_types, keybind='O'),
            SetField('include_tags', config.include_tags, all_tags, keybind='I'),
            SetField('exclude_tags', config.exclude_tags, all_tags, keybind='X'),
            TextField('custom_expr', config.custom_expr, keybind='U',
                      validator=validate_expr, normalizer=normalize_expr)
        ]

    def field_committed(self, field, value):
        self.need_reload = True
        assert field.key in self.config.defaults, (field.key, value)
        setattr(self.config, field.key, value)
        super().field_committed(field, value)
