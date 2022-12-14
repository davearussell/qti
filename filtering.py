import copy

from dialog import FieldDialog
from line_edit import LineEdit
from fields import SetField, TextField
import expr
import keys


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


def default_filter_config(library):
    c = FilterConfig(group_by=list(library.hierarchy))
    c.defaults = copy.deepcopy(c.defaults)
    c.defaults['group_by'] = copy.deepcopy(library.hierarchy)
    return c


class ExprEdit(LineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textChanged.connect(self.check_valid)

    def is_valid(self, value):
        try:
            expr.parse_expr(value)
            return True
        except expr.BadExpr:
            return False

    def normalise(self, value):
        try:
            return str(expr.parse_expr(value))
        except expr.BadExpr:
            return ''

    def check_valid(self, value):
        self.setProperty("valid", self.is_valid(value))
        self.setStyleSheet("/* /") # force stylesheet recalc

    def keyPressEvent(self, event):
        if keys.get_action(event) == 'select':
            self.setText(self.normalise(self.text()))
        super().keyPressEvent(event)


class ExprField(TextField):
    edit_cls = ExprEdit


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

    def field_committed(self, field, value):
        self.need_reload = True
        assert field.key in self.config.defaults, (field.key, value)
        setattr(self.config, field.key, value)
        super().field_committed(field, value)
