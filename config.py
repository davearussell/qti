import copy
from PySide6.QtCore import Qt

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


class Config:
    defaults = {
        'group_by': [],
        'order_by': [],
        'include_tags': [],
        'exclude_tags': [],
        'custom_expr': '',
    }

    def __init__(self, **kwargs):
        for k, v in self.defaults.items():
            setattr(self, k, kwargs.pop(k, copy.deepcopy(v)))
        if kwargs:
            raise AttributeError("%s does not take attribute(s) %r" % (
                type(self).__name__, ', '.join(kwargs.keys())))

    def copy(self):
        kwargs = {k: getattr(self, k) for k in self.defaults}
        return type(self)(**copy.deepcopy(kwargs))

    def clear_filters(self):
        for k in ['include_tags', 'exclude_tags', 'custom_expr']:
            setattr(self, k, self.defaults[k])

    @property
    def filter(self):
        clauses = []
        if self.custom_expr:
            clauses.append(self.custom_expr)
        if self.include_tags:
            clauses.append('|'.join(self.include_tags))
        if self.exclude_tags:
            clauses.append('!(%s)' % ('|'.join(self.exclude_tags)))
        filter_expr = '&'.join('(%s)' % clause for clause in clauses)
        return expr.parse_expr(filter_expr) if filter_expr else None


def default_config(library):
    return Config(group_by=library.default_group_by)


class ConfigDialog(FieldDialog):
    title = "Config"

    def __init__(self, main_window, library, config):
        super().__init__(main_window)
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
            SetField("group_by", config.group_by, self.library.keys, keybind='G'),
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
