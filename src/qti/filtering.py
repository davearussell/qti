import copy
from . import expr


class FilterConfig:
    defaults = {
        'group_by': [],
        'order_by': [],
        'include_tags': [],
        'exclude_tags': [],
        'custom_expr': expr.Empty(),
    }

    def __init__(self, **kwargs):
        for k, v in self.defaults.items():
            setattr(self, k, kwargs.pop(k, copy.deepcopy(v)))
        if kwargs:
            raise AttributeError("%s does not take attribute(s) %r" % (
                type(self).__name__, ', '.join(kwargs.keys())))

    def rename_key(self, old_name, new_name):
        try:
            self.group_by[self.group_by.index(old_name)] = new_name
        except ValueError:
            pass

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
    hierarchy = library.metadata.hierarchy()
    c = FilterConfig(group_by=hierarchy)
    c.defaults = copy.deepcopy(c.defaults)
    c.defaults['group_by'] = hierarchy.copy()
    return c
