from PySide6.QtCore import Qt

from fields import FieldDialog, SetField, TextField
import expr


def construct_filter(config):
    clauses = []
    if config['custom_expr']:
        clauses.append(config['custom_expr'])
    if config['include_tags']:
        clauses.append('|'.join(config['include_tags']))
    if config['exclude_tags']:
        clauses.append('!(%s)' % ('|'.join(config['exclude_tags'])))
    filter_expr = '&'.join('(%s)' % clause for clause in clauses)
    return expr.parse_expr(filter_expr) if filter_expr else None


def validate_expr(text):
    try:
        expr.parse_expr(text)
    except expr.BadExpr:
        return False
    return True


def normalize_expr(text):
    return str(expr.parse_expr(text)) if text else text


def default_config(library):
    return {
        'group_by': library.default_group_by,
        'order_by': [],
        'include_tags': [],
        'exclude_tags': [],
        'custom_expr': '',
        '_filter': None,
    }


class ConfigDialog(FieldDialog):
    title = "Config"

    def __init__(self, main_window, library, config):
        super().__init__(main_window)
        self.library = library
        self.config = config
        self.need_reload = False
        self.init_fields(self.choose_fields())

    def choose_fields(self):
        all_tags = set()
        for _set in self.library.sets.values():
            all_tags |= _set
        sort_types = list(self.library.sort_types.keys())
        return [
            SetField("group_by", self.config['group_by'].copy(), self.library.keys, keybind='G'),
            SetField("order_by", self.config['order_by'].copy(), sort_types, keybind='O'),
            SetField('include_tags', self.config['include_tags'].copy(), all_tags, keybind='I'),
            SetField('exclude_tags', self.config['exclude_tags'].copy(), all_tags, keybind='X'),
            TextField('custom_expr', self.config['custom_expr'], keybind='U',
                      validator=validate_expr, normalizer=normalize_expr)
        ]

    def accept(self):
        if self.need_reload:
            self.main_window.reload_tree()
        super().accept()

    def field_committed(self, key, value):
        self.need_reload = True
        assert key in self.config, (key, value)
        self.config[key] = value
        self.config['_filter'] = construct_filter(self.config)
        super().field_committed(key, value)
