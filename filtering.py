import copy

from dialog import FieldDialog
from line_edit import ValidatedLineEdit
from fields import SetField, ValidatedTextField
import expr


class FilterConfig:
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

    def is_default(self):
        return all(getattr(self, k) == v for (k, v) in self.defaults.items())

    def copy(self):
        kwargs = {k: getattr(self, k) for k in self.defaults}
        return type(self)(**copy.deepcopy(kwargs))

    def clear_filters(self):
        for k in ['include_tags', 'exclude_tags', 'custom_expr',
                  'group_by', 'order_by']:
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


def default_filter_config(library):
    c = FilterConfig(group_by=list(library.hierarchy))
    c.defaults = copy.deepcopy(c.defaults)
    c.defaults['group_by'] = copy.deepcopy(library.hierarchy)
    return c


class ExprField(ValidatedTextField):
    class edit_cls(ValidatedLineEdit):
        def normalise(self, value):
            return str(expr.parse_expr(value))


class FilterConfigDialog(FieldDialog):
    title = "Filtering and grouping"

    def __init__(self, app, library, filter_config):
        super().__init__(app)
        self.library = library
        self.config = filter_config
        self.init_fields(self.choose_fields())

    def choose_fields(self):
        all_tags = set()
        for _set in self.library.sets.values():
            all_tags |= _set
        sort_types = self.library.sort_types()
        config = self.config.copy()
        return [
            SetField("group_by", config.group_by, self.library.groupable_keys(), keybind='G'),
            SetField("order_by", config.order_by, sort_types, keybind='O'),
            SetField('include_tags', config.include_tags, all_tags, keybind='I'),
            SetField('exclude_tags', config.exclude_tags, all_tags, keybind='X'),
            ExprField('custom_expr', config.custom_expr, keybind='U'),
        ]

    def commit(self):
        super().commit()
        self.app.reload_tree()

    def apply_field_update(self, field, value):
        setattr(self.config, field.key, value)
