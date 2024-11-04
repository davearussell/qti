import copy

from .. import template
from ..import ui
from .common import DataDialog


class BulkEditDialog(DataDialog):
    ui_cls = ui.cls('bulk_edit_dialog')

    def __init__(self, app, node):
        self.app = app
        self.node = node
        self.library = self.app.library
        self.edit_type = self.node.children[0].type
        self.title = "Bulk %s edit" % (self.edit_type,)
        self.keys = self.choose_keys()
        self.table = self.make_table(self.keys)
        self.orig_table = copy.deepcopy(self.table)
        super().__init__(app.window)

    @property
    def ui_args(self):
        return {
            'keys': self.keys,
            'table': self.table,
            'update_cb': self.update_key,
        }

    def make_table(self, keys):
        return [{key: child.get_key(key) for key in keys} for child in self.node.children]

    def choose_keys(self):
        hierarchy = self.library.metadata.hierarchy()
        if self.edit_type == 'image':
            parents = hierarchy
        elif self.edit_type in hierarchy:
            i = hierarchy.index(self.edit_type)
            parents = hierarchy[:i]
        else:
            parents = []
        keys = ['name']
        for key in self.library.metadata.keys:
            if key.builtin or key.multi:
                continue
            if key.in_hierarchy and key.name not in parents:
                continue
            keys.append(key.name)
        return keys

    def template_spec(self, node):
        spec = {
            'i': node.index,
            'name': node.name,
        }
        if node.type == 'image':
            spec['dir'] = os.path.basename(os.path.dirname(node.abspath))
            spec['file'] = os.path.splitext(os.path.basename(node.abspath))[0]
        for key in self.library.metadata.keys:
            spec[key.name] = node.get_key(key.name)
        return spec

    def update_key(self, key, value):
        for i, node in enumerate(self.node.children):
            self.table[i][key] = template.apply(self.template_spec(node), value)
        self.ui.refresh()
        self.data_updated()

    def dirty(self):
        return self.table != self.orig_table

    def commit(self):
        for node, row in zip(self.node.children, self.table):
            for key in self.keys:
                node.update(key, row[key])
        self.app.reload_tree()
